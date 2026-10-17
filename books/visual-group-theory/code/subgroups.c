/* Chapter 6. Exhaustive subsets of D_n, bounded to 2n <= 12. */
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#define MAX_SIZE 12

static int multiply(int a, int b, int n) {
    int k = a % n + (a / n ? -1 : 1) * (b % n);
    k = (k % n + n) % n;
    return k + n * ((a / n + b / n) % 2);
}
static int count_bits(unsigned mask) {
    int count = 0;
    while (mask) { count += (int)(mask & 1u); mask >>= 1; }
    return count;
}
static void print_set(unsigned mask, int size) {
    int first = 1;
    printf("{");
    for (int i = 0; i < size; ++i) if (mask & (1u << i)) {
        printf("%s%d", first ? "" : ",", i); first = 0;
    }
    printf("}");
}
static int cosets(unsigned mask, int n, int right, unsigned result[MAX_SIZE]) {
    int count = 0;
    for (int g = 0; g < 2*n; ++g) {
        unsigned image = 0;
        for (int h = 0; h < 2*n; ++h) if (mask & (1u << h))
            image |= 1u << (right ? multiply(h,g,n) : multiply(g,h,n));
        int i = 0;
        while (i < count && result[i] < image) ++i;
        if (i < count && result[i] == image) continue;
        for (int j = count; j > i; --j) result[j] = result[j-1];
        result[i] = image; ++count;
    }
    return count;
}
int main(int argc, char **argv) {
    int n = 4;
    if (argc > 2) { fprintf(stderr,"error: expected n in 1..6\n"); return 2; }
    if (argc == 2) {
        const char *s = argv[1]; n = 0;
        if (!*s) { fprintf(stderr,"error: empty n\n"); return 2; }
        for (; *s; ++s) {
            if (!isdigit((unsigned char)*s) || n > 6) {
                fprintf(stderr,"error: expected n in 1..6\n"); return 2;
            }
            n = 10*n + *s - '0';
        }
    }
    if (n < 1 || n > 6) { fprintf(stderr,"error: n must be in 1..6\n"); return 2; }
    int size = 2*n, count = 0;
    printf("D%d: index i+n*j means r^i f^j; identity=0\n", n);
    for (unsigned mask = 1; mask < (1u << size); mask += 2) {
        int closed = 1;
        for (int a = 0; a < size && closed; ++a) if (mask & (1u << a))
            for (int b = 0; b < size; ++b) if (mask & (1u << b))
                if (!(mask & (1u << multiply(a,b,n)))) { closed = 0; break; }
        if (!closed) continue;
        /* A nonempty finite product-closed subset of a group contains inverses. */
        unsigned left[MAX_SIZE], right[MAX_SIZE];
        int lc = cosets(mask,n,0,left), rc = cosets(mask,n,1,right), normal = lc == rc;
        for (int k = 0; k < lc && normal; ++k) normal = left[k] == right[k];
        int order = count_bits(mask); ++count;
        printf("H="); print_set(mask,size);
        printf(" order=%d index=%d normal=%s\n", order,size/order,normal ? "yes" : "no");
        printf("L ");
        for (int k = 0; k < lc; ++k) { if (k) printf("|"); print_set(left[k],size); }
        printf("\nR ");
        for (int k = 0; k < rc; ++k) { if (k) printf("|"); print_set(right[k],size); }
        printf("\n");
    }
    printf("subgroups=%d\n",count);
    return 0;
}
