#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

/* fig1.3: Bad(0) = 0; Bad(n) = Bad(n / 3 + 1) + n - 1. */
static long long bad(long long n)
{
    if (n == 0) {
        return 0;
    }
    return bad(n / 3 + 1) + n - 1;
}

int main(int argc, char *argv[])
{
    char *end;
    long long n;

    if (argc != 2) {
        fprintf(stderr, "用法：%s N（N >= 0）\n", argv[0]);
        return EXIT_FAILURE;
    }

    errno = 0;
    n = strtoll(argv[1], &end, 10);
    if (errno != 0 || end == argv[1] || *end != '\0' || n < 0) {
        fprintf(stderr, "N 必须是非负整数。\n");
        return EXIT_FAILURE;
    }

    /* Every positive n eventually reaches 1, and Bad(1) calls itself. */
    if (n > 0) {
        fprintf(stderr, "原公式对正整数不会终止：Bad(1) 会再次调用 Bad(1)。\n");
        return EXIT_FAILURE;
    }

    printf("Bad(%lld) = %lld\n", n, bad(n));
    return EXIT_SUCCESS;
}
