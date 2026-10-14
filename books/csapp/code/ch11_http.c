#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
/* C11 + POSIX. A bounded HTTP/1.x teaching core, not a general HTTP server.
 * Static assets: one plain filename beneath root, no symlinks, <=64 KiB.
 * build_response computes the adder in process. --serve-cgi actually forks and
 * execs this binary (or an operator-selected CGI), reaping via SIGCHLD.
 * build_response owns no socket; caller frees *response. handle owns no fd.
 */
#include <arpa/inet.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define CH11_REQUEST_LIMIT 12288
#define CH11_HEADER_LIMIT 8192
#define CH11_BODY_LIMIT 4096
#define CH11_FILE_LIMIT 65536

static long long now_ms(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) return -1;
    return (long long)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}
static int io_ready(int fd, short events, long long end) {
    for (;;) {
        long long left = end - now_ms();
        if (left <= 0) return 0;
        struct pollfd p = {fd, events, 0};
        int rc = poll(&p, 1, (int)left);
        if (rc < 0 && errno == EINTR) continue;
        return rc > 0;
    }
}
static int write_all(int fd, const void *data, size_t n) {
    const unsigned char *p = data;
    int flags = fcntl(fd, F_GETFL), rc = -1;
    if (flags < 0 || fcntl(fd, F_SETFL, flags | O_NONBLOCK)) return -1;
    long long end = now_ms() + 2000;
    while (n) {
        if (!io_ready(fd, POLLOUT, end)) { errno = ETIMEDOUT; goto done; }
        ssize_t k = write(fd, p, n > 4096 ? 4096 : n);
        if (k < 0 && (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)) continue;
        if (k <= 0) goto done;
        p += (size_t)k; n -= (size_t)k;
    }
    rc = 0;
done: {
        int saved = errno;
        if (fcntl(fd, F_SETFL, flags)) return -1;
        errno = saved; return rc;
    }
}
/* Returns 0 for an incomplete request, 1 for a complete request, -1 if invalid.
 * Input need not be NUL terminated. This conservative framing rejects TE and
 * repeated Content-Length rather than attempting ambiguous interpretations. */
