/* C11 arithmetic model; not an ELF parser or an instruction executor. */
#include <inttypes.h>
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Inputs are 32-bit addresses; int64_t safely holds S + A - P. */
static bool relocate(uint32_t symbol, int32_t addend, uint32_t place,
                     bool pc_relative, unsigned char out[4]) {
    int64_t value = (int64_t)symbol + addend;
    if (pc_relative) value -= place;
    if ((pc_relative && (value < INT32_MIN || value > INT32_MAX)) ||
        (!pc_relative && (value < 0 || value > UINT32_MAX))) return false;
    uint32_t bits = (uint32_t)value;
    for (unsigned i = 0; i < 4; ++i)
        out[i] = (unsigned char)((bits >> (8U * i)) & UINT32_C(255));
    return true;
}

struct test_case {
    const char *name;
    uint32_t symbol;
    int32_t addend;
    uint32_t place;
    bool pc_relative;
    bool accepted;
    uint32_t expected;
};

int main(void) {
    const struct test_case cases[] = {
        {"sum", 0x4004e8, -4, 0x4004df, true, true, 5},
        {"swap", 0x4004e8, -4, 0x4004da, true, true, 10},
        {"7.12A", 0x4004f8, -4, 0x4004ea, true, true, 10},
        {"7.12B", 0x400500, -4, 0x4004da, true, true, 34},
        {"array", 0x601018, 0, 0, false, true, 0x601018},
        {"backward", 0x4004d0, -4, 0x4004df, true, true, 0xffffffed},
        {"pc-max", 0x7fffffff, 0, 0, true, true, 0x7fffffff},
        {"pc-min", 0, 0, 0x80000000, true, true, 0x80000000},
        {"pc-too-high", 0x80000000, 0, 0, true, false, 0},
        {"pc-too-low", 0, -1, 0x80000000, true, false, 0},
        {"abs-max", 0xffffffff, 0, 0, false, true, 0xffffffff},
        {"abs-overflow", 0xffffffff, 1, 0, false, false, 0},
        {"abs-negative", 0, -1, 0, false, false, 0}
    };
    for (size_t k = 0; k < sizeof cases / sizeof cases[0]; ++k) {
        const struct test_case *t = &cases[k];
        unsigned char bytes[4] = {0xa5, 0xa5, 0xa5, 0xa5};
        bool ok = relocate(t->symbol, t->addend, t->place, t->pc_relative, bytes);
        uint32_t got = 0;
        for (unsigned i = 0; i < 4; ++i) got |= (uint32_t)bytes[i] << (8U * i);
        if (ok != t->accepted || (ok && got != t->expected) ||
            (!ok && got != UINT32_C(0xa5a5a5a5))) return 1;
        printf("%s:", t->name);
        if (ok) {
            for (unsigned i = 0; i < 4; ++i) printf(" %02x", (unsigned)bytes[i]);
            putchar('\n');
        } else puts(" rejected");
    }
    return 0;
}
