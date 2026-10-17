/* Finite model: bits 0..n-1 name points; null in JSON denotes infinity. */
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CAP 256
#define INF (LLONG_MAX / 4)

static int number(const char *s, int maximum, int *out) {
    char *end = NULL;
    errno = 0;
    long value = strtol(s, &end, 10);
    if (errno || end == s || *end || value < 0 || value > maximum) return 0;
    *out = (int)value;
    return 1;
}
static int fail(void) {
    fputs("invalid input: sigma n [mask ...] | outer n [mask:cost ...]\n", stderr);
    return 2;
}
static int compare(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}
static void array(const int *values, int count) {
    putchar('[');
    for (int i = 0; i < count; ++i) printf("%s%d", i ? "," : "", values[i]);
    putchar(']');
}
int main(int argc, char **argv) {
    int n;
    if (argc < 3 || !number(argv[2], 8, &n) || n < 1) return fail();
    int full = (1 << n) - 1;
    if (strcmp(argv[1], "sigma") == 0) {
        int atoms[CAP] = {full}, count = 1;
        for (int k = 3; k < argc; ++k) {
            int mask, next[CAP], used = 0;
            if (!number(argv[k], full, &mask)) return fail();
            for (int j = 0; j < count; ++j) {
                int a = atoms[j] & mask, b = atoms[j] & (full ^ mask);
                if (a) next[used++] = a;
                if (b) next[used++] = b;
            }
            memcpy(atoms, next, (size_t)used * sizeof(int));
            count = used;
        }
        qsort(atoms, (size_t)count, sizeof(int), compare);
        int sets[CAP] = {0}, size = 1;
        for (int i = 0; i < count; ++i) {
            for (int j = 0; j < size; ++j) sets[size + j] = sets[j] | atoms[i];
            size *= 2;
        }
        qsort(sets, (size_t)size, sizeof(int), compare);
        fputs("{\"atoms\":", stdout); array(atoms, count);
        fputs(",\"sets\":", stdout); array(sets, size); puts("}");
    } else if (strcmp(argv[1], "outer") == 0) {
        int masks[CAP], weights[CAP], count = argc - 3;
        if (count > CAP) return fail();
        for (int i = 0; i < count; ++i) {
            const char *item = argv[i + 3], *colon = strchr(item, ':');
            char left[32];
            if (!colon || (size_t)(colon - item) >= sizeof left) return fail();
            memcpy(left, item, (size_t)(colon - item)); left[colon - item] = '\0';
            if (!number(left, full, &masks[i]) || !number(colon + 1, 1000000, &weights[i])) return fail();
        }
        long long cost[CAP], tau[CAP];
        for (int i = 0; i <= full; ++i) cost[i] = INF;
        cost[0] = 0;
        for (int s = 0; s <= full; ++s) {
            if (cost[s] == INF) continue;
            for (int i = 0; i < count; ++i) {
                int target = s | masks[i];
                long long candidate = cost[s] + weights[i];
                if (candidate < cost[target]) cost[target] = candidate;
            }
        }
        for (int a = 0; a <= full; ++a) {
            tau[a] = INF;
            for (int s = 0; s <= full; ++s)
                if ((s & a) == a && cost[s] < tau[a]) tau[a] = cost[s];
        }
        int measurable[CAP], size = 0;
        for (int a = 0; a <= full; ++a) {
            int ok = 1;
            for (int d = 0; d <= full; ++d) {
                long long l = tau[d & a], r = tau[d & (full ^ a)];
                long long sum = (l == INF || r == INF) ? INF : l + r;
                if (tau[d] != sum) { ok = 0; break; }
            }
            if (ok) measurable[size++] = a;
        }
        fputs("{\"outer\":[", stdout);
        for (int a = 0; a <= full; ++a) {
            if (a) putchar(',');
            if (tau[a] == INF) fputs("null", stdout); else printf("%lld", tau[a]);
        }
        fputs("],\"measurable\":", stdout); array(measurable, size); puts("}");
    } else return fail();
    return 0;
}
