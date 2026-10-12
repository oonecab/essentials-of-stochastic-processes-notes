#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

static void print_digit(unsigned int digit)
{
    putchar('0' + (int)digit);
}

/* fig1.4: print a non-negative integer one digit at a time. */
static int print_out(long long n)
{
    if (n < 0) {
        fprintf(stderr, "n 是负数。\n");
        return 0;
    }
    if (n < 10) {
        print_digit((unsigned int)n);
    } else {
        print_out(n / 10);
        print_digit((unsigned int)(n % 10));
    }
    return 1;
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
    if (errno != 0 || end == argv[1] || *end != '\0') {
        fprintf(stderr, "N 必须是非负整数。\n");
        return EXIT_FAILURE;
    }

    if (!print_out(n)) {
        return EXIT_FAILURE;
    }
    putchar('\n');
    return EXIT_SUCCESS;
}