static int request_size(const char *data, size_t n, size_t *expected) {
    if (n > CH11_REQUEST_LIMIT || memchr(data, 0, n)) return -1;
    char text[CH11_REQUEST_LIMIT + 1]; memcpy(text, data, n); text[n] = 0;
    char *end = strstr(text, "\r\n\r\n");
    if (!end) return n >= CH11_HEADER_LIMIT ? -1 : 0;
    size_t head = (size_t)(end - text) + 4, body = 0;
    if (head > CH11_HEADER_LIMIT) return -1;
    char *line = strstr(text, "\r\n");
    if (!line) return -1;
    line += 2; bool seen = false;
    while (line < end) {
        char *next = strstr(line, "\r\n");
        if (!next) return -1;
        *next = 0;
        char *colon = strchr(line, ':');
        if (!colon || colon == line || line[0] == ' ' || line[0] == '\t') return -1;
        *colon = 0; char *value = colon + 1;
        while (*value == ' ' || *value == '\t') ++value;
        char *tail = next;
        while (tail > value && (tail[-1] == ' ' || tail[-1] == '\t')) --tail;
        *tail = 0;
        for (const unsigned char *q = (const unsigned char *)value; *q; ++q)
            if ((*q < 32 && *q != '\t') || *q == 127) return -1;
        for (const char *q = line; *q; ++q)
            if (!isalnum((unsigned char)*q) && *q != '-') return -1;
        if (!strcasecmp(line, "Transfer-Encoding")) return -1;
        if (!strcasecmp(line, "Content-Length")) {
            if (seen || !*value) return -1;
            seen = true;
            for (const char *q = value; *q; ++q) {
                if (*q < '0' || *q > '9') return -1;
                body = body * 10 + (size_t)(*q - '0');
                if (body > CH11_BODY_LIMIT) return -1;
            }
        }
        line = next + 2;
    }
    *expected = head + body;
    return n >= *expected;
}
static int integer(const char *s, long *result) {
    if (!*s || strlen(s) > 8) return 0;
    const char *p = s;
    if (*p == '+' || *p == '-') ++p;
    if (!*p) return 0;
    for (; *p; ++p) if (*p < '0' || *p > '9') return 0;
    char *end; errno = 0; long v = strtol(s, &end, 10);
    if (errno || *end || v < -1000000 || v > 1000000) return 0;
    *result = v; return 1;
}
static int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
static int unescape(char *s) {
    char *w = s;
    while (*s) {
        if (*s == '%') {
            if (!s[1] || !s[2]) return 0;
            int a = hex_digit(s[1]), b = hex_digit(s[2]);
            if (a < 0 || b < 0 || a * 16 + b == 0) return 0;
            *w++ = (char)(a * 16 + b); s += 3;
        } else { *w++ = *s == '+' ? ' ' : *s; ++s; }
    }
    *w = 0; return 1;
}
static int sum_arguments(char *args, long *a, long *b) {
    char *amp = strchr(args, '&');
    if (!amp || strchr(amp + 1, '&')) return 0;
    *amp++ = 0;
    if (!strncmp(args, "a=", 2) && !strncmp(amp, "b=", 2)) {
        args += 2; amp += 2;
        if (!unescape(args) || !unescape(amp)) return 0;
    }
    return integer(args, a) && integer(amp, b);
}
static const char *mime(const char *name) {
    const char *ext = strrchr(name, '.');
    if (!ext) return "application/octet-stream";
    if (!strcmp(ext, ".html")) return "text/html; charset=utf-8";
    if (!strcmp(ext, ".txt")) return "text/plain; charset=utf-8";
    if (!strcmp(ext, ".png")) return "image/png";
    if (!strcmp(ext, ".gif")) return "image/gif";
    if (!strcmp(ext, ".jpg")) return "image/jpeg";
    if (!strcmp(ext, ".mpg") || !strcmp(ext, ".mpeg")) return "video/mpeg";
    return "application/octet-stream";
}
static int read_asset(const char *root, const char *name, char **body, size_t *n) {
    if (!*name || strstr(name, "..")) return 403;
    for (const char *p = name; *p; ++p)
        if (!isalnum((unsigned char)*p) && *p != '_' && *p != '-' && *p != '.') return 403;
    int dir = open(root, O_RDONLY | O_DIRECTORY);
    if (dir < 0) return 500;
    int fd = openat(dir, name, O_RDONLY | O_NOFOLLOW | O_NONBLOCK); close(dir);
    if (fd < 0) return errno == ENOENT ? 404 : 403;
    struct stat st;
    if (fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_size < 0 || st.st_size > CH11_FILE_LIMIT) {
        close(fd); return 403;
    }
    *n = (size_t)st.st_size; *body = malloc(*n ? *n : 1);
    if (!*body) { close(fd); return 500; }
    size_t done = 0;
    while (done < *n) {
        ssize_t k = read(fd, *body + done, *n - done);
        if (k < 0 && errno == EINTR) continue;
        if (k <= 0) { free(*body); *body = NULL; close(fd); return 500; }
        done += (size_t)k;
    }
    close(fd); return 200;
}
static int header_value(const char *request, const char *name, char *value, size_t cap) {
    const char *p = strstr(request, "\r\n"); int found = 0;
    if (!p) return 0;
    p += 2;
    while (*p && strncmp(p, "\r\n", 2)) {
        const char *end = strstr(p, "\r\n"), *colon = strchr(p, ':');
        if (!end || !colon || colon > end) return -1;
        if ((size_t)(colon - p) == strlen(name) && !strncasecmp(p, name, strlen(name))) {
            if (found++) return -1;
            const char *v = colon + 1;
            while (v < end && (*v == ' ' || *v == '\t')) ++v;
            const char *tail = end;
            while (tail > v && (tail[-1] == ' ' || tail[-1] == '\t')) --tail;
            size_t n = (size_t)(tail - v);
            if (n >= cap) return -1;
            memcpy(value, v, n); value[n] = 0;
        }
        p = end + 2;
    }
    return found;
}
/* Ready to generate a final response, not necessarily a complete message.
 * A validated header with unsupported Expect must be rejected before waiting
 * for its body: the client may be waiting for our decision before sending it.
 * request_size retains its framing contract for callers such as the proxy. */
