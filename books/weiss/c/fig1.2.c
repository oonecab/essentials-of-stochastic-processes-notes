#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* fig1.2: F(0) = 0; F(n) = 2 * F(n - 1) + n * n. */
static int64_t f(unsigned int n)
{
    if (n == 0) {
        return 0;
    }
    return 2 * f(n - 1) + (int64_t)n * n;
}

int main(int argc, char *argv[])
{
    char *end;
    long n;

    if (argc != 2) {
        fprintf(stderr, "用法：%s N（0 <= N <= 60）\n", argv[0]);
        return EXIT_FAILURE;
    }

    errno = 0;
    n = strtol(argv[1], &end, 10);
    if (errno != 0 || end == argv[1] || *end != '\0' || n < 0 || n > 60) {
        fprintf(stderr, "N 必须是 0 到 60 之间的整数。\n");
        return EXIT_FAILURE;
    }

    printf("F(%ld) = %" PRId64 "\n", n, f((unsigned int)n));
    return EXIT_SUCCESS;
}
