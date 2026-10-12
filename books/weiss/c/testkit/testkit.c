#define _POSIX_C_SOURCE 200809L

#include "testkit.h"

#include <errno.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define TK_COMMAND_TIMEOUT_SEC 5
#define TK_CASE_TIMEOUT_SEC 30

enum tk_kind { TK_UNIT, TK_SYSTEM };

struct tk_testcase {
    const char *name;
    const char *location;
    enum tk_kind kind;
    int expected_exit;
    const char *const *argv;
    tk_unit_fn unit;
    tk_system_fn system;
};

static struct tk_testcase tests[TK_MAX_TESTS];
static size_t test_count;

_Noreturn void tk_fail(const char *condition, const char *file, int line,
                       const char *format, ...)
{
    va_list args;

    fprintf(stderr, "Assertion failed: %s (%s:%d)\n", condition, file, line);
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
    fputc('\n', stderr);
    abort();
}

static void tk_add_test(struct tk_testcase test)
{
    tk_assert(test_count < TK_MAX_TESTS, "Too many tests (limit %d)",
              TK_MAX_TESTS);
    tk_assert(test.name != NULL && test.location != NULL,
              "A test needs a name and location");
    tests[test_count++] = test;
}

void tk_register_unit(const char *name, const char *location, tk_unit_fn test)
{
    tk_assert(test != NULL, "Unit test %s has no body", name);
    tk_add_test((struct tk_testcase){
        .name = name, .location = location, .kind = TK_UNIT, .unit = test
    });
}

void tk_register_system(const char *name, const char *location,
                        int expected_exit, const char *const argv[],
                        tk_system_fn test)
{
    tk_assert(argv != NULL && argv[0] != NULL,
              "System test %s has no executable", name);
    tk_assert(test != NULL, "System test %s has no body", name);
    tk_add_test((struct tk_testcase){
        .name = name, .location = location, .kind = TK_SYSTEM,
        .expected_exit = expected_exit, .argv = argv, .system = test
    });
}

static int tk_wait(pid_t pid)
{
    int status;
    pid_t waited;

    do {
        waited = waitpid(pid, &status, 0);
    } while (waited == -1 && errno == EINTR);
    tk_assert(waited == pid, "waitpid failed: %s", strerror(errno));
    return status;
}

static void tk_capture(int fd, char *output, size_t *length, int *truncated)
{
    char chunk[4096];
    ssize_t count;

    *length = 0;
    *truncated = 0;
    for (;;) {
        count = read(fd, chunk, sizeof(chunk));
        if (count == 0) {
            break;
        }
        if (count < 0) {
            if (errno == EINTR) {
                continue;
            }
            tk_fail("read", __FILE__, __LINE__, "%s", strerror(errno));
        }
        size_t available = TK_OUTPUT_LIMIT - *length;
        size_t keep = (size_t)count < available ? (size_t)count : available;
        memcpy(output + *length, chunk, keep);
        *length += keep;
        if (keep < (size_t)count) {
            *truncated = 1;
        }
    }
    output[*length] = '\0';
}

struct tk_result tk_run_command(const char *const argv[])
{
    int fds[2];
    pid_t pid;
    int status;
    struct tk_result result = {0};

    tk_assert(argv != NULL && argv[0] != NULL, "Missing executable");
    tk_assert(pipe(fds) == 0, "pipe failed: %s", strerror(errno));
    fflush(NULL);
    pid = fork();
    tk_assert(pid >= 0, "fork failed: %s", strerror(errno));
    if (pid == 0) {
        close(fds[0]);
        if (dup2(fds[1], STDOUT_FILENO) == -1 ||
            dup2(fds[1], STDERR_FILENO) == -1) {
            _exit(127);
        }
        close(fds[1]);
        alarm(TK_COMMAND_TIMEOUT_SEC);
        execv(argv[0], (char *const *)argv);
        perror(argv[0]);
        _exit(127);
    }

    close(fds[1]);
    result.output = malloc(TK_OUTPUT_LIMIT + 1u);
    tk_assert(result.output != NULL, "Cannot allocate output buffer");
    tk_capture(fds[0], result.output, &result.output_length,
               &result.output_truncated);
    close(fds[0]);
    status = tk_wait(pid);
    result.exit_status = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
    result.signal_number = WIFSIGNALED(status) ? WTERMSIG(status) : 0;
    result.timed_out = result.signal_number == SIGALRM;
    return result;
}

