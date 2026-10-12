#include "array_input.h"

/* Quadratic-time maximum subsequence sum (fig2.6). */
static int64_t max_subsequence_sum(const int64_t *a, size_t n,
                                   size_t *best_i, size_t *best_j)
{
    int64_t max_sum = 0;

    *best_i = 0;
    *best_j = 0;
    for (size_t i = 1; i <= n; ++i) {
        int64_t this_sum = 0;
        for (size_t j = i; j <= n; ++j) {
            this_sum += a[j];
            if (this_sum > max_sum) {
                max_sum = this_sum;
                *best_i = i;
                *best_j = j;
            }
        }
    }
    return max_sum;
}

int main(int argc, char *argv[])
{
    int64_t *a;
    size_t n, best_i, best_j;
    int64_t result;

    if (argc < 2) {
        fprintf(stderr, "用法：%s 整数1 [整数2 ...]\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (!read_array(argc, argv, 1, 10000, &a, &n)) {
        return EXIT_FAILURE;
    }

    result = max_subsequence_sum(a, n, &best_i, &best_j);
    printf("最大子序列和 = %" PRId64 "；区间 = [%zu, %zu]\n",
           result, best_i, best_j);
    free(a);
    return EXIT_SUCCESS;
}
