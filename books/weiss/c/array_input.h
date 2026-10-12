#ifndef WEISS_ARRAY_INPUT_H
#define WEISS_ARRAY_INPUT_H

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* Bounds keep every partial sum within int64_t for the supported array size. */
#define MAX_ABS_VALUE INT64_C(1000000000)

static int parse_int64(const char *text, int64_t *value)
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

/* Store the input at A[1..n], matching the indexing in the figures. */
static int read_array(int argc, char *argv[], int first_arg, size_t max_count,
                      int64_t **array, size_t *count)
{
    size_t n;
    int64_t *a;

    if (argc < first_arg) {
        return 0;
    }
    n = (size_t)(argc - first_arg);
    if (n > max_count) {
        fprintf(stderr, "最多接受 %zu 个数组元素。\n", max_count);
        return 0;
    }

    a = calloc(n + 1, sizeof(*a));
    if (a == NULL) {
        fprintf(stderr, "无法分配数组内存。\n");
        return 0;
    }
    for (size_t i = 0; i < n; ++i) {
        if (!parse_int64(argv[first_arg + (int)i], &a[i + 1]) ||
            a[i + 1] < -MAX_ABS_VALUE || a[i + 1] > MAX_ABS_VALUE) {
            fprintf(stderr, "数组元素必须是 -1000000000 到 1000000000 之间的整数。\n");
            free(a);
            return 0;
        }
    }

    *array = a;
    *count = n;
    return 1;
}

#endif
