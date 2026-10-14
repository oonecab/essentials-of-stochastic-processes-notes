#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define SETS 4u
#define MAX_WAYS 4u
struct line { bool valid; uint64_t tag, age; };
struct cache { struct line lines[SETS][MAX_WAYS]; unsigned int ways, block;
               uint64_t clock, hits, misses; };
static bool access_cache(struct cache *c, uint64_t address) {
    const uint64_t number = address / c->block;
    const unsigned int set = (unsigned int)(number % SETS);
    const uint64_t tag = number / SETS;
    struct line *rows = c->lines[set];
    ++c->clock;
    for (unsigned int i = 0; i < c->ways; ++i) {
        if (rows[i].valid && rows[i].tag == tag) {
            rows[i].age = c->clock; ++c->hits; return true;
        }
    }
    unsigned int victim = 0;
    for (unsigned int i = 0; i < c->ways; ++i) {
        if (!rows[i].valid) { victim = i; break; }
        if (rows[i].age < rows[victim].age) victim = i;
    }
    rows[victim] = (struct line){true, tag, c->clock};
    ++c->misses; return false;
}
static bool parse(const char *s, uint64_t *out) {
    if (!*s || *s == '-') return false;
    const char *p = *s == '+' ? s + 1 : s;
    if (!*p) return false;
    for (; *p; ++p) if (*p < '0' || *p > '9') return false;
    char *end;
    errno = 0;
    const uintmax_t value = strtoumax(s, &end, 10);
    if (errno || *end || value > UINT64_MAX) return false;
    *out = (uint64_t)value; return true;
}
static void report(struct cache *c, uint64_t a) {
    const bool hit = access_cache(c, a);
    printf("addr=%" PRIu64 " set=%" PRIu64 " tag=%" PRIu64 " hit=%u\n",
           a, (a / c->block) % SETS, (a / c->block) / SETS, hit ? 1u : 0u);
}
int main(int argc, char **argv) {
    struct cache c = {.ways = 1, .block = 2};
    if (argc > 1) {
        uint64_t ways;
        if (argc < 3 || !parse(argv[1], &ways) ||
            (ways != 1 && ways != 2 && ways != 4)) return 2;
        c.ways = (unsigned int)ways;
        for (int i = 2; i < argc; ++i) {
            uint64_t a;
            if (!parse(argv[i], &a)) return 2;
            report(&c, a);
        }
    } else {
        const uint64_t trace[] = {0, 1, 13, 8, 0};
        for (size_t i = 0; i < sizeof trace / sizeof trace[0]; ++i) report(&c, trace[i]);
    }
    printf("hits=%" PRIu64 " misses=%" PRIu64 "\n", c.hits, c.misses);
    if (argc == 1) {
        for (unsigned int column = 0; column < 2; ++column) {
            memset(&c, 0, sizeof c); c.ways = 1; c.block = 16;
            for (unsigned int i = 0; i < 8; ++i) for (unsigned int j = 0; j < 8; ++j) {
                const uint64_t index = column ? (uint64_t)j * 8u + i : (uint64_t)i * 8u + j;
                (void)access_cache(&c, index * 4u);
            }
            printf("matrix-%s hits=%" PRIu64 " misses=%" PRIu64 "\n",
                   column ? "column" : "row", c.hits, c.misses);
        }
    }
    return 0;
}
