#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

/* Single-threaded POSIX experiment. No handler prints or edits a job table. */
static volatile sig_atomic_t noticed;
static volatile sig_atomic_t usr1_count;
static volatile sig_atomic_t expired;
static jmp_buf escape;
static void handler(int sig) {
    int saved = errno;
    if (sig == SIGALRM) expired = 1;
    else {
        noticed = 1;
        if (sig == SIGUSR1) ++usr1_count; /* Same signal is blocked in its handler. */
    }
    errno = saved;
}
static void die(const char *s) { perror(s); exit(1); }
static int reap(pid_t p) {
    int status;
    while (waitpid(p, &status, 0) < 0) {
        if (errno != EINTR) die("waitpid");
    }
    return status;
}
static void install(int sig) {
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = handler;
    if (sigemptyset(&sa.sa_mask) || sigaction(sig, &sa, NULL)) die("sigaction");
}
static void inner(void) { longjmp(escape, 2); }
static void outer(void) { inner(); }
int main(void) {
    int x = 9, status;
    pid_t pid = fork();
    if (pid < 0) die("fork");
    if (pid == 0) { --x; _exit(x); }
    status = reap(pid);
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 8 || x != 9) return 1;
    puts("private-copy parent=9 child=8");

    /* exec runs /bin/sh in the same child. The exit status is the observation. */
    fflush(stdout);
    pid = fork();
    if (pid < 0) die("fork");
    if (pid == 0) {
        char *const args[] = {"sh", "-c", "exit 7", NULL};
        char *const env[] = {"PATH=/usr/bin:/bin", NULL};
        execve("/bin/sh", args, env);
        _exit(127);
    }
    status = reap(pid);
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 7) return 1;
    puts("exec-status=7");

    install(SIGUSR1); install(SIGCHLD); install(SIGALRM);
    sigset_t block, before, pending, waiting;
    if (sigemptyset(&block) || sigaddset(&block, SIGUSR1) ||
        sigprocmask(SIG_BLOCK, &block, &before)) die("mask");
    for (int i = 0; i < 5; ++i) if (kill(getpid(), SIGUSR1)) die("kill");
    if (sigpending(&pending)) die("sigpending");
    if (sigismember(&pending, SIGUSR1) != 1 || noticed) return 1;
    waiting = before;
    if (sigdelset(&waiting, SIGUSR1) || sigdelset(&waiting, SIGALRM)) die("sigdelset");
    alarm(3);
    while (!noticed && !expired) sigsuspend(&waiting);
    alarm(0);
    if (expired || usr1_count != 1) return 1;
    if (sigprocmask(SIG_SETMASK, &before, NULL)) die("restore");
    puts("standard-signals sent=5 pending=1 handled=1");

    noticed = 0; expired = 0;
    if (sigemptyset(&block) || sigaddset(&block, SIGCHLD) ||
        sigaddset(&block, SIGALRM) || sigprocmask(SIG_BLOCK, &block, &before)) die("mask");
    fflush(stdout);
    pid = fork();
    if (pid < 0) die("fork");
    if (pid == 0) {
        if (sigprocmask(SIG_SETMASK, &before, NULL)) _exit(126);
        _exit(23);
    }
    /* The registration happens while SIGCHLD is blocked. */
    int registered = 1;
    waiting = before;
    if (sigdelset(&waiting, SIGCHLD) || sigdelset(&waiting, SIGALRM)) die("sigdelset");
    alarm(3);
    while (!noticed && !expired) sigsuspend(&waiting);
    alarm(0);
    if (expired && kill(pid, SIGKILL) < 0 && errno != ESRCH) die("kill timeout");
    status = reap(pid);
    if (sigprocmask(SIG_SETMASK, &before, NULL)) die("restore");
    if (expired || !registered || !WIFEXITED(status) || WEXITSTATUS(status) != 23) return 1;
    puts("mask-register-suspend reaped=1 status=23");
    switch (setjmp(escape)) {
    case 0: outer(); return 1;
    case 2: puts("nonlocal-jump=2"); break;
    default: return 1;
    }
    return 0;
}
