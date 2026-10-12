#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

#define SAMPLE_N 7
#define CUTOFF 3

static void swap(int *a, int *b) { int tmp = *a; *a = *b; *b = tmp; }

static void print_array(const int *a, int n)
{
    for (int i = 1; i <= n; ++i) printf("%d%s", a[i], i == n ? "\n" : " ");
}

static void insertion_sort(int *a, int n)
{
    a[0] = INT_MIN;
    for (int p = 2; p <= n; ++p) {
        int tmp = a[p], j = p;
        while (tmp < a[j - 1]) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = tmp;
    }
}

static void insertion_sort_range(int *a, int left, int right)
{
    for (int p = left + 1; p <= right; ++p) {
        int tmp = a[p], j = p;
        while (j > left && tmp < a[j - 1]) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = tmp;
    }
}

static void shellsort(int *a, int n)
{
    for (int gap = n / 2; gap > 0; gap /= 2)
        for (int i = gap + 1; i <= n; ++i) {
            int tmp = a[i], j = i;
            while (j - gap > 0 && tmp < a[j - gap]) {
                a[j] = a[j - gap];
                j -= gap;
            }
            a[j] = tmp;
        }
}

static void perc_down(int *a, int i, int n)
{
    int tmp = a[i];
    while (2 * i <= n) {
        int child = 2 * i;
        if (child != n && a[child + 1] > a[child]) ++child;
        if (tmp >= a[child]) break;
        a[i] = a[child];
        i = child;
    }
    a[i] = tmp;
}

static void heap_sort_fig(int *a, int n)
{
    for (int i = n / 2; i >= 1; --i) perc_down(a, i, n);
    for (int i = n; i >= 2; --i) {
        swap(&a[1], &a[i]);
        perc_down(a, 1, i - 1);
    }
}

static void merge(int *a, int *tmp, int left, int right_start, int right_end)
{
    int left_end = right_start - 1, pos = left;
    int count = right_end - left + 1; /* Missing assignment in fig7.10. */
    while (left <= left_end && right_start <= right_end)
        tmp[pos++] = a[left] < a[right_start] ? a[left++] : a[right_start++];
    while (left <= left_end) tmp[pos++] = a[left++];
    while (right_start <= right_end) tmp[pos++] = a[right_start++];
    for (int i = 0; i < count; ++i, --right_end) a[right_end] = tmp[right_end];
}

static void msort(int *a, int *tmp, int left, int right)
{
    if (left >= right) return;
    int center = left + (right - left) / 2;
    msort(a, tmp, left, center);
    msort(a, tmp, center + 1, right);
    merge(a, tmp, left, center + 1, right);
}

static int median3(int *a, int left, int right)
{
    int center = left + (right - left) / 2;
    if (a[left] > a[center]) swap(&a[left], &a[center]);
    if (a[left] > a[right]) swap(&a[left], &a[right]);
    if (a[center] > a[right]) swap(&a[center], &a[right]);
    swap(&a[center], &a[right - 1]);
    return a[right - 1];
}

static int partition_median(int *a, int left, int right)
{
    int pivot = median3(a, left, right);
    int i = left, j = right - 1;
    for (;;) {
        while (a[++i] < pivot) {}
        while (a[--j] > pivot) {}
        if (i >= j) break;
        swap(&a[i], &a[j]);
    }
    swap(&a[i], &a[right - 1]);
    return i;
}

/* fig7.15's alternate partition starts just inside the sentinel positions. */
static int partition_alternate(int *a, int left, int right)
{
    int pivot = median3(a, left, right);
    int i = left + 1, j = right - 2;
    for (;;) {
        while (a[i] < pivot) ++i;
        while (a[j] > pivot) --j;
        if (i >= j) break;
        swap(&a[i++], &a[j--]);
    }
    swap(&a[i], &a[right - 1]);
    return i;
}

static void qsort_part(int *a, int left, int right)
{
    if (left + CUTOFF > right) return;
    int pivot_index = partition_median(a, left, right);
    qsort_part(a, left, pivot_index - 1);
    qsort_part(a, pivot_index + 1, right);
}

static void quicksort(int *a, int n)
{
    qsort_part(a, 1, n);
    insertion_sort(a, n);
}

static void qselect(int *a, int k, int left, int right)
{
    if (left + CUTOFF > right) {
        insertion_sort_range(a, left, right);
        return;
    }
    int pivot_index = partition_median(a, left, right);
    if (k < pivot_index) qselect(a, k, left, pivot_index - 1);
    else if (k > pivot_index) qselect(a, k, pivot_index + 1, right);
}

int weiss_run_ch7(int number)
{
    int a[SAMPLE_N + 1] = {0, 5, 2, 9, 1, 3, 7, 4};
    int tmp[SAMPLE_N + 1] = {0};
    switch (number) {
    case 2: insertion_sort(a, SAMPLE_N); break;
    case 4: shellsort(a, SAMPLE_N); break;
    case 8: heap_sort_fig(a, SAMPLE_N); break;
    case 9: msort(a, tmp, 1, SAMPLE_N); break;
    case 10: {
        int halves[SAMPLE_N + 1] = {0, 1, 5, 9, 2, 3, 4, 7};
        for (int i = 1; i <= SAMPLE_N; ++i) a[i] = halves[i];
        merge(a, tmp, 1, 4, SAMPLE_N);
        break;
    }
    case 12: quicksort(a, SAMPLE_N); break;
    case 13: printf("Median3 pivot = %d\n", median3(a, 1, SAMPLE_N)); return 0;
    case 14: qsort_part(a, 1, SAMPLE_N); insertion_sort(a, SAMPLE_N); break;
    case 15: printf("Alternate partition pivot index = %d\n", partition_alternate(a, 1, SAMPLE_N)); return 0;
    case 16: qselect(a, 4, 1, SAMPLE_N); printf("4th smallest = %d\n", a[4]); return 0;
    default: fprintf(stderr, "unknown chapter 7 figure: %d\n", number); return 1;
    }
    print_array(a, SAMPLE_N);
    return 0;
}