static int request_ready(const char *request, size_t n) {
    size_t expected = 0;
    if (request_size(request, n, &expected) != 0) return 1;
    if (!expected) return 0; /* The complete header has not been validated yet. */
    char text[CH11_REQUEST_LIMIT + 1], value[100];
    memcpy(text, request, n); text[n] = 0;
    return header_value(text, "Expect", value, sizeof(value)) != 0;
}
static int build_response(const char *request, size_t request_len, const char *root,
                          char **response, size_t *response_len) {
    char text[CH11_REQUEST_LIMIT + 1], method[16] = "", target[2048], version[16], extra, header_scratch[100];
    char original[CH11_REQUEST_LIMIT + 1];
    int status = 400; size_t expected = 0, n = 0; char *body = NULL;
    const char *type = "text/plain; charset=utf-8";
    *response = NULL; *response_len = 0;
    if (request_len >= 5 && !memcmp(request, "HEAD ", 5)) strcpy(method, "HEAD");
    if (request_len <= CH11_REQUEST_LIMIT) {
        memcpy(text, request, request_len); text[request_len] = 0;
        memcpy(original, text, request_len + 1);
        char *end = strstr(text, "\r\n"), *headers_end = strstr(text, "\r\n\r\n");
        if (end && headers_end) {
            *end = 0;
            int fields = sscanf(text, "%15s %2047s %15s %c", method, target, version, &extra);
            int framing = request_size(request, request_len, &expected);
            int expect = header_value(original, "Expect", header_scratch, sizeof(header_scratch)) != 0;
            /* Valid Expect headers are actionable before the declared body.
             * Invalid framing and extra bytes still reject as a bad request. */
            if (fields == 3 && framing >= 0 && expected && request_len <= expected &&
                (request_len == expected || expect)) {
                if (strcmp(version, "HTTP/1.0") && strcmp(version, "HTTP/1.1")) status = 505;
                else if (strcmp(method, "GET") && strcmp(method, "HEAD") && strcmp(method, "POST")) status = 501;
                else if (target[0] != '/') status = 400;
                else if (!strcmp(version, "HTTP/1.1") &&
                         (header_value(original, "Host", header_scratch, sizeof(header_scratch)) != 1 || !header_scratch[0])) status = 400;
                else if (expect) status = 417;
                else if (!strcmp(method, "POST") && header_value(original, "Content-Length", header_scratch, sizeof(header_scratch)) != 1) status = 411;
                else if (!strcmp(method, "POST") &&
                         (header_value(original, "Content-Type", header_scratch, sizeof(header_scratch)) != 1 ||
                          strcmp(header_scratch, "application/x-www-form-urlencoded"))) status = 415;
                else {
                    char *query = strchr(target, '?');
                    if (query) *query++ = 0;
                    if (!strcmp(target, "/cgi-bin/adder")) {
                        char args[CH11_BODY_LIMIT + 1];
                        const char *source = !strcmp(method, "POST") ? headers_end + 4 : query;
                        if (!source) source = "";
                        size_t len = strlen(source);
                        if (len <= CH11_BODY_LIMIT) {
                            memcpy(args, source, len + 1); long a, b;
                            if (sum_arguments(args, &a, &b)) {
                                char result[128]; int k = snprintf(result, sizeof(result), "<p>%ld + %ld = %ld</p>\n", a, b, a + b);
                                n = (size_t)k; body = malloc(n ? n : 1);
                                if (!body) status = 500;
                                else { memcpy(body, result, n); status = 200; type = "text/html; charset=utf-8"; }
                            }
                        }
                    } else if (!strcmp(method, "POST")) status = 405;
                    else {
                        const char *name = !strcmp(target, "/") ? "home.html" : target + 1;
                        status = read_asset(root, name, &body, &n); type = mime(name);
                    }
                }
            }
        }
    }
    const char *reason = status == 200 ? "OK" : status == 403 ? "Forbidden" :
        status == 404 ? "Not Found" : status == 405 ? "Method Not Allowed" :
        status == 411 ? "Length Required" : status == 415 ? "Unsupported Media Type" :
        status == 417 ? "Expectation Failed" :
        status == 500 ? "Internal Server Error" : status == 501 ? "Not Implemented" :
        status == 505 ? "HTTP Version Not Supported" : "Bad Request";
    if (status != 200) {
        free(body); n = strlen(reason); body = malloc(n);
        if (!body) return -1;
        memcpy(body, reason, n); type = "text/plain; charset=utf-8";
    }
    char header[512]; int h = snprintf(header, sizeof(header),
        "HTTP/1.0 %d %s\r\nContent-Type: %s\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n",
        status, reason, type, n);
    if (h < 0 || (size_t)h >= sizeof(header)) { free(body); return -1; }
    size_t payload = !strcmp(method, "HEAD") ? 0 : n;
    *response_len = (size_t)h + payload; *response = malloc(*response_len);
    if (!*response) { free(body); return -1; }
    memcpy(*response, header, (size_t)h); memcpy(*response + h, body, payload);
    free(body); return 0;
}
static int handle(int fd, const char *root) {
    char request[CH11_REQUEST_LIMIT]; size_t n = 0;
    int flags = fcntl(fd, F_GETFL), rc = -1;
    if (flags < 0 || fcntl(fd, F_SETFL, flags | O_NONBLOCK)) return -1;
    long long end = now_ms() + 2000;
    while (n < sizeof(request)) {
        if (!io_ready(fd, POLLIN, end)) { errno = ETIMEDOUT; goto done; }
        ssize_t k = read(fd, request + n, sizeof(request) - n);
        if (k < 0 && (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)) continue;
        if (k <= 0) break;
        n += (size_t)k;
        if (request_ready(request, n)) break;
    }
    char *response; size_t len;
    if (build_response(request, n, root, &response, &len)) goto done;
    rc = write_all(fd, response, len); free(response);
done: {
        int saved = errno;
        if (fcntl(fd, F_SETFL, flags)) return -1;
        errno = saved; return rc;
    }
}
static volatile sig_atomic_t reaped, reap_max_batch;
static void child_handler(int sig) {
    (void)sig; int saved = errno; pid_t p; sig_atomic_t batch = 0;
    do { p = waitpid(-1, NULL, WNOHANG); if (p > 0) { ++reaped; ++batch; } }
    while (p > 0 || (p < 0 && errno == EINTR));
    if (batch > reap_max_batch) reap_max_batch = batch;
    errno = saved;
}
static int reaper_test(void) {
    sigset_t block, old, suspend_mask; sigemptyset(&block); sigaddset(&block, SIGCHLD);
    struct sigaction action = {0}; action.sa_handler = child_handler;
    sigemptyset(&action.sa_mask); action.sa_flags = SA_RESTART;
    if (sigaction(SIGCHLD, &action, NULL) || sigprocmask(SIG_BLOCK, &block, &old)) return 1;
    reaped = 0; pid_t child = fork();
    if (child == 0) _exit(0);
    if (child < 0) { sigprocmask(SIG_SETMASK, &old, NULL); return 1; }
    suspend_mask = old; sigdelset(&suspend_mask, SIGCHLD);
    if (sigprocmask(SIG_SETMASK, &suspend_mask, NULL)) return 1;
    long long deadline = now_ms() + 2000;
    while (!reaped && now_ms() < deadline) {
        struct timespec pause = {0, 10000000}; nanosleep(&pause, NULL);
    }
    int failed = !reaped;
    if (failed) { kill(child, SIGKILL); while (waitpid(child, NULL, 0) < 0 && errno == EINTR) {} }
    return sigprocmask(SIG_SETMASK, &old, NULL) != 0 || failed;
}
/* An actual CGI program: exec resets caught handlers and reads standard CGI
 * variables. The trusted executable is selected by the server operator only.
 * The alarm inherited across exec bounds its lifetime even if a client stalls. */
