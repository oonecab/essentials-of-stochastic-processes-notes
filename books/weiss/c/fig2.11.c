#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* fig2.11: exponentiation by repeated squaring. */
static int power(int64_t x, uint64_t n, int64_t *result)
{
    int64_t square, partial;

    if (n == 0) {
        *result = 1;
        return 1;
    }
    if (n == 1) {
        *result = x;
        return 1;
    }
    if (__builtin_mul_overflow(x, x, &square) ||
        !power(square, n / 2, &partial)) {
        return 0;
    }
    if (n % 2 == 0) {
        *result = partial;
        return 1;
    }
    return !__builtin_mul_overflow(partial, x, result);
}

static int read_int64(const char *text, int64_t *value)
{
    char *end;
    intmax_t parsed;

    errno = 0;
    parsed = strtoimax(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' ||
        parsed < INT64_MIN || parsed > INT64_MAX) {
        return 0;
    }
    *value = (int64_t)parsed;
    return 1;
}

int main(int argc, char *argv[])
{
    int64_t x, n, result;

    if (argc != 3 || !read_int64(argv[1], &x) ||
        !read_int64(argv[2], &n) || n < 0) {
        fprintf(stderr, "用法：%s 整数X 非负指数N\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (!power(x, (uint64_t)n, &result)) {
        fprintf(stderr, "结果超出有符号 64 位整数范围。\n");
        return EXIT_FAILURE;
    }
    printf("Pow = %" PRId64 "\n", result);
    return EXIT_SUCCESS;
}
