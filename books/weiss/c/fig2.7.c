#include "array_input.h"

static int64_t max3(int64_t a, int64_t b, int64_t c)
{
    int64_t max = a > b ? a : b;
    return max > c ? max : c;
}

/* Divide-and-conquer maximum subsequence sum (fig2.7). */
static int64_t max_sub_sum(const int64_t *a, size_t left, size_t right)
{
    size_t center;
    int64_t max_left_sum, max_right_sum;
    int64_t max_left_border_sum = 0, max_right_border_sum = 0;
    int64_t left_border_sum = 0, right_border_sum = 0;

    if (left == right) {
        return a[left] > 0 ? a[left] : 0;
    }

    center = left + (right - left) / 2;
    max_left_sum = max_sub_sum(a, left, center);
    max_right_sum = max_sub_sum(a, center + 1, right);

    for (size_t i = center + 1; i > left; ) {
        --i;
        left_border_sum += a[i];
        if (left_border_sum > max_left_border_sum) {
            max_left_border_sum = left_border_sum;
        }
    }
    for (size_t i = center + 1; i <= right; ++i) {
        right_border_sum += a[i];
        if (right_border_sum > max_right_border_sum) {
            max_right_border_sum = right_border_sum;
        }
    }

    return max3(max_left_sum, max_right_sum,
                max_left_border_sum + max_right_border_sum);
}

int main(int argc, char *argv[])
{
    int64_t *a;
    size_t n;
    int64_t result;

    if (argc < 2) {
        fprintf(stderr, "用法：%s 整数1 [整数2 ...]\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (!read_array(argc, argv, 1, 100000, &a, &n)) {
        return EXIT_FAILURE;
    }

    result = max_sub_sum(a, 1, n);
    printf("最大子序列和 = %" PRId64 "\n", result);
    free(a);
    return EXIT_SUCCESS;
}
