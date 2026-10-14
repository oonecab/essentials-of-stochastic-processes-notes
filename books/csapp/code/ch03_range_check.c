/* Build with ch03_ranges.S on an x86-64 execution environment.
   --exhaustive checks every binary32 encoding, including signaling NaNs.
   It requires IEEE binary32 and the default masked floating exceptions. */
#include <float.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern int ch03_range_branch(float x);
extern int ch03_range_cmov(float x);

static int from_bits(uint32_t u)
{
    uint32_t mag = u & UINT32_C(0x7fffffff);
    if (mag > UINT32_C(0x7f800000)) return 3;
    if (mag == 0) return 1;
    return (u >> 31) ? 0 : 2;
}

static int check(uint32_t u, uint64_t counts[4])
{
    float x;
    memcpy(&x, &u, sizeof x);
    int expected = from_bits(u);
    int a = ch03_range_branch(x);
    int b = ch03_range_cmov(x);
    if (a != expected || b != expected) {
        fprintf(stderr, "bits=%08" PRIx32 " expected=%d branch=%d cmov=%d\n",
                u, expected, a, b);
        return 1;
    }
    counts[expected]++;
    return 0;
}

int main(int argc, char **argv)
{
    if (sizeof(float) != sizeof(uint32_t) || FLT_RADIX != 2 ||
        FLT_MANT_DIG != 24 || FLT_MAX_EXP != 128) return 2;
    int all = argc == 2 && strcmp(argv[1], "--exhaustive") == 0;
    if (argc > 1 && !all) return 2;
    uint64_t counts[4] = {0, 0, 0, 0};
    uint64_t checked = 0;
    if (all) {
        for (uint64_t i = 0; i < (UINT64_C(1) << 32); ++i) {
            if (check((uint32_t)i, counts)) return 1;
            ++checked;
        }
    } else {
        const uint32_t cases[] = {0, UINT32_C(0x80000000), 1,
            UINT32_C(0x80000001), UINT32_C(0x007fffff), UINT32_C(0x00800000),
            UINT32_C(0x3f800000), UINT32_C(0xbf800000), UINT32_C(0x7f7fffff),
            UINT32_C(0xff7fffff), UINT32_C(0x7f800000), UINT32_C(0xff800000),
            UINT32_C(0x7f800001), UINT32_C(0xff800001), UINT32_C(0x7fc00000),
            UINT32_C(0xffffffff)};
        for (size_t i = 0; i < sizeof cases / sizeof cases[0]; ++i) {
            if (check(cases[i], counts)) return 1;
            ++checked;
        }
    }
    printf("checked=%" PRIu64 " branch=pass cmov=pass\n", checked);
    printf("NEG=%" PRIu64 " ZERO=%" PRIu64 " POS=%" PRIu64 " OTHER=%" PRIu64 "\n",
           counts[0], counts[1], counts[2], counts[3]);
    return 0;
}
