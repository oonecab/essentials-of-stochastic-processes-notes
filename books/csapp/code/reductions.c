#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
static uint64_t sum_serial(const uint64_t *a, size_t n) {
    uint64_t acc = 0;
    for (size_t i = 0; i < n; ++i) acc += a[i];
    return acc;
}
static uint64_t sum_two(const uint64_t *a, size_t n) {
    uint64_t acc0 = 0, acc1 = 0;
    size_t i = 0;
    for (; n - i >= 2; i += 2) {
        acc0 += a[i]; acc1 += a[i + 1];
    }
    for (; i < n; ++i) acc0 += a[i];
    return acc0 + acc1;
}
int main(void) {
    uint64_t values[65];
    for (size_t i = 0; i < 65; ++i) values[i] = (uint64_t)i * (uint64_t)i + 3u;
    values[0] = UINT64_MAX;
    const size_t lengths[] = {0, 1, 2, 3, 4, 5, 7, 8, 17, 64, 65};
    for (size_t i = 0; i < sizeof lengths / sizeof lengths[0]; ++i) {
        const size_t n = lengths[i];
        const uint64_t a = sum_serial(values, n), b = sum_two(values, n);
        if (a != b) return 3;
        printf("n=%zu sum=%" PRIu64 "\n", n, b);
    }
    return 0;
}
