/* Every homomorphism C_m -> C_n is determined by the image of 1. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse(const char *s) {
    size_t length = strlen(s);
    if (!length || length > 2) return -1;
    int value = 0;
    for (size_t i = 0; i < length; ++i) {
        if (s[i] < '0' || s[i] > '9') return -1;
        value = value * 10 + (s[i] - '0');
    }
    return value >= 1 && value <= 12 ? value : -1;
}

static void show(const int *items, int count) {
    putchar('{');
    for (int i = 0; i < count; ++i) printf("%s%d", i ? "," : "", items[i]);
    putchar('}');
}

int main(int argc, char **argv) {
    int m = 12, n = 8;
    if (argc == 3) { m = parse(argv[1]); n = parse(argv[2]); }
    if ((argc != 1 && argc != 3) || m < 1 || n < 1) {
        fputs("usage: homomorphisms [m n], 1 <= m,n <= 12\n", stderr);
        return 2;
    }
    printf("C%d -> C%d\n", m, n);
    int count = 0;
    for (int k = 0; k < n; ++k) {
        if (m * k % n != 0) continue; /* m*1=0 must remain true. */
        int values[12], kernel[12], image[12], used[12] = {0};
        int nk = 0, ni = 0;
        for (int x = 0; x < m; ++x) {
            values[x] = x * k % n;
            used[values[x]] = 1;
            if (values[x] == 0) kernel[nk++] = x;
        }
        for (int y = 0; y < n; ++y) if (used[y]) image[ni++] = y;
        ++count;
        printf("k=%d values=", k); show(values, m); putchar('\n');
        printf("kernel="); show(kernel, nk); printf(" image="); show(image, ni);
        printf(" injective=%s surjective=%s\n", nk == 1 ? "yes" : "no", ni == n ? "yes" : "no");
        for (int j = 0; j < ni; ++j) {
            int fiber[12], nf = 0;
            for (int x = 0; x < m; ++x) if (values[x] == image[j]) fiber[nf++] = x;
            printf("fiber "); show(fiber, nf); printf(" -> %d\n", image[j]);
        }
    }
    printf("homomorphisms=%d\n", count);
    return 0;
}