void tk_free_result(struct tk_result *result)
{
    if (result != NULL) {
        free(result->output);
        result->output = NULL;
        result->output_length = 0;
    }
}

static void tk_run_body(const struct tk_testcase *test)
{
    if (test->kind == TK_UNIT) {
        test->unit();
    } else {
        struct tk_result result = tk_run_command(test->argv);

        if (result.output_length != 0) {
            fwrite(result.output, 1, result.output_length, stderr);
            if (result.output[result.output_length - 1] != '\n') {
                fputc('\n', stderr);
            }
        }
        tk_assert(!result.output_truncated,
                  "Output exceeded %u bytes", TK_OUTPUT_LIMIT);
        tk_assert(result.signal_number == 0,
                  "Command terminated by signal %d%s", result.signal_number,
                  result.timed_out ? " (timeout)" : "");
        tk_assert(result.exit_status == test->expected_exit,
                  "Expected exit %d, got %d", test->expected_exit,
                  result.exit_status);
        test->system(&result);
        tk_free_result(&result);
    }
}

static int tk_run_one(const struct tk_testcase *test, int verbose)
{
    int fds[2];
    pid_t pid;
    int status, truncated;
    size_t length;
    char *output;
    int passed;

    tk_assert(pipe(fds) == 0, "pipe failed: %s", strerror(errno));
    fflush(NULL);
    pid = fork();
    tk_assert(pid >= 0, "fork failed: %s", strerror(errno));
    if (pid == 0) {
        close(fds[0]);
        if (dup2(fds[1], STDOUT_FILENO) == -1 ||
            dup2(fds[1], STDERR_FILENO) == -1) {
            _exit(127);
        }
        close(fds[1]);
        setbuf(stdout, NULL);
        setbuf(stderr, NULL);
        alarm(TK_CASE_TIMEOUT_SEC);
        tk_run_body(test);
        fflush(NULL);
        _exit(0);
    }

    close(fds[1]);
    output = malloc(TK_OUTPUT_LIMIT + 1u);
    tk_assert(output != NULL, "Cannot allocate output buffer");
    tk_capture(fds[0], output, &length, &truncated);
    close(fds[0]);
    status = tk_wait(pid);
    passed = WIFEXITED(status) && WEXITSTATUS(status) == 0 && !truncated;

    printf("- [%s] %s (%s)", passed ? "PASS" : "FAIL", test->name,
           test->location);
    if (!passed) {
        if (WIFSIGNALED(status)) {
            printf(" - signal %d%s", WTERMSIG(status),
                   WTERMSIG(status) == SIGALRM ? " (timeout)" : "");
        } else if (WIFEXITED(status)) {
            printf(" - exit %d", WEXITSTATUS(status));
        }
        if (truncated) {
            printf(" - output truncated");
        }
    }
    putchar('\n');
    if ((!passed || verbose) && length != 0) {
        fwrite(output, 1, length, stdout);
        if (output[length - 1] != '\n') {
            putchar('\n');
        }
    }
    free(output);
    return passed;
}

int tk_run_all(void)
{
    size_t passed = 0;
    int verbose = getenv("TK_VERBOSE") != NULL;

    printf("TestKit (%zu cases)\n", test_count);
    for (size_t i = 0; i < test_count; ++i) {
        passed += (size_t)tk_run_one(&tests[i], verbose);
    }
    printf("%zu/%zu test cases passed.\n", passed, test_count);
    return passed == test_count && test_count != 0 ? 0 : 1;
}

int tk_run_named(const char *name, int inline_debug)
{
    tk_assert(name != NULL, "Missing test name");
    for (size_t i = 0; i < test_count; ++i) {
        if (strcmp(tests[i].name, name) == 0) {
            if (inline_debug) {
                printf("Debugging %s (%s)\n", tests[i].name,
                       tests[i].location);
                fflush(stdout);
                tk_run_body(&tests[i]);
                printf("- [PASS] %s\n", tests[i].name);
                return 0;
            }
            return tk_run_one(&tests[i], getenv("TK_VERBOSE") != NULL) ? 0 : 1;
        }
    }
    fprintf(stderr, "Unknown test case: %s\n", name);
    return 2;
}
