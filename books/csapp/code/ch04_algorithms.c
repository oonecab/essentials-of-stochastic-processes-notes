/* Pointer bubblesort and the switch table's mathematical reference. */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

static void bubble_p(int64_t *data, size_t count) {
    if (count < 2) return; /* Avoid forming a pointer before the array. */
    for (int64_t *last = data + count - 1; last > data; --last) {
        for (int64_t *p = data; p < last; ++p) {
            if (p[1] < p[0]) {
                const int64_t t = p[1];
                p[1] = p[0];
                p[0] = t;
            }
        }
    }
}
static uint64_t switchv(int64_t idx) {
    switch (idx) {
    case 0: return 0xaaa;
    case 2: case 5: return 0xbbb;
    case 3: return 0xccc;
    default: return 0xddd;
    }
}
int main(void) {
    int64_t data[] = {5, -2, 5, 0, INT64_MIN, INT64_MAX};
    const size_t count = sizeof data / sizeof data[0];
    bubble_p(data,count);
    printf("sorted:");
    for (size_t i = 0; i < count; ++i) printf(" %" PRId64,data[i]);
    putchar('\n');
    for (int64_t i = -1; i <= 6; ++i)
        printf("idx=%" PRId64 " value=0x%" PRIx64 "\n",i,switchv(i));
    return 0;
}
