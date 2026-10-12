#include "array_input.h"

/* fig2.9: use A[0] as a sentinel so a failed search returns index 0. */
static size_t binary_search_with_sentinel(int64_t *a, size_t n, int64_t x)
{
    long low = 1, high = (long)n, mid;

    a[0] = x;
    do {
        mid = (low + high) / 2;
        if (low > high) {
            mid = 0;
        } else if (a[mid] < x) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    } while (a[mid] != x);
    return (size_t)mid;
}

int main(int argc, char *argv[])
{
    int64_t x, *a;
    size_t n, position;

    if (argc < 2) {
        fprintf(stderr, "用法：%s 目标值 [已排序整数1 ...]\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (!parse_int64(argv[1], &x) ||
        !read_array(argc, argv, 2, 100000, &a, &n)) {
        fprintf(stderr, "目标值或数组元素无效。\n");
        return EXIT_FAILURE;
    }
    for (size_t i = 2; i <= n; ++i) {
        if (a[i - 1] > a[i]) {
            fprintf(stderr, "数组必须按非降序排列。\n");
            free(a);
            return EXIT_FAILURE;
        }
    }

    position = binary_search_with_sentinel(a, n, x);
    if (position == 0) {
        puts("未找到（返回 0）。");
    } else {
        printf("找到：位置 %zu（从 1 开始）。\n", position);
    }
    free(a);
    return EXIT_SUCCESS;
}