static int cgi_main(void) {
    const char *method = getenv("REQUEST_METHOD"), *query = getenv("QUERY_STRING");
    char args[CH11_BODY_LIMIT + 1]; size_t n = 0;
    if (!method) return 1;
    if (!strcmp(method, "POST")) {
        const char *length = getenv("CONTENT_LENGTH");
        if (!length || !*length) return 1;
        char *end; errno = 0; unsigned long amount = strtoul(length, &end, 10);
        if (errno || *end || amount > CH11_BODY_LIMIT) return 1;
        while (n < amount) {
            ssize_t got = read(STDIN_FILENO, args + n, amount - n);
            if (got < 0 && errno == EINTR) continue;
            if (got <= 0) return 1;
            n += (size_t)got;
        }
    } else {
        n = query ? strlen(query) : 0;
        if (n > CH11_BODY_LIMIT) return 1;
        if (n) memcpy(args, query, n);
    }
    args[n] = 0; long a, b;
    if (!sum_arguments(args, &a, &b)) return 1;
    char body[128], header[512];
    int size = snprintf(body, sizeof(body), "<p>%ld + %ld = %ld</p>\n", a, b, a + b);
    int h = snprintf(header, sizeof(header),
        "HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
        "Content-Length: %d\r\nConnection: close\r\n\r\n", size);
    if (size < 0 || h < 0 || (size_t)h >= sizeof(header) ||
        write_all(STDOUT_FILENO, header, (size_t)h)) return 1;
    return strcmp(method, "HEAD") && write_all(STDOUT_FILENO, body, (size_t)size);
}
/* Returns 1 when this connection was transferred to a CGI child, 0 when the
 * parent served it, and -1 on an I/O/setup failure. Caller always closes fd.
 * Single-threaded, with exclusive ownership of every child in this server. */
