/* Exact six-dimensional example, with a deliberately bounded integer CLI. */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct { int64_t n, d; } Rational;
typedef struct { Rational c[6]; } Element;

static int64_t gcd(int64_t a, int64_t b) {
    if (a < 0) a = -a;
    while (b) { int64_t r = a % b; a = b; b = r; }
    return a;
}

static Rational rat(int64_t n, int64_t d) {
    /* All callers construct nonzero positive denominators in this example. */
    int64_t g = gcd(n, d);
    Rational r = {n / g, d / g};
    return r;
}

static Rational radd(Rational a, Rational b) {
    return rat(a.n * b.d + b.n * a.d, a.d * b.d);
}

static Rational rmul(Rational a, Rational b) {
    return rat(a.n * b.n, a.d * b.d);
}

static Element zero(void) {
    Element a;
    for (int i = 0; i < 6; ++i) a.c[i] = rat(0, 1);
    return a;
}

static Element basis(int i) {
    Element a = zero(); a.c[i] = rat(1, 1); return a;
}

static Element add(Element a, Element b) {
    for (int i = 0; i < 6; ++i) a.c[i] = radd(a.c[i], b.c[i]);
    return a;
}

static Element scale(Element a, Rational c) {
    for (int i = 0; i < 6; ++i) a.c[i] = rmul(a.c[i], c);
    return a;
}

static Element mul(Element a, Element b) {
    Element out = zero();
    for (int i = 0; i < 6; ++i) for (int j = 0; j < 6; ++j) {
        int tp = i % 3 + j % 3, sp = i / 3 + j / 3, factor = 1;
        if (tp >= 3) { tp -= 3; factor *= 2; }
        if (sp >= 2) { sp -= 2; factor *= -3; }
        int at = tp + 3 * sp;
        out.c[at] = radd(out.c[at], rmul(rmul(a.c[i], b.c[j]), rat(factor, 1)));
    }
    return out;
}

static Element automorphism(Element a, int k, int sign) {
    Element one = basis(0), t = basis(1), s = basis(3);
    Element zeta = scale(add(scale(one, rat(-1, 1)), s), rat(1, 2));
    Element zp = one;
    for (int i = 0; i < k; ++i) zp = mul(zp, zeta);
    Element ti = mul(t, zp), si = scale(s, rat(sign, 1));
    Element images[6]; images[0] = one; images[1] = ti; images[2] = mul(ti, ti);
    for (int i = 0; i < 3; ++i) images[i + 3] = mul(images[i], si);
    Element out = zero();
    for (int i = 0; i < 6; ++i) out = add(out, scale(images[i], a.c[i]));
    return out;
}

static void show(Element a) {
    putchar('[');
    for (int i = 0; i < 6; ++i) {
        printf("%s%" PRId64, i ? "," : "", a.c[i].n);
        if (a.c[i].d != 1) printf("/%" PRId64, a.c[i].d);
    }
    putchar(']');
}

static int parse(const char *s, int *value) {
    size_t len = strlen(s), at = s[0] == '-' ? 1U : 0U;
    if (len <= at || len - at > 3) return 0;
    int v = 0;
    for (size_t i = at; i < len; ++i) {
        if (s[i] < '0' || s[i] > '9') return 0;
        v = v * 10 + s[i] - '0';
    }
    if (v > 100) return 0;
    *value = at ? -v : v;
    return 1;
}

int main(int argc, char **argv) {
    Element a = zero();
    if (argc != 1 && argc != 7) {
        fputs("usage: galois [a b c d e f], six integers -100..100\n", stderr);
        return 2;
    }
    for (int i = 0; i < 6; ++i) {
        int value = 1;
        if (argc == 7 && !parse(argv[i + 1], &value)) {
            fputs("coefficients must be integers in -100..100\n", stderr);
            return 2;
        }
        a.c[i] = rat(value, 1);
    }
    puts("basis=1,t,t^2,s,ts,t^2s; t^3=2; s^2=-3");
    printf("input="); show(a); putchar('\n');
    Element trace = zero();
    for (int k = 0; k < 3; ++k) for (int sign = 1; sign >= -1; sign -= 2) {
        Element value = automorphism(a, k, sign);
        trace = add(trace, value);
        printf("sigma(%d,%d) roots=", k, sign);
        for (int j = 0; j < 3; ++j) printf("%s%d", j ? "," : "", (k + sign * j + 3) % 3 + 1);
        printf(" value="); show(value); putchar('\n');
    }
    printf("trace="); show(trace); putchar('\n');
    printf("z*conjugate(z)="); show(mul(a, automorphism(a, 0, -1))); putchar('\n');
    return 0;
}
