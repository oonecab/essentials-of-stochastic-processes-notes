#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* fig2.10: Euclid's algorithm. */
static int64_t gcd(int64_t m, int64_t n)
{
    while (n > 0) {
        int64_t rem = m % n;
        m = n;
        n = rem;
    }
    return m;
}

static int read_nonnegative(const char *text, int64_t *value)
{
    char *end;
    intmax_t parsed;

    errno = 0;
    parsed = strtoimax(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || parsed < 0 ||
        parsed > INT64_MAX) {
        return 0;
    }
    *value = (int64_t)parsed;
    return 1;
}

int main(int argc, char *argv[])
{
    int64_t m, n;

    if (argc != 3 || !read_nonnegative(argv[1], &m) ||
        !read_nonnegative(argv[2], &n)) {
        fprintf(stderr, "用法：%s 非负整数M 非负整数N\n", argv[0]);
        return EXIT_FAILURE;
    }
    printf("Gcd = %" PRId64 "\n", gcd(m, n));
    return EXIT_SUCCESS;
}
