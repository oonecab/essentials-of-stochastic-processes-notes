#include <float.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static int decode8(uint8_t u) {
    return u < 128u ? (int)u : (int)u - 256;
}
int main(void) {
    for (unsigned int u = 0; u < 256u; ++u) {
        printf("u=%u signed=%d plus1=%u\n", u, decode8((uint8_t)u),
               (u + 1u) & 255u);
    }
    const uint32_t word = UINT32_C(0x12345678);
    const unsigned char *bytes = (const unsigned char *)(const void *)&word;
    printf("bytes=");
    for (size_t i = 0; i < sizeof word; ++i) printf("%02x", (unsigned int)bytes[i]);
    putchar('\n');
    if (sizeof(double) != sizeof(uint64_t) || FLT_RADIX != 2 || DBL_MANT_DIG != 53) {
        fputs("This example requires IEEE binary64.\n", stderr);
        return 2;
    }
    const double one = 1.0;
    uint64_t bits;
    memcpy(&bits, &one, sizeof bits);
    printf("double1=%016" PRIx64 "\n", bits);
    volatile double a = 1.0e16, b = -1.0e16, c = 1.0;
    const double left = (a + b) + c;
    const double right = a + (b + c);
    printf("grouping=%.0f,%.0f\n", left, right);
    return 0;
}
