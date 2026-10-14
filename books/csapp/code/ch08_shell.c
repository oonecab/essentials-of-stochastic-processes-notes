#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <limits.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/wait.h>
#include <unistd.h>
extern char **environ;
#define JOBS 32
#define LINE 1024
#define ARGS 128
enum state { UNUSED, BACKGROUND, FOREGROUND, STOPPED };
struct job { pid_t pid; int jid; enum state state; char command[LINE]; };
static struct job jobs[JOBS];
static int next_jid = 1;
static volatile sig_atomic_t foreground;
static sigset_t original, waiting;
static int quiet;
static int foreground_status;

/* All job-table access is in main with CHLD/INT/TSTP blocked. */
static void handler(int sig) {
    int saved = errno;
    if ((sig == SIGINT || sig == SIGTSTP) && foreground > 0)
        (void)kill(-(pid_t)foreground, sig);
    errno = saved;
}
static struct job *by_pid(pid_t pid) {
    for (int i = 0; i < JOBS; ++i) if (jobs[i].state && jobs[i].pid == pid) return jobs + i;
    return NULL;
}
static struct job *slot(void) {
    for (int i = 0; i < JOBS; ++i) if (!jobs[i].state) return jobs + i;
    return NULL;
}
static void reap(void) {
    int status; pid_t p;
    for (;;) {
        p = waitpid(-1, &status, WNOHANG | WUNTRACED | WCONTINUED);
        if (p == 0 || (p < 0 && errno == ECHILD)) return;
        if (p < 0) { if (errno == EINTR) continue; perror("waitpid"); return; }
        struct job *j = by_pid(p);
        if (!j) continue;
        if (WIFSTOPPED(status)) {
            j->state = STOPPED;
            if (foreground == p) foreground = 0;
            if (!quiet) printf("Job [%d] %ld stopped by signal %d: %s\n", j->jid,
                (long)p, WSTOPSIG(status), strsignal(WSTOPSIG(status)));
        } else if (WIFCONTINUED(status)) {
            if (j->state == STOPPED) j->state = BACKGROUND;
        } else {
            if (WIFSIGNALED(status) && !quiet)
                printf("Job %ld terminated by signal %d: %s\n", (long)p,
                       WTERMSIG(status), strsignal(WTERMSIG(status)));
            if (foreground == p) { foreground = 0; foreground_status = status; }
            j->state = UNUSED;
        }
    }
}
static void wait_foreground(void) {
    for (;;) {
        reap();
        if (!foreground) return;
        sigsuspend(&waiting);
    }
}
static int launch(char **av, int bg, const char *line) {
    struct job *j = slot();
    if (!j) { fputs("job table full\n", stderr); return -1; }
    if (next_jid == INT_MAX) { fputs("job ID range exhausted\n", stderr); return -1; }
    fflush(NULL);
    pid_t p = fork();
    if (p < 0) { perror("fork"); return -1; }
    if (p == 0) {
        struct sigaction sa; memset(&sa, 0, sizeof sa);
        sa.sa_handler = SIG_DFL; sigemptyset(&sa.sa_mask);
        if (setpgid(0, 0) || sigaction(SIGINT, &sa, NULL) ||
            sigaction(SIGTSTP, &sa, NULL) || sigaction(SIGCHLD, &sa, NULL) ||
            sigprocmask(SIG_SETMASK, &original, NULL)) _exit(126);
        execve(av[0], av, environ);
        static const char error[] = "Command not found or not executable.\n";
        (void)write(STDERR_FILENO, error, sizeof error - 1);
        _exit(127);
    }
    /* Both sides setpgid: the child can reach exec before the parent runs. */
    if (setpgid(p, p) < 0 && errno != EACCES && errno != ESRCH) {
        perror("setpgid"); (void)kill(p, SIGKILL);
        while (waitpid(p, NULL, 0) < 0 && errno == EINTR) {}
        return -1;
    }
    if ((long)p > SIG_ATOMIC_MAX) {
        (void)kill(-p, SIGKILL);
        while (waitpid(p, NULL, 0) < 0 && errno == EINTR) {}
        return -1;
    }
    j->pid = p; j->jid = next_jid++; j->state = bg ? BACKGROUND : FOREGROUND;
    snprintf(j->command, sizeof j->command, "%s", line);
    if (bg) { if (!quiet) printf("[%d] %ld %s\n", j->jid, (long)p, line); }
    else { foreground = (sig_atomic_t)p; wait_foreground(); }
    return 0;
}
static struct job *lookup(const char *arg) {
    int jid = arg[0] == '%'; const char *digits = arg + jid;
    if (!*digits) return NULL;
    for (const char *s = digits; *s; ++s) if (*s < '0' || *s > '9') return NULL;
    char *end; errno = 0; long id = strtol(digits, &end, 10);
    if (errno || *end || id <= 0) return NULL;
    for (int i = 0; i < JOBS; ++i)
        if (jobs[i].state && (jid ? jobs[i].jid == id : (long)jobs[i].pid == id)) return jobs + i;
    return NULL;
}
static int evaluate(char *line) {
    char saved[LINE]; snprintf(saved, sizeof saved, "%s", line);
    char *av[ARGS], *context; int count = 0;
    for (char *s = strtok_r(line, " \t\r\n", &context); s;
         s = strtok_r(NULL, " \t\r\n", &context)) {
        if (count == ARGS - 1) { fputs("too many arguments\n", stderr); return 0; }
        av[count++] = s;
    }
    av[count] = NULL;
    if (!count) return 0;
    int bg = !strcmp(av[count - 1], "&");
    if (bg) av[--count] = NULL;
    if (!count) return 0;
    if (!strcmp(av[0], "quit")) return 1;
    if (!strcmp(av[0], "jobs")) {
        reap();
        for (int i = 0; i < JOBS; ++i) if (jobs[i].state && jobs[i].state != FOREGROUND)
            printf("[%d] %ld %s %s\n", jobs[i].jid, (long)jobs[i].pid,
                   jobs[i].state == STOPPED ? "Stopped" : "Running", jobs[i].command);
        return 0;
    }
    if (!strcmp(av[0], "bg") || !strcmp(av[0], "fg")) {
        struct job *j = count == 2 ? lookup(av[1]) : NULL;
        if (!j) { fputs("No such process or invalid job argument\n", stderr); return 0; }
        int fg = !strcmp(av[0], "fg");
        if (kill(-j->pid, SIGCONT) < 0) { perror("SIGCONT"); reap(); return 0; }
        j->state = fg ? FOREGROUND : BACKGROUND;
        if (fg) { foreground = (sig_atomic_t)j->pid; wait_foreground(); }
        else printf("[%d] %ld %s\n", j->jid, (long)j->pid, j->command);
        return 0;
    }
    (void)launch(av, bg, saved);
    return 0;
}
/* Keep each recorded PID reserved until waitpid: a live child may leave its
 * original group. Signal that group and the direct PID independently. */
