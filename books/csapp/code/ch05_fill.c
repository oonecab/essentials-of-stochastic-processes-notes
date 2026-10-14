#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

/* GNU/Clang may_alias permits word accesses to objects of other effective types.
   The fallback is strictly conforming byte access. uintptr_t is a target condition. */
#if defined(__GNUC__) || defined(__clang__)
typedef unsigned long alias_word __attribute__((__may_alias__));
#define WORD_ACCESS 1
#else
#define WORD_ACCESS 0
#endif
static void *fill(void *s,int c,size_t n) {
    unsigned char *p=s;const unsigned char byte=(unsigned char)c;
    const size_t k=sizeof(unsigned long);
    unsigned long packed=byte;
    for(size_t i=1;i<k;++i) packed=(packed<<CHAR_BIT)|byte;
    while(n>0 && (uintptr_t)p % k!=0) {*p++=byte;--n;}
    while(n>=k) {
#if WORD_ACCESS
        *(alias_word *)(void *)p=packed;
#else
        for(size_t j=0;j<k;++j) p[j]=(unsigned char)(packed>>(j*CHAR_BIT));
#endif
        p+=k;n-=k;
    }
    while(n>0) {*p++=byte;--n;}
    return s;
}
int main(void) {
    unsigned char a[96];size_t cases=0;
    /* Guard regions expose both undershoot and overshoot. */
    for(size_t offset=0;offset<16;++offset) for(size_t n=0;n<=64;++n)
        for(int c=-257;c<=257;c+=257) {
            for(size_t i=0;i<sizeof a;++i) a[i]=0xa5;
            void *result=fill(a+offset,c,n);
            if(result!=a+offset) {
                fprintf(stderr,"fill return differs: offset=%zu n=%zu c=%d\n",offset,n,c);
                return 1;
            }
            for(size_t i=0;i<sizeof a;++i) {
                unsigned char expected=i>=offset && i<offset+n ? (unsigned char)c : 0xa5;
                if(a[i]!=expected) {
                    fprintf(stderr,"fill byte differs: offset=%zu n=%zu c=%d index=%zu\n",offset,n,c,i);
                    return 1;
                }
            }
            ++cases;
        }
    printf("fill-cases=%zu word-bytes=%zu guards=ok\n",cases,sizeof(unsigned long));
    return 0;
}
