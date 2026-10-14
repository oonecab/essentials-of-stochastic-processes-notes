#define _POSIX_C_SOURCE 200809L
/* Bounded real TCP experiment. C11 syntax, POSIX sockets, loopback only. */
#include <arpa/inet.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

static int ready(int fd, short events) {
    struct pollfd p = {fd, events, 0};
    int rc;
    do { rc = poll(&p, 1, 2000); } while (rc < 0 && errno == EINTR);
    return rc > 0;
}
static int write_all(int fd, const unsigned char *data, size_t n) {
    while (n) {
        if (!ready(fd, POLLOUT)) return -1;
        ssize_t k = write(fd, data, n);
        if (k < 0 && errno == EINTR) continue;
        if (k <= 0) return -1;
        data += (size_t)k; n -= (size_t)k;
    }
    return 0;
}
static ssize_t read_some(int fd, void *buf, size_t cap) {
    if (!ready(fd, POLLIN)) return -1;
    ssize_t n;
    do { n = read(fd, buf, cap); } while (n < 0 && errno == EINTR);
    return n;
}
static int timeout(int fd) {
    struct timeval tv = {2, 0};
    return setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) ||
           setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
}
int main(void) {
    int listener = -1, client = -1, server = -1, rc = 1;
    struct sigaction act = {0}; act.sa_handler = SIG_IGN;
    if (sigemptyset(&act.sa_mask) || sigaction(SIGPIPE, &act, NULL)) return 1;
    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    if (inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr) != 1) return 1;
    addr.sin_port = htons(0); /* Ask the kernel for an unused port. */
    listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0 || bind(listener, (struct sockaddr *)&addr, sizeof(addr)) ||
        listen(listener, 1)) goto done;
    socklen_t len = sizeof(addr);
    if (getsockname(listener, (struct sockaddr *)&addr, &len)) goto done;
    client = socket(AF_INET, SOCK_STREAM, 0);
    if (client < 0 || timeout(client) ||
        connect(client, (struct sockaddr *)&addr, sizeof(addr)) ||
        !ready(listener, POLLIN)) goto done;
    server = accept(listener, NULL, NULL);
    if (server < 0 || timeout(server)) goto done;
    const unsigned char sent[] = {'a', 'b', '\n', 'x', 0, 'y', '\n', 't', 'a', 'i', 'l'};
    if (write_all(client, sent, 2) || write_all(client, sent + 2, sizeof(sent) - 2) ||
        shutdown(client, SHUT_WR)) goto done;
    size_t count = 0; unsigned char block[3]; ssize_t n;
    while ((n = read_some(server, block, sizeof(block))) > 0) {
        count += (size_t)n;
        if (count > sizeof(sent) || write_all(server, block, (size_t)n)) goto done;
    }
    if (n < 0 || count != sizeof(sent) || shutdown(server, SHUT_WR)) goto done;
    unsigned char got[sizeof(sent) + 1]; size_t used = 0;
    while ((n = read_some(client, got + used, sizeof(got) - used)) > 0) {
        used += (size_t)n;
        if (used > sizeof(sent)) goto done;
    }
    if (n < 0 || used != sizeof(sent) || memcmp(sent, got, sizeof(sent))) goto done;
    puts("echo bytes=11 binary=preserved half-close=EOF listener=separate");
    rc = 0;
done:
    if (server >= 0) close(server);
    if (client >= 0) close(client);
    if (listener >= 0) close(listener);
    if (rc) fputs("echo experiment failed\n", stderr);
    return rc;
}
