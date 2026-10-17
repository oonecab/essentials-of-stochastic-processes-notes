/* Chapter 5. p*q applies p first and q second. C11; no dependencies. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#define MAX_N 8

typedef struct { int n; int to[MAX_N]; } Perm;

static int parse(const char *text, Perm *p) {
    const char *s = text;
    p->n = 0;
    while (*s) {
        if (p->n == MAX_N || !isdigit((unsigned char)*s)) return 0;
        int value = 0;
        while (isdigit((unsigned char)*s)) {
            value = value * 10 + (*s++ - '0');
            if (value > MAX_N) return 0;
        }
        if (value < 1) return 0;
        p->to[p->n++] = value - 1;
        if (!*s) break;
        if (*s++ != ',' || !*s) return 0;
    }
    if (p->n == 0) return 0;
    int seen[MAX_N] = {0};
    for (int i = 0; i < p->n; ++i) {
        int v = p->to[i];
        if (v >= p->n || seen[v]) return 0;
        seen[v] = 1;
    }
    return 1;
}

static Perm compose(Perm p, Perm q) {
    Perm r = p;
    for (int i = 0; i < p.n; ++i) r.to[i] = q.to[p.to[i]];
    return r;
}
static Perm inverse(Perm p) {
    Perm q = p;
    for (int i = 0; i < p.n; ++i) q.to[p.to[i]] = i;
    return q;
}
static int gcd(int a, int b) {
    while (b) { int r = a % b; a = b; b = r; }
    return a;
}
static void describe(const char *label, Perm p) {
    printf("%s ", label);
    for (int i = 0; i < p.n; ++i) printf("%s%d", i ? "," : "", p.to[i] + 1);
    printf(" ");
    int seen[MAX_N] = {0}, order = 1, printed = 0, inversions = 0;
    for (int i = 0; i < p.n; ++i) {
        if (seen[i]) continue;
        int part[MAX_N], size = 0, x = i;
        while (!seen[x]) { seen[x] = 1; part[size++] = x; x = p.to[x]; }
        order = order / gcd(order, size) * size;
        if (size > 1) {
            printf("(");
            for (int j = 0; j < size; ++j) printf("%s%d", j ? " " : "", part[j] + 1);
            printf(")");
            printed = 1;
        }
    }
    if (!printed) printf("()");
    for (int i = 0; i < p.n; ++i)
        for (int j = i + 1; j < p.n; ++j) inversions += p.to[i] > p.to[j];
    printf(" order=%d sign=%d\n", order, inversions % 2 ? -1 : 1);
}
int main(int argc, char **argv) {
    Perm p, q;
    const char *a = "2,3,4,1", *b = "2,1,3,4";
    if (argc == 3) { a = argv[1]; b = argv[2]; }
    else if (argc != 1) { fprintf(stderr, "error: expected two permutations\n"); return 2; }
    if (!parse(a, &p) || !parse(b, &q) || p.n != q.n) {
        fprintf(stderr, "error: permutations must contain 1..n exactly once; 1 <= n <= 8\n");
        return 2;
    }
    describe("p", p); describe("q", q);
    describe("p*q", compose(p,q)); describe("q*p", compose(q,p));
    describe("p^-1", inverse(p)); describe("p^2", compose(p,p));
    return 0;
}