static int cleanup(void) {
    int failed = 0, waitable[JOBS] = {0};
    for (int i = 0; i < JOBS; ++i) if (jobs[i].state) {
        if (kill(-jobs[i].pid, SIGKILL) < 0 && errno != ESRCH) {
            perror("cleanup group"); failed = 1;
        }
        if (kill(jobs[i].pid, SIGKILL) == 0 || errno == ESRCH) {
            waitable[i] = 1;
        } else {
            perror("cleanup child"); failed = 1;
        }
    }
    for (int i = 0; i < JOBS; ++i) if (jobs[i].state) {
        pid_t result;
        do { result = waitpid(jobs[i].pid, NULL, waitable[i] ? 0 : WNOHANG); }
        while (result < 0 && errno == EINTR);
        if (result > 0 || (result < 0 && errno == ECHILD)) {
            jobs[i].state = UNUSED;
        } else {
            if (result < 0) perror("cleanup waitpid");
            else fputs("cleanup: child remains alive after signal failure\n", stderr);
            failed = 1;
        }
    }
    if (sigprocmask(SIG_SETMASK, &original, NULL) < 0) {
        perror("cleanup mask"); failed = 1;
    }
    return failed;
}

int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--interactive"))) return 2;
    quiet = argc == 1;
    sigset_t block; sigemptyset(&block);
    sigaddset(&block, SIGCHLD); sigaddset(&block, SIGINT); sigaddset(&block, SIGTSTP);
    if (sigprocmask(SIG_BLOCK, &block, &original)) return 1;
    waiting = original;
    sigdelset(&waiting, SIGCHLD); sigdelset(&waiting, SIGINT); sigdelset(&waiting, SIGTSTP);
    struct sigaction sa; memset(&sa, 0, sizeof sa);
    sa.sa_handler = handler; sa.sa_mask = block;
    if (sigaction(SIGCHLD, &sa, NULL) || sigaction(SIGINT, &sa, NULL) ||
        sigaction(SIGTSTP, &sa, NULL)) { cleanup(); return 1; }
    if (quiet) {
        char *av[] = {"/usr/bin/true", NULL};
        int rc = launch(av, 0, "/usr/bin/true");
        if (rc || foreground || !WIFEXITED(foreground_status) || WEXITSTATUS(foreground_status) || by_pid(getpid())) { cleanup(); return 1; }
        for (int i = 0; i < JOBS; ++i) if (jobs[i].state) { cleanup(); return 1; }
        puts("shell foreground-completed jobs=0");
        return cleanup();
    }
    char line[LINE]; size_t used = 0; int overflow = 0, prompt = 1;
    for (;;) {
        reap();
        if (prompt && isatty(STDIN_FILENO)) { fputs("> ", stdout); fflush(stdout); }
        prompt = 0;
        fd_set ready; FD_ZERO(&ready); FD_SET(STDIN_FILENO, &ready);
        int rc = pselect(STDIN_FILENO + 1, &ready, NULL, NULL, NULL, &waiting);
        if (rc < 0) { if (errno == EINTR) continue; perror("pselect"); break; }
        char c; ssize_t got = read(STDIN_FILENO, &c, 1);
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0) { if (used && !overflow) { line[used] = '\0'; (void)evaluate(line); } break; }
        if (c == '\n') {
            line[used] = '\0';
            if (overflow) fputs("line too long\n", stderr);
            else if (evaluate(line)) break;
            used = 0; overflow = 0; prompt = 1;
        } else if (used < sizeof line - 1) line[used++] = c;
        else overflow = 1;
    }
    return cleanup();
}
