/* p <= 10^6 and level <= 20 keep every product below 2^40. */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

static int integer(const char *text, unsigned long long maximum, unsigned long long *value) {
    char *end = NULL;
    if (!*text) return 0;
    for (const char *p = text; *p; ++p)
        if (*p < '0' || *p > '9') return 0;
    errno = 0;
    unsigned long long result = strtoull(text, &end, 10);
    if (errno || end == text || *end || result > maximum) return 0;
    *value = result;
    return 1;
}
int main(int argc, char **argv) {
    unsigned long long p, q, level;
    if (argc != 4 || !integer(argv[1], 1000000, &p) ||
        !integer(argv[2], 1000000, &q) || !q ||
        !integer(argv[3], 20, &level) || !level) {
        fputs("require 0<=p<=1000000, 1<=q<=1000000, 1<=level<=20\n", stderr);
        return 2;
    }
    unsigned long long scale = 1ULL << level;
    unsigned long long grid = p * scale / q;
    if (grid > level * scale) grid = level * scale;
    printf("{\"grid\":%llu,\"scale\":%llu}\n", grid, scale);
    return 0;
}
