#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
extern char **environ;

/* This teaching function requires exclusive use of the stream and its fd. */
char *tfgets(char *s, int n, FILE *stream) {
    if (!s || !stream || n <= 0) { errno = EINVAL; return NULL; }
    if (n == 1) { s[0] = '\0'; return s; }
    int fd = fileno(stream), flags = fcntl(fd, F_GETFL);
    if (flags < 0 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) < 0) return NULL;
    struct timespec start, now;
    int used = 0, ok = 0, err = 0;
    if (clock_gettime(CLOCK_MONOTONIC, &start)) goto restore;
    for (;;) {
        if (clock_gettime(CLOCK_MONOTONIC, &now)) break;
        double left = 5.0 - ((double)(now.tv_sec - start.tv_sec) +
                            (double)(now.tv_nsec - start.tv_nsec) / 1e9);
        if (left <= 0) { errno = ETIMEDOUT; break; }
        errno = 0;
        int ch = fgetc(stream); /* Checks stdio's existing buffer first. */
        if (ch != EOF) {
            s[used++] = (char)ch;
            if (ch == '\n' || used == n - 1) { ok = 1; break; }
            continue;
        }
        if (feof(stream)) { ok = used != 0; break; }
        if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR) break;
        clearerr(stream);
        struct pollfd p = {fd, POLLIN, 0};
        int rc = poll(&p, 1, (int)(left * 1000.0 + 1.0));
        if (rc < 0 && errno != EINTR) break;
    }
restore:
    err = errno;
    s[used] = '\0';
    if (fcntl(fd, F_SETFL, flags) < 0) return NULL;
    errno = err;
    return ok ? s : NULL;
}
int mysystem(char *command) {
    if (!command) { errno = EINVAL; return -1; }
    pid_t p = fork();
    if (p < 0) return -1;
    if (p == 0) {
        char *const av[] = {"sh", "-c", command, NULL};
        execve("/bin/sh", av, environ);
        _exit(127);
    }
    int status;
    while (waitpid(p, &status, 0) < 0) if (errno != EINTR) return -1;
    return WIFEXITED(status) ? WEXITSTATUS(status) : status;
}
static void catch_int(int sig) { (void)sig; }
unsigned int wakeup(unsigned int secs) {
    unsigned int remaining = sleep(secs);
    printf("Woke up at %u secs.\n", secs - remaining);
    return remaining;
}
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--text-fault")) {
#ifdef __linux__
        /* Intentional Linux text-write fault: run only without sanitizers. */
        pid_t children[2]; int made = 0;
        for (int i = 0; i < 2; ++i) {
            pid_t p = fork();
            if (p < 0) break;
            if (p == 0) {
                volatile unsigned char *text = (volatile unsigned char *)(uintptr_t)&main;
                *text = 0; /* Outside defined ISO C; expected Linux protection fault. */
                _exit(99);
            }
            children[made++] = p;
        }
        int failed = made != 2;
        for (int i = 0; i < made; ++i) {
            int status; pid_t r;
            do { r = waitpid(children[i], &status, 0); } while (r < 0 && errno == EINTR);
            if (r < 0 || !WIFSIGNALED(status)) { failed = 1; continue; }
            int sig = WTERMSIG(status);
            fprintf(stderr, "child %ld terminated by signal %d: %s\n",
                    (long)r, sig, strsignal(sig));
            if (sig != SIGSEGV) failed = 1;
        }
        return failed;
#else
        fputs("--text-fault requires the documented Linux experiment\n", stderr);
        return 2;
#endif
    }
    if (argc > 1 && !strcmp(argv[1], "--myecho")) {
        puts("Command-line arguments:");
        for (int i = 1; i < argc; ++i) printf("argv[%d]: %s\n", i - 1, argv[i]);
        puts("Environment variables:");
        for (size_t i = 0; environ[i]; ++i) printf("envp[%zu]: %s\n", i, environ[i]);
        return 0;
    }
    if (argc > 1 && !strcmp(argv[1], "--myls")) {
        argv[1] = (char *)"ls";
        execve("/bin/ls", argv + 1, environ);
        perror("execve /bin/ls"); return 127;
    }
    if (argc == 2 && !strcmp(argv[1], "--tfgets")) {
        char s[256];
        if (tfgets(s, (int)sizeof s, stdin)) { fputs(s, stdout); return 0; }
        return errno == ETIMEDOUT ? 3 : 1;
    }
    if (argc == 3 && !strcmp(argv[1], "--snooze")) {
        char *end; errno = 0; unsigned long value = strtoul(argv[2], &end, 10);
        if (errno || argv[2][0] == '-' || !argv[2][0] || *end || value > 3600) return 2;
        struct sigaction sa; memset(&sa, 0, sizeof sa);
        sa.sa_handler = catch_int;
        if (sigemptyset(&sa.sa_mask) || sigaction(SIGINT, &sa, NULL)) return 1;
        unsigned int secs = (unsigned int)value, remaining = sleep(secs);
        printf("Slept for %u of %u secs.\n", secs - remaining, secs);
        return 0;
    }
    if (argc != 1) return 2;
    int a = mysystem("exit 8"), b = mysystem("exit 0");
    if (a != 8 || b != 0) return 1;
    puts("mysystem exit8=8 exit0=0");
    FILE *f = tmpfile(); char s[8];
    if (!f) return 1;
    fputs("abc\ndef", f); rewind(f);
    if (!tfgets(s, 8, f) || strcmp(s, "abc\n")) return 1;
    if (!tfgets(s, 8, f) || strcmp(s, "def")) return 1;
    if (tfgets(s, 8, f)) return 1;
    fclose(f);
    puts("tfgets line=abc partial=def eof=null");
    return 0;
}
