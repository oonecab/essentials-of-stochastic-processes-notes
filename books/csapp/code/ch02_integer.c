/* Chapter 2: integer models. C11, 8-bit bytes, 32-bit two's-complement int.
 * Negative right shifts and uint-to-int conversion use the stated machine model.
 * No evaluated signed addition, subtraction, multiplication, or left shift overflows.
 */
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
_Static_assert(CHAR_BIT == 8 && UINT_MAX == UINT32_MAX && INT_MAX == INT32_MAX,
               "32-bit int and 8-bit bytes required");
static int decode(unsigned u) {
    return u <= (unsigned)INT_MAX ? (int)u : -1 - (int)(UINT_MAX-u);
}
void show_bytes(const void *p, size_t n) {
    const unsigned char *b = p;
    for (size_t i=0; i<n; ++i) printf("%s%02x", i ? " " : "", (unsigned)b[i]);
    putchar('\n');
}
void show_short(short x) { show_bytes(&x, sizeof x); }
void show_long(long x) { show_bytes(&x, sizeof x); }
void show_double(double x) { show_bytes(&x, sizeof x); }
int is_little_endian(void) { const unsigned x=1; return *(const unsigned char *)&x == 1; }
void inplace_swap(unsigned *x, unsigned *y) { *y=*x^*y; *x=*x^*y; *y=*x^*y; }
void reverse_array(unsigned *a, size_t n) {
    if (!n) return;
    for (size_t first=0,last=n-1; first<last; ++first,--last) inplace_swap(&a[first],&a[last]);
}
unsigned bis(unsigned x,unsigned m) { return x|m; }
unsigned bic(unsigned x,unsigned m) { return x&~m; }
unsigned bool_or(unsigned x,unsigned y) { return bis(x,y); }
unsigned bool_xor(unsigned x,unsigned y) { return bis(bic(x,y),bic(y,x)); }
float sum_elements(const float *a,size_t n) { float s=0; for(size_t i=0;i<n;++i) s+=a[i]; return s; }
int strlonger(const char *s,const char *t) { return strlen(s)>strlen(t); }
int uadd_ok(unsigned x,unsigned y) { unsigned sum=x+y; return sum>=x; }
int tadd_ok(int x,int y) {
    return !(y>0 && x>INT_MAX-y) && !(y<0 && x<INT_MIN-y);
}
int tsub_ok(int x,int y) {
    return !(y>0 && x<INT_MIN+y) && !(y<0 && x>INT_MAX+y);
}
int tmult_ok(int x,int y) { int64_t p=(int64_t)x*y; return p>=INT_MIN && p<=INT_MAX; }
int div16(int x) { int bias=(x>>31)&15; return (x+bias)>>4; }
unsigned replace_byte(unsigned x,int i,unsigned char b) {
    unsigned shift=(unsigned)i<<3; return (x&~(255u<<shift))|((unsigned)b<<shift);
}
int any_one(int x) { return !!x; }
int any_zero(int x) { return !!~x; }
int low_any_one(int x) { return !!(x&255); }
int high_any_zero(int x) { return !!((~x>>(((sizeof(int)-1)<<3)))&255); }
int int_shifts_are_arithmetic(void) { return (-1>>1)==-1; }
unsigned srl(unsigned x,int k) {
    unsigned xsra=(unsigned)((int)x>>k);
    int w=(int)(sizeof(int)<<3);
    unsigned high=(~0u<<(w-1-k))<<1;
    return xsra&~high;
}
int sra(int x,int k) {
    unsigned xsrl=(unsigned)x>>k;
    int w=(int)(sizeof(int)<<3);
    unsigned high=(~0u<<(w-1-k))<<1;
    unsigned sign=0u-(unsigned)!!((unsigned)x&(1u<<(w-1)));
    return (int)(xsrl|(high&sign));
}
int any_odd_one(unsigned x) { return !!(x&0xAAAAAAAAu); }
int odd_ones(unsigned x) {
    x^=x>>16; x^=x>>8; x^=x>>4; x^=x>>2; x^=x>>1; return (int)(x&1);
}
int leftmost_one(unsigned x) {
    x|=x>>1; x|=x>>2; x|=x>>4; x|=x>>8; x|=x>>16;
    return (int)(x&~(x>>1));
}
int int_size_is_32(void) { unsigned x=1u<<15; x<<=15; x<<=1; return !!x && !(x<<1); }
int lower_one_mask(int n) { int w=(int)(sizeof(int)<<3); return (int)(~0u>>(w-n)); }
unsigned rotate_left(unsigned x,int n) { int w=(int)(sizeof(int)<<3); return (x<<n)|((x>>(w-1-n))>>1); }
int fits_bits(int x,int n) { int t=x>>(n-1); return !t || !~t; }
int xbyte(unsigned word,int bytenum) { return (int)(word<<((3-bytenum)<<3))>>24; }
int copy_int(int val,void *buf,int maxbytes) {
    if(maxbytes>=0 && (size_t)maxbytes>=sizeof val) { memcpy(buf,&val,sizeof val); return 1; }
    return 0;
}
int saturating_add(int x,int y) {
    unsigned ux=(unsigned)x,uy=(unsigned)y,s=ux+uy;
    int w=(int)(sizeof(int)<<3);
    unsigned sx=ux>>(w-1),sy=uy>>(w-1),ss=s>>(w-1);
    unsigned overflow=(~(sx^sy)&(sx^ss))&1;
    unsigned mask=0u-overflow;
    unsigned bound=(unsigned)INT_MAX+sx;
    return (int)((s&~mask)|(bound&mask));
}
int signed_high_prod(int x,int y) {
    int64_t p=(int64_t)x*y;
    uint64_t bits=(uint64_t)p;
    return decode((unsigned)(bits>>32));
}
unsigned unsigned_high_prod(unsigned x,unsigned y) {
    int w=(int)(sizeof(int)<<3);
    unsigned sx=0u-(x>>(w-1)),sy=0u-(y>>(w-1));
    return (unsigned)signed_high_prod((int)x,(int)y)+(sx&y)+(sy&x);
}
void *checked_calloc(size_t nmemb,size_t size) {
    if(!nmemb || !size || nmemb>SIZE_MAX/size) return NULL;
    size_t bytes=nmemb*size;
    void *p=malloc(bytes);
    if(p) memset(p,0,bytes);
    return p;
}
void *copy_elements(const void *const src[],int n,size_t size) {
    if(n<0 || (size && (size_t)n>SIZE_MAX/size)) return NULL;
    size_t bytes=(size_t)n*size;
    if(!bytes) return NULL;
    unsigned char *p=malloc(bytes);
    if(!p) return NULL;
    for(int i=0;i<n;++i) memcpy(p+(size_t)i*size,src[i],size);
    return p;
}
int divide_power2(int x,int k) { int w=(int)(sizeof(int)<<3); int bias=(x>>(w-1))&((1<<k)-1); return (x+bias)>>k; }
int mul3div4(int x) {
    unsigned u=(unsigned)x;
    int product=(int)((u<<1)+u);
    int w=(int)(sizeof(int)<<3);
    int bias=(product>>(w-1))&3;
    return (product+bias)>>2;
}
int threefourths(int x) {
    int q=x>>2,r=x&3;
    int w=(int)(sizeof(int)<<3);
    int bias=(x>>(w-1))&3;
    return (q+q+q)+((r+r+r+bias)>>2);
}
static unsigned rng=0x31415926u;
static unsigned next_word(void) { rng=rng*1664525u+1013904223u; return rng; }
static int check_pair(int x,int y) {
    int64_t a=(int64_t)x+y,b=(int64_t)x-y,p=(int64_t)x*y;
    int add=a>=INT_MIN&&a<=INT_MAX,sub=b>=INT_MIN&&b<=INT_MAX,mul=p>=INT_MIN&&p<=INT_MAX;
    int sat=a<INT_MIN ? INT_MIN : a>INT_MAX ? INT_MAX : (int)a;
    uint64_t up=(uint64_t)(unsigned)x*(unsigned)y;
    return tadd_ok(x,y)==add && tsub_ok(x,y)==sub && tmult_ok(x,y)==mul &&
           saturating_add(x,y)==sat && unsigned_high_prod((unsigned)x,(unsigned)y)==(unsigned)(up>>32) &&
           uadd_ok((unsigned)x,(unsigned)y)==((uint64_t)(unsigned)x+(unsigned)y<=UINT_MAX);
}
int main(void) {
    if(!int_shifts_are_arithmetic()) return 2;
    const int edge[]={INT_MIN,INT_MIN+1,-65535,-129,-128,-1,0,1,127,128,65535,INT_MAX-1,INT_MAX};
    unsigned long tests=0;
    for(size_t i=0;i<sizeof edge/sizeof *edge;++i)
      for(size_t j=0;j<sizeof edge/sizeof *edge;++j) { if(!check_pair(edge[i],edge[j])) return 1; ++tests; }
    for(unsigned i=0;i<100000;++i) {
        unsigned u=next_word(); int x=decode(u),y=decode(next_word());
        if(!check_pair(x,y) || threefourths(x)!=(int)((int64_t)x*3/4) ||
           mul3div4(x)!=decode((unsigned)((uint64_t)u*3))/4 || div16(x)!=x/16) return 1;
        unsigned parity=0,top=0;
        for(unsigned j=0;j<32;++j) if((u>>j)&1) { parity^=1;top=1u<<j; }
        if(odd_ones(u)!=(int)parity || (unsigned)leftmost_one(u)!=top) return 1;
        for(int k=0;k<32;++k) {
            uint64_t doubled=((uint64_t)u<<32)|u;
            unsigned rot=(unsigned)((doubled<<k)>>32);
            int64_t d=INT64_C(1)<<k;
            int ar=(int)((int64_t)x/d-((x<0 && (int64_t)x%d)!=0));
            if(srl(u,k)!=(u>>k)||sra(x,k)!=ar||rotate_left(u,k)!=rot) return 1;
            if(k<31 && divide_power2(x,k)!=x/(1<<k)) return 1;
        }
        for(int n=1;n<=32;++n) {
            int64_t lim=INT64_C(1)<<(n-1);
            if(fits_bits(x,n)!=(x>=-lim&&x<lim)) return 1;
            if((unsigned)lower_one_mask(n)!=(unsigned)((UINT64_C(1)<<n)-1)) return 1;
        }
        ++tests;
    }
    unsigned a[]={1,2,3,4,5}; reverse_array(a,5);
    const float fa[]={1.0f,2.0f,3.0f};
    if(a[2]!=3 || a[0]!=5 || sum_elements(fa,3)!=6 || sum_elements(NULL,0)!=0 || !strlonger("abcd","ab")) return 1;
    if(replace_byte(0x12345678,2,0xAB)!=0x12AB5678 || xbyte(0x80FF017Fu,3)!=-128) return 1;
    if(any_one(0)||!any_zero(0)||low_any_one(256)||!high_any_zero(0)||any_odd_one(0x55555555u)) return 1;
    if(bool_or(0x69,0x55)!=0x7D || bool_xor(0x69,0x55)!=0x3C || !int_size_is_32()) return 1;
    int target=0; if(copy_int(42,&target,-1) || !copy_int(42,&target,sizeof target) || target!=42) return 1;
    unsigned char *p=checked_calloc(17,3); if(!p) return 1;
    for(size_t i=0;i<51;++i) if(p[i]) { free(p); return 1; } free(p);
    if(checked_calloc(SIZE_MAX,2)!=NULL || checked_calloc(0,4)!=NULL) return 1;
    int aa=17,bb=-4; const void *src[]={&aa,&bb}; int *cp=copy_elements(src,2,sizeof(int));
    if(!cp) return 1; int copy_ok=cp[0]==aa&&cp[1]==bb; free(cp); if(!copy_ok) return 1;
    printf("integer_cases=%lu shifts=%u widths=%u status=ok\n",tests,100000u*32,100000u*32);
    printf("endian=%s int=%zu long=%zu double=%zu\n",is_little_endian()?"little":"big",sizeof(int),sizeof(long),sizeof(double));
    printf("short12345=");show_short(12345); printf("long12345=");show_long(12345);printf("double1=");show_double(1.0);
    printf("reverse=5,4,3,2,1 replace=%08x xbyte=%d threefourths(-7)=%d\n",replace_byte(0x12345678,2,0xAB),xbyte(0x80FF017Fu,3),threefourths(-7));
    return 0;
}
