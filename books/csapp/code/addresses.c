#include <stddef.h>
#include <stdio.h>
struct record { char c; long value; short flag; };
/* ASM_BEGIN: compile this function alone for the x86-64 Linux example. */
long affine(long x) { return 3 * x + 7; }
/* ASM_END */
int main(void) {
    printf("long=%zu pointer=%zu int=%zu\n", sizeof(long), sizeof(void *), sizeof(int));
    printf("record=%zu,%zu,%zu size=%zu\n", offsetof(struct record, c),
           offsetof(struct record, value), offsetof(struct record, flag), sizeof(struct record));
    int a[2][3] = {{0, 1, 2}, {3, 4, 5}};
    const unsigned char *base = (const unsigned char *)(const void *)&a;
    const unsigned char *element = (const unsigned char *)(const void *)&a[1][2];
    printf("array-offset=%td value=%d\n", element - base, a[1][2]);
    for (long x = -2; x <= 2; ++x) printf("affine=%ld,%ld\n", x, affine(x));
    return 0;
}
