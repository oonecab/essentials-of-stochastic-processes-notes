/* Exercise 3.33: C models of two memory-update orders, not x86 execution.
 * Runtime checks state the little-endian, 8-bit-byte LP64 assumptions. */
#include <limits.h>
#include <stdio.h>

static int source_order(int b, short a, long *v, char *u) {
    *u += a;
    *v += b;
    return sizeof a + sizeof b;
}

static int assembly_order(int b, short a, long *v, char *u) {
    *v += b;
    *u += a;
    return sizeof a + sizeof b;
}

int main(void) {
    const unsigned one = 1;
    if (CHAR_BIT != 8 || sizeof(long) != 8 || sizeof(int) != 4 ||
        sizeof(short) != 2 || *(const unsigned char *)&one != 1 ||
        CHAR_MIN != -128 || CHAR_MAX != 127) {
        fputs("requires little-endian LP64 with signed 8-bit char\n", stderr);
        return 2;
    }
    long x = 255, y = 255;
    int sx = source_order(1, 1, &x, (char *)&x);
    int sy = assembly_order(1, 1, &y, (char *)&y);
    if (sx != 6 || sy != 6 || x != 1 || y != 257) {
        fprintf(stderr, "alias mismatch: source=%ld assembly=%ld\n", x, y);
        return 1;
    }
    long a = 255, b = 255;
    char ca = -1, cb = -1;
    sx = source_order(1, 1, &a, &ca);
    sy = assembly_order(1, 1, &b, &cb);
    if (sx != 6 || sy != 6 || a != 256 || b != 256 || ca != 0 || cb != 0) {
        fputs("independent objects mismatch\n", stderr);
        return 1;
    }
    puts("alias source-order=1 assembly-order=257 independent-long=256 independent-char=0 checks=2");
    return 0;
}