static int dispatch_cgi(int fd, int listener, const char *root, const char *program) {
    char request[CH11_REQUEST_LIMIT + 1]; size_t n = 0;
    long long end = now_ms() + 2000;
    while (n < CH11_REQUEST_LIMIT) {
        if (!io_ready(fd, POLLIN, end)) return -1;
        ssize_t got = read(fd, request + n, CH11_REQUEST_LIMIT - n);
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0) break;
        n += (size_t)got;
        if (request_ready(request, n)) break;
    }
    request[n] = 0;
    char *response = NULL; size_t length = 0;
    if (build_response(request, n, root, &response, &length)) return -1;
    char method[16] = "", target[2048] = "";
    (void)sscanf(request, "%15s %2047s", method, target);
    char *query = strchr(target, '?');
    if (query) *query++ = 0;
    if (length < 15 || memcmp(response, "HTTP/1.0 200 OK\r", 15) || strcmp(target, "/cgi-bin/adder")) {
        int rc = write_all(fd, response, length); free(response); return rc ? -1 : 0;
    }
    free(response);
    char *body = strstr(request, "\r\n\r\n") + 4;
    /* GET/HEAD use QUERY_STRING; their already-consumed HTTP bodies do not
     * become CGI stdin. Only POST transfers its declared body through pipe. */
    size_t body_size = !strcmp(method, "POST") ? n - (size_t)(body - request) : 0;
    int input[2];
    if (pipe(input)) return -1;
    pid_t child = fork();
    if (child < 0) { close(input[0]); close(input[1]); return -1; }
    if (child == 0) {
        close(listener); close(input[1]);
        if (dup2(input[0], STDIN_FILENO) < 0 || dup2(fd, STDOUT_FILENO) < 0) _exit(126);
        if (input[0] != STDIN_FILENO) close(input[0]);
        if (fd != STDOUT_FILENO) close(fd);
        char count[32]; (void)snprintf(count, sizeof(count), "%zu", body_size);
        if (setenv("REQUEST_METHOD", method, 1) || setenv("QUERY_STRING", query ? query : "", 1) ||
            setenv("CONTENT_LENGTH", count, 1) ||
            setenv("CONTENT_TYPE", !strcmp(method, "POST") ? "application/x-www-form-urlencoded" : "", 1) ||
            setenv("CSAPP_FULL_HTTP", "1", 1)) _exit(126);
        struct sigaction default_action = {0}; default_action.sa_handler = SIG_DFL;
        sigemptyset(&default_action.sa_mask);
        if (sigaction(SIGCHLD, &default_action, NULL) || sigaction(SIGALRM, &default_action, NULL)) _exit(126);
        sigset_t mask; sigemptyset(&mask);
        if (sigprocmask(SIG_SETMASK, &mask, NULL)) _exit(126);
        alarm(5);
        execlp(program, program, "--cgi", (char *)NULL);
        const char failure[] = "HTTP/1.0 502 Bad Gateway\r\nContent-Length: 11\r\nConnection: close\r\n\r\nBad Gateway";
        (void)write_all(STDOUT_FILENO, failure, sizeof(failure) - 1); _exit(127);
    }
    close(input[0]);
    int rc = write_all(input[1], body, body_size), saved = errno;
    close(input[1]);
    /* A CGI may reject POST early, close stdin, then send its own response.
     * EPIPE is not permission to kill that response. Other transfer failures
     * cancel this child; the handler owns it in either case, and alarm bounds
     * its remaining lifetime even when it elects not to consume stdin. */
    if (rc && saved != EPIPE) (void)kill(child, SIGKILL);
    return 1;
}
static int serve_cgi(const char *root, const char *program, int limit) {
    sigset_t block, old_mask, running;
    struct sigaction action = {0}, old_action;
    sigemptyset(&block); sigaddset(&block, SIGCHLD);
    action.sa_handler = child_handler; sigemptyset(&action.sa_mask); action.sa_flags = SA_RESTART;
    if (sigprocmask(SIG_BLOCK, &block, &old_mask)) return 1;
    if (sigaction(SIGCHLD, &action, &old_action)) {
        (void)sigprocmask(SIG_SETMASK, &old_mask, NULL); return 1;
    }
    running = old_mask; sigdelset(&running, SIGCHLD);
    reaped = 0; reap_max_batch = 0;
    int listener = socket(AF_INET, SOCK_STREAM, 0), accepted = 0, spawned = 0, failed = 0;
    struct sockaddr_in address = {0}; address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    socklen_t address_size = sizeof(address);
    if (listener < 0 || bind(listener, (struct sockaddr *)&address, sizeof(address)) ||
        listen(listener, 16) || getsockname(listener, (struct sockaddr *)&address, &address_size)) failed = 1;
    if (!failed) {
        printf("LISTEN 127.0.0.1 %u\n", (unsigned)ntohs(address.sin_port)); fflush(stdout);
        long long deadline = now_ms() + 120000;
        while (accepted < limit) {
            if (sigprocmask(SIG_SETMASK, &running, NULL) || !io_ready(listener, POLLIN, deadline)) { failed = 1; break; }
            int fd = accept(listener, NULL, NULL);
            if (fd < 0 && errno == EINTR) continue;
            if (fd < 0) { failed = 1; break; }
            ++accepted;
            if (sigprocmask(SIG_BLOCK, &block, NULL)) { close(fd); failed = 1; break; }
            int rc = dispatch_cgi(fd, listener, root, program);
            close(fd); /* Child owns the remaining connected socket reference. */
            if (rc > 0) ++spawned;
            else if (rc < 0) failed = 1;
        }
    }
    if (listener >= 0) close(listener);
    if (sigprocmask(SIG_BLOCK, &block, NULL)) failed = 1;
    while (reaped < spawned) sigsuspend(&running);
    printf("CGI accepted=%d spawned=%d reaped=%d max-batch=%d\n",
           accepted, spawned, (int)reaped, (int)reap_max_batch); fflush(stdout);
    if (sigaction(SIGCHLD, &old_action, NULL) || sigprocmask(SIG_SETMASK, &old_mask, NULL)) failed = 1;
    return failed || accepted != limit;
}

