/* Exact finite integration and conditioning. All integer inputs are bounded. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAX_N 8

static int vector(const char *text, int low, int high, int out[MAX_N], int *length) {
    const char *cursor = text;
    int count = 0;
    if (strlen(text) > 127U || *cursor == '\0') return 0;
    for (;;) {
        int sign = 1, value = 0;
        if (count == MAX_N) return 0;
        if (*cursor == '-') { sign = -1; ++cursor; }
        if (*cursor < '0' || *cursor > '9') return 0;
        while (*cursor >= '0' && *cursor <= '9') {
            value = value * 10 + (*cursor - '0');
            if (value > 1000) return 0;
            ++cursor;
        }
        value *= sign;
        if (value < low || value > high) return 0;
        out[count++] = value;
        if (*cursor == '\0') break;
        if (*cursor++ != ',') return 0;
    }
    *length = count;
    return 1;
}

static long long gcd_nonnegative(long long a, long long b) {
    while (b != 0) { long long remainder = a % b; a = b; b = remainder; }
    return a;
}

static void ratio(long long numerator, long long denominator) {
    long long common = gcd_nonnegative(numerator < 0 ? -numerator : numerator, denominator);
    printf("[%lld,%lld]", numerator / common, denominator / common);
}

static void integer_array(const int *values, int n) {
    putchar('[');
    for (int i = 0; i < n; ++i) printf("%s%d", i ? "," : "", values[i]);
    putchar(']');
}

int main(int argc, char **argv) {
    int weights[MAX_N], values[MAX_N], groups[MAX_N], signed_mass[MAX_N];
    int lengths[4], positive[MAX_N], negative[MAX_N], ac[MAX_N], singular[MAX_N];
    long long mass = 0, integral = 0, plus = 0, minus = 0, second = 0, variation = 0;
    int absolutely_continuous = 1;
    if (argc != 5 || !vector(argv[1], 0, 1000, weights, &lengths[0]) ||
        !vector(argv[2], -1000, 1000, values, &lengths[1]) ||
        !vector(argv[3], 0, 7, groups, &lengths[2]) ||
        !vector(argv[4], -1000, 1000, signed_mass, &lengths[3])) {
        fputs("expected four bounded integer vectors\n", stderr); return 2;
    }
    int n = lengths[0];
    for (int k = 1; k < 4; ++k) {
        if (lengths[k] != n) { fputs("vector lengths differ\n", stderr); return 2; }
    }
    for (int i = 0; i < n; ++i) {
        if (groups[i] >= n) { fputs("group label outside space\n", stderr); return 2; }
        long long w = weights[i], v = values[i];
        mass += w; integral += w * v; second += w * v * v;
        plus += w * (v > 0 ? v : 0); minus += w * (v < 0 ? -v : 0);
        positive[i] = signed_mass[i] > 0 ? signed_mass[i] : 0;
        negative[i] = signed_mass[i] < 0 ? -signed_mass[i] : 0;
        variation += (long long)positive[i] + negative[i];
        ac[i] = weights[i] ? signed_mass[i] : 0;
        singular[i] = weights[i] ? 0 : signed_mass[i];
        if (singular[i] != 0) absolutely_continuous = 0;
    }
    if (mass == 0) { fputs("positive total mass required\n", stderr); return 2; }
    printf("{\"mass\":%lld,\"integral\":%lld,\"positive_integral\":%lld,"
           "\"negative_integral\":%lld,\"second_moment_integral\":%lld,\"expectation\":",
           mass, integral, plus, minus, second);
    ratio(integral, mass);
    fputs(",\"block_mass\":[", stdout);
    for (int i = 0; i < n; ++i) {
        long long total = 0;
        for (int j = 0; j < n; ++j) if (groups[j] == groups[i]) total += weights[j];
        printf("%s%lld", i ? "," : "", total);
    }
    fputs("],\"conditional\":[", stdout);
    for (int i = 0; i < n; ++i) {
        long long total = 0, amount = 0;
        for (int j = 0; j < n; ++j) if (groups[j] == groups[i]) {
            total += weights[j]; amount += (long long)weights[j] * values[j];
        }
        if (i != 0) putchar(',');
        ratio(total ? amount : 0, total ? total : 1);
    }
    fputs("],\"jordan_positive\":", stdout); integer_array(positive, n);
    fputs(",\"jordan_negative\":", stdout); integer_array(negative, n);
    printf(",\"variation_total\":%lld,\"ac_masses\":", variation); integer_array(ac, n);
    fputs(",\"singular_masses\":", stdout); integer_array(singular, n);
    fputs(",\"density\":[", stdout);
    for (int i = 0; i < n; ++i) {
        if (i != 0) putchar(',');
        ratio(weights[i] ? signed_mass[i] : 0, weights[i] ? weights[i] : 1);
    }
    printf("],\"absolute_continuous\":%s}\n", absolutely_continuous ? "true" : "false");
    return 0;
}
