/* Strict C11: deterministic LP64 layout and fixed-width machine models. */
#include <inttypes.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

struct Test { short *p; struct { short x, y; } s; struct Test *next; };
struct P1 { short i; int c; int *j; short *d; };
struct P2 { int i[2]; char c[8]; short s[4]; long *j; };
struct P3 { long w[2]; int *c[2]; };
struct ACE { short v; struct ACE *p; };
struct P4 { char w[16]; char *c[2]; };
struct P5 { struct P4 a[2]; struct P1 t; };
struct Record { int *a; float b; char c; short d; long e; double f; int g; char *h; };
struct CompactRecord { int *a; char *h; double f; long e; float b; int g; short d; char c; };

static uint16_t reverse16(uint16_t x)
{
    uint16_t out = 0;
    for (unsigned i = 0; i < 16; ++i) {
        out = (uint16_t)((out << 1) | (x & 1u));
        x >>= 1;
    }
    return out;
}

static void product128(uint64_t a, uint64_t b, uint64_t *hi, uint64_t *lo)
{
    const uint64_t mask = UINT32_MAX;
    uint64_t a0 = a & mask, a1 = a >> 32;
    uint64_t b0 = b & mask, b1 = b >> 32;
    uint64_t w0 = a0*b0;
    uint64_t t = a1*b0 + (w0 >> 32);
    uint64_t w1 = t & mask, w2 = t >> 32;
    w1 += a0*b1;
    *lo = (w1 << 32) | (w0 & mask);
    *hi = a1*b1 + w2 + (w1 >> 32);
    /* Convert unsigned full product to signed 128-bit representation. */
    if (a >> 63) *hi -= b;
    if (b >> 63) *hi -= a;
}

static uint64_t rfun(uint64_t x)
{
    if (x == 0) return 0;
    return x + rfun(x >> 2);
}

static int signed8(unsigned u)
{
    return u < 128 ? (int)u : (int)u - 256;
}

int main(void)
{
    if (CHAR_BIT != 8 || sizeof(long) != 8 || sizeof(void *) != 8 ||
        sizeof(int) != 4 || sizeof(short) != 2) return 2;
    unsigned flag_cases = 0;
    for (unsigned a = 0; a < 256; ++a) {
        for (unsigned b = 0; b < 256; ++b) {
            unsigned result = (a-b) & 255u;
            unsigned sf = result >> 7;
            unsigned of = ((a^b) & (a^result) & 128u) != 0;
            unsigned cf = a < b;
            unsigned zf = result == 0;
            if ((sf^of) != (unsigned)(signed8(a) < signed8(b)) ||
                cf != (unsigned)(a < b) || zf != (unsigned)(a == b)) return 1;
            ++flag_cases;
        }
    }
    printf("flags8=%u pass\n", flag_cases);
    uint64_t checksum = 0;
    for (unsigned x = 0; x < 65536; ++x) {
        unsigned oracle = 0;
        for (unsigned bit = 0; bit < 16; ++bit)
            if (x & (1u << bit)) oracle |= 1u << (15-bit);
        uint16_t got = reverse16((uint16_t)x);
        if (got != oracle) return 1;
        checksum += got;
    }
    printf("reverse16=65536 checksum=%" PRIu64 "\n", checksum);
    printf("layout-test=%zu,%zu,%zu,%zu size=%zu\n", offsetof(struct Test,p),
           offsetof(struct Test,s.x),offsetof(struct Test,s.y),
           offsetof(struct Test,next),sizeof(struct Test));
    printf("layout-P1=%zu,%zu,%zu,%zu size=%zu\n",offsetof(struct P1,i),
           offsetof(struct P1,c),offsetof(struct P1,j),offsetof(struct P1,d),sizeof(struct P1));
    printf("layout-P2=%zu,%zu,%zu,%zu size=%zu\n",offsetof(struct P2,i),
           offsetof(struct P2,c),offsetof(struct P2,s),offsetof(struct P2,j),sizeof(struct P2));
    printf("layout-P3=%zu,%zu size=%zu\n",offsetof(struct P3,w),offsetof(struct P3,c),sizeof(struct P3));
    printf("layout-P4=%zu,%zu size=%zu\n",offsetof(struct P4,w),offsetof(struct P4,c),sizeof(struct P4));
    printf("layout-ACE=%zu,%zu size=%zu\n",offsetof(struct ACE,v),offsetof(struct ACE,p),sizeof(struct ACE));
    printf("layout-P5=%zu,%zu size=%zu\n",offsetof(struct P5,a),offsetof(struct P5,t),sizeof(struct P5));
    printf("layout-rec=%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu size=%zu\n",
           offsetof(struct Record,a),offsetof(struct Record,b),offsetof(struct Record,c),
           offsetof(struct Record,d),offsetof(struct Record,e),offsetof(struct Record,f),
           offsetof(struct Record,g),offsetof(struct Record,h),sizeof(struct Record));
    printf("layout-rec-reordered=%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu size=%zu\n",
           offsetof(struct CompactRecord,a),offsetof(struct CompactRecord,h),
           offsetof(struct CompactRecord,f),offsetof(struct CompactRecord,e),
           offsetof(struct CompactRecord,b),offsetof(struct CompactRecord,g),
           offsetof(struct CompactRecord,d),offsetof(struct CompactRecord,c),sizeof(struct CompactRecord));
    const uint64_t vals[] = {0,1,2,3,UINT64_MAX,UINT64_MAX-1,
        UINT64_C(0x8000000000000000),UINT64_C(0x7fffffffffffffff),
        UINT64_C(0x0123456789abcdef)};
    for (size_t i=0;i<sizeof vals/sizeof vals[0];++i)
        for (size_t j=0;j<sizeof vals/sizeof vals[0];++j) {
            uint64_t hi,lo;
            product128(vals[i],vals[j],&hi,&lo);
            printf("product=%016" PRIx64 ",%016" PRIx64 ":%016" PRIx64 "%016" PRIx64 "\n",
                   vals[i],vals[j],hi,lo);
        }
    for (uint64_t x=0;x<=21;++x)
        printf("rfun=%" PRIu64 ",%" PRIu64 "\n",x,rfun(x));
    uint64_t fact=1;
    for (unsigned n=1;n<=21;++n) {
        if (fact>(uint64_t)INT64_MAX/n) {
            printf("factorial-overflow=%u\n",n);
            break;
        }
        fact*=n;
        if (n==14 || n==20) printf("factorial=%u,%" PRIu64 "\n",n,fact);
    }
    return 0;
}
