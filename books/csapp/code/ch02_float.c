/* Integer-only binary32 operations; the test driver uses native float as reference. */
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <fenv.h>
typedef unsigned float_bits;
_Static_assert(UINT_MAX==UINT32_MAX && INT_MAX==INT32_MAX,"32-bit integers required");
float_bits float_negate(float_bits f) {
    unsigned a=f&0x7FFFFFFFu;
    return a>0x7F800000u ? f : f^0x80000000u;
}
float_bits float_absval(float_bits f) {
    unsigned a=f&0x7FFFFFFFu;
    return a>0x7F800000u ? f : a;
}
float_bits float_twice(float_bits f) {
    unsigned sign=f&0x80000000u,exp=f>>23&255u,frac=f&0x7FFFFFu;
    if(exp==255) return f;
    if(exp==0) return sign|(frac<<1);
    if(exp==254) return sign|0x7F800000u;
    return f+0x00800000u;
}
float_bits float_half(float_bits f) {
    unsigned sign=f&0x80000000u,exp=f>>23&255u,frac=f&0x7FFFFFu;
    if(exp==255) return f;
    if(exp>1) return f-0x00800000u;
    unsigned m=(exp<<23)|frac;
    unsigned rounded=(m>>1)+((m&3u)==3u);
    return sign|rounded;
}
int float_f2i(float_bits f) {
    unsigned sign=f>>31,exp=f>>23&255u,frac=f&0x7FFFFFu;
    int e=(int)exp-127;
    if(e<0) return 0;
    if(e>30) {
        if(e==31 && sign && frac==0) return INT_MIN;
        return INT_MIN;
    }
    unsigned m=0x800000u|frac;
    unsigned mag=e>=23 ? m<<(e-23) : m>>(23-e);
    return sign ? -(int)mag : (int)mag;
}
float_bits float_i2f(int i) {
    if(i==0) return 0;
    unsigned sign=(unsigned)i&0x80000000u;
    unsigned mag=sign ? 0u-(unsigned)i : (unsigned)i;
    unsigned t=mag,p=0;
    if(t>>16) {p+=16;t>>=16;} if(t>>8) {p+=8;t>>=8;}
    if(t>>4) {p+=4;t>>=4;} if(t>>2) {p+=2;t>>=2;} if(t>>1) ++p;
    unsigned exp=p+127,sig;
    if(p<=23) sig=mag<<(23-p);
    else {
        unsigned d=p-23;
        sig=mag>>d;
        unsigned rem=mag&((1u<<d)-1),half=1u<<(d-1);
        if(rem>half || (rem==half && (sig&1))) ++sig;
        if(sig==0x1000000u) {sig>>=1;++exp;}
    }
    return sign|(exp<<23)|(sig&0x7FFFFFu);
}
float_bits fpwr2_bits(int x) {
    unsigned exp,frac;
    if(x < -149) {exp=0;frac=0;}
    else if(x < -126) {exp=0;frac=1u<<(x+149);}
    else if(x < 128) {exp=(unsigned)(x+127);frac=0;}
    else {exp=255;frac=0;}
    return (exp<<23)|frac;
}
int float_le_bits(float_bits ux,float_bits uy) {
    unsigned sx=ux>>31,sy=uy>>31;
    return ((ux<<1)==0 && (uy<<1)==0) || (sx!=sy ? sx : sx ? ux>=uy : ux<=uy);
}
static float u2f(unsigned u) {float f;memcpy(&f,&u,sizeof f);return f;}
static unsigned f2u(float f) {unsigned u;memcpy(&u,&f,sizeof u);return u;}
static int decode(unsigned u) {return u<=INT_MAX ? (int)u : -1-(int)(UINT_MAX-u);}
static int test_one(unsigned u) {
    unsigned a=u&0x7FFFFFFFu;
    int i=decode(u);
    if(float_i2f(i)!=f2u((float)i)) return 6;
    if(a>0x7F800000u) {
        if(float_negate(u)!=u||float_absval(u)!=u||float_twice(u)!=u||float_half(u)!=u||float_f2i(u)!=INT_MIN) return 7;
        return 0;
    }
    float f=u2f(u);
    if(float_negate(u)!=f2u(-f)) return 1;
    float absolute=f<0 ? -f : f;
    if(a==0) absolute=0.0f;
    if(float_absval(u)!=f2u(absolute)) return 2;
    if(float_twice(u)!=f2u(f*2.0f)) return 3;
    if(float_half(u)!=f2u(f*0.5f)) return 4;
    double d=(double)f;
    int reference=(d>=-2147483648.0 && d<2147483648.0) ? (int)f : INT_MIN;
    if(float_f2i(u)!=reference) return 5;
    return 0;
}
int main(int argc,char **argv) {
    if(sizeof(float)!=4 || FLT_RADIX!=2 || FLT_MANT_DIG!=24 || FLT_MIN_EXP!=-125 || FLT_MAX_EXP!=128 || fegetround()!=FE_TONEAREST) return 2;
    uint64_t count=0;
    if(argc==2 && strcmp(argv[1],"--exhaustive")==0) {
        for(uint64_t u=0;u<UINT64_C(0x100000000);++u) {
            int error=test_one((unsigned)u);
            if(error) {fprintf(stderr,"failed operation=%d input=%08" PRIx64 "\n",error,u);return 1;}
            if((u&0xFFFFFFFu)==0 && u) fprintf(stderr,"checked=%" PRIu64 "\n",u);
        }
        count=UINT64_C(0x100000000);
    } else if(argc==1) {
        const unsigned frac[]={0,1,2,3,4,0x3FFFFF,0x400000,0x400001,0x7FFFFC,0x7FFFFD,0x7FFFFE,0x7FFFFF};
        for(unsigned s=0;s<2;++s) for(unsigned e=0;e<256;++e)
            for(size_t j=0;j<sizeof frac/sizeof *frac;++j) {
                unsigned u=(s<<31)|(e<<23)|frac[j];
                int error=test_one(u);
                if(error) {fprintf(stderr,"failed operation=%d input=%08x\n",error,u);return 1;}
                ++count;
            }
        unsigned rng=0x27182818u;
        for(unsigned j=0;j<100000;++j) {
            rng=rng*1664525u+1013904223u;
            int error=test_one(rng);
            if(error) {fprintf(stderr,"failed operation=%d input=%08x\n",error,rng);return 1;}
            ++count;
        }
    } else {fputs("usage: ch02_float [--exhaustive]\n",stderr);return 2;}
    const unsigned le_cases[]={0,0x80000000u,0x3F800000u,0xBF800000u,0x7F800000u,0xFF800000u,1,0x80000001u};
    for(size_t i=0;i<8;++i) for(size_t j=0;j<8;++j)
        if(float_le_bits(le_cases[i],le_cases[j])!=(u2f(le_cases[i])<=u2f(le_cases[j]))) return 1;
    printf("float_cases=%" PRIu64 " operations=6 comparison_pairs=64 status=ok\n",count);
    const unsigned sample[]={0,1,3,0x007FFFFFu,0x00800000u,0x3F800000u,0x7F7FFFFFu,0x7F800000u,0x7FC12345u};
    for(size_t i=0;i<sizeof sample/sizeof *sample;++i)
        printf("bits=%08x twice=%08x half=%08x int=%d\n",sample[i],float_twice(sample[i]),float_half(sample[i]),float_f2i(sample[i]));
    printf("powers=%08x,%08x,%08x,%08x\n",fpwr2_bits(-150),fpwr2_bits(-149),fpwr2_bits(-126),fpwr2_bits(128));
    return 0;
}