int main(int argc, char **argv) {
    struct sigaction ignore = {0}; ignore.sa_handler = SIG_IGN;
    sigemptyset(&ignore.sa_mask);
    if (sigaction(SIGPIPE, &ignore, NULL)) return 1;
    if (argc == 2 && !strcmp(argv[1], "--cgi")) return cgi_main();
    if (argc >= 3 && argc <= 5 && !strcmp(argv[1], "--serve-cgi")) {
        long limit = 1;
        if (argc >= 4 && (!integer(argv[3], &limit) || limit < 1 || limit > 1000)) return 2;
        return serve_cgi(argv[2], argc == 5 ? argv[4] : argv[0], (int)limit);
    }
    if (argc != 1) { fputs("usage: ch11_http [--cgi | --serve-cgi ROOT [REQUESTS [CGI_PROGRAM]]]\n", stderr); return 2; }
    const char *req = "GET /cgi-bin/adder?15000&213 HTTP/1.0\r\n\r\n";
    char *response; size_t len;
    if (build_response(req, strlen(req), ".", &response, &len)) return 1;
    int valid;
    /* Verify payload by locating the boundary in a NUL-terminated test copy. */
    char *copy = malloc(len + 1);
    if (!copy) { free(response); return 1; }
    memcpy(copy, response, len); copy[len] = 0;
    valid = strstr(copy, "\r\n\r\n<p>15000 + 213 = 15213</p>\n") != NULL;
    free(copy); free(response); if (!valid) return 1;
    int pair[2]; if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair)) return 1;
    if (write_all(pair[0], req, strlen(req)) || shutdown(pair[0], SHUT_WR) || handle(pair[1], ".")) return 1;
    close(pair[0]); close(pair[1]);
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair)) return 1;
    close(pair[1]); errno = 0;
    int broken = write_all(pair[0], "x", 1); close(pair[0]);
    if (broken != -1 || errno != EPIPE || reaper_test()) return 1;
    puts("http core: adder=15213 framing=bounded SIGPIPE=survived child=reaped");
    return 0;
}
