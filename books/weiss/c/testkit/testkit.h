#ifndef WEISS_TESTKIT_H
#define WEISS_TESTKIT_H

#include <stddef.h>

/* Tests are registered before main and run explicitly by tk_run_all(). */
#define TK_MAX_TESTS 1024
#define TK_OUTPUT_LIMIT (1u << 20)

struct tk_result {
    int exit_status;       /* -1 if the command was killed by a signal */
    int signal_number;     /* 0 if the command exited normally */
    int timed_out;
    int output_truncated;
    char *output;          /* owned by the caller of tk_run_command() */
    size_t output_length;
};

typedef void (*tk_unit_fn)(void);
typedef void (*tk_system_fn)(const struct tk_result *result);

void tk_register_unit(const char *name, const char *location, tk_unit_fn test);
void tk_register_system(const char *name, const char *location,
                        int expected_exit, const char *const argv[],
                        tk_system_fn test);
int tk_run_all(void);
int tk_run_named(const char *name, int inline_debug);
struct tk_result tk_run_command(const char *const argv[]);
void tk_free_result(struct tk_result *result);
_Noreturn void tk_fail(const char *condition, const char *file, int line,
                       const char *format, ...);

#define tk_assert(condition, ...) \
    do { \
        if (!(condition)) { \
            tk_fail(#condition, __FILE__, __LINE__, __VA_ARGS__); \
        } \
    } while (0)

#define TK_STRINGIFY_INNER(value) #value
#define TK_STRINGIFY(value) TK_STRINGIFY_INNER(value)
#define TK_LOCATION __FILE__ ":" TK_STRINGIFY(__LINE__)

/* A test body can call tk_run_command() to check relationships across runs. */
#define UnitTest(name) \
    static void tk_unit_##name(void); \
    static void tk_register_##name(void) __attribute__((constructor)); \
    static void tk_register_##name(void) \
    { \
        tk_register_unit(#name, TK_LOCATION, tk_unit_##name); \
    } \
    static void tk_unit_##name(void)

/* argv[0] is the executable path; expected_exit is checked by TestKit. */
#define SystemTest(name, expected_exit, ...) \
    static const char *const tk_argv_##name[] = { __VA_ARGS__, NULL }; \
    static void tk_system_##name(const struct tk_result *result); \
    static void tk_register_##name(void) __attribute__((constructor)); \
    static void tk_register_##name(void) \
    { \
        tk_register_system(#name, TK_LOCATION, expected_exit, \
                           tk_argv_##name, tk_system_##name); \
    } \
    static void tk_system_##name(const struct tk_result *result)

#endif
