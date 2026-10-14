#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static void require(int condition, const char *message) {
    if (!condition) { fprintf(stderr,"loop check failed: %s\n",message); exit(1); }
}

/* Unsigned arithmetic makes every regrouping exact modulo 2^64. */
static uint64_t combine5(const uint64_t *a, size_t n) {
    uint64_t r = 0; size_t i = 0;
    for (; n - i >= 5; i += 5) {
        r += a[i]; r += a[i+1]; r += a[i+2]; r += a[i+3]; r += a[i+4];
    }
    for (; i < n; ++i) r += a[i];
    return r;
}
static uint64_t dot6x1(const uint64_t *u, const uint64_t *v, size_t n) {
    uint64_t r = 0; size_t i = 0;
    for (; n-i >= 6; i += 6) {
        r += u[i]*v[i]; r += u[i+1]*v[i+1]; r += u[i+2]*v[i+2];
        r += u[i+3]*v[i+3]; r += u[i+4]*v[i+4]; r += u[i+5]*v[i+5];
    }
    for (; i < n; ++i) r += u[i]*v[i];
    return r;
}
static uint64_t dot6x6(const uint64_t *u, const uint64_t *v, size_t n) {
    uint64_t r0=0,r1=0,r2=0,r3=0,r4=0,r5=0; size_t i=0;
    for (; n-i >= 6; i += 6) {
        r0+=u[i]*v[i]; r1+=u[i+1]*v[i+1]; r2+=u[i+2]*v[i+2];
        r3+=u[i+3]*v[i+3]; r4+=u[i+4]*v[i+4]; r5+=u[i+5]*v[i+5];
    }
    for (; i<n; ++i) r0+=u[i]*v[i];
    return ((r0+r1)+(r2+r3))+(r4+r5);
}
static uint64_t dot6x1a(const uint64_t *u, const uint64_t *v, size_t n) {
    uint64_t r=0; size_t i=0;
    for (; n-i >= 6; i+=6) {
        uint64_t a=u[i]*v[i]+u[i+1]*v[i+1];
        uint64_t b=u[i+2]*v[i+2]+u[i+3]*v[i+3];
        uint64_t c=u[i+4]*v[i+4]+u[i+5]*v[i+5];
        r += (a+b)+c;
    }
    for (; i<n; ++i) r+=u[i]*v[i];
    return r;
}
static void merge(const long *a,const long *b,long *d,size_t n) {
    size_t i=0,j=0,k=0;
    while(i<n && j<n) {
        long x=a[i],y=b[j]; int take=x<y;
        d[k++]=take?x:y; i+=(size_t)take; j+=(size_t)(1-take);
    }
    while(i<n) d[k++]=a[i++];
    while(j<n) d[k++]=b[j++];
}
static void copy_forward(const long *src,long *dest,size_t n) {
    for(size_t i=0;i<n;++i) dest[i]=src[i];
}
static void prefix1(const float *a,float *p,size_t n) {
    float s=0;
    for(size_t i=0;i<n;++i) { s=s+a[i]; p[i]=s; }
}
/* Three local prefixes, then one carry per output.
 * Contract: a[0..n) and p[0..n) are disjoint, or a == p.
 * Partial overlap changes the serial loop's read-after-write behavior. */
static void prefix3(const float *a,float *p,size_t n) {
    size_t i=0; float s=0;
    for(;n-i>=3;i+=3) {
        float b0=a[i],b1=b0+a[i+1],b2=b1+a[i+2];
        p[i]=s+b0; p[i+1]=s+b1; s=s+b2; p[i+2]=s;
    }
    for(;i<n;++i) { s=s+a[i]; p[i]=s; }
}
int main(void) {
    uint64_t a[130],b[130];
    size_t lengths=0,prefix_cases=0,inplace_cases=0;
    for(size_t i=0;i<130;++i) {a[i]=(uint64_t)i*17+3; b[i]=(uint64_t)i*9+1;}
    a[0]=UINT64_MAX;
    for(size_t n=0;n<=130;++n) {
        uint64_t sum=0,dot=0;
        for(size_t i=0;i<n;++i) {sum+=a[i];dot+=a[i]*b[i];}
        uint64_t combined=combine5(a,n),d1=dot6x1(a,b,n);
        uint64_t d6=dot6x6(a,b,n),da=dot6x1a(a,b,n);
        require(combined==sum,"combine5 modulo 2^64");
        require(d1==dot && d6==dot && da==dot,"dot products modulo 2^64");
        ++lengths;
    }
    long x[1000],y[1000];
    for(long i=0;i<1000;++i) x[i]=y[i]=i;
    copy_forward(x+1,x,999); copy_forward(y,y+1,999);
    require(x[0]==1 && x[998]==999 && y[999]==0,"forward copy overlap");
    long u[]={-4,0,3,9},v[]={-3,0,7,8},d[8];
    const long want[]={-4,-3,0,0,3,7,8,9};
    merge(u,v,d,4);
    for(size_t i=0;i<8;++i) require(d[i]==want[i],"merged order");
    float f[130],p[130],q[130],inplace1[130],inplace3[130];
    for(size_t i=0;i<130;++i) f[i]=(float)((int)(i%17)-8)/4.0f;
    for(size_t n=0;n<=130;++n) {
        prefix1(f,p,n);prefix3(f,q,n);
        for(size_t i=0;i<n;++i) inplace1[i]=inplace3[i]=f[i];
        prefix1(inplace1,inplace1,n);prefix3(inplace3,inplace3,n);
        for(size_t i=0;i<n;++i) {
            require(p[i]==q[i],"exact prefix input");
            require(inplace1[i]==p[i] && inplace3[i]==q[i],"in-place prefix");
        }
        ++prefix_cases; ++inplace_cases;
    }
    /* This exact input deliberately exposes changed float rounding. */
    const float hard[]={16777216.0f,0.0f,0.0f,1.0f,-16777216.0f,1.0f};
    prefix1(hard,p,6);prefix3(hard,q,6);
    require(p[5]==1 && q[5]==2,"binary32 regrouping counterexample");
    printf("lengths=%zu modular-reductions=ok merge=ok overlap=ok\n",lengths);
    printf("prefix-exact=%zu inplace=%zu serial-last=%.0f grouped-last=%.0f\n",
           prefix_cases,inplace_cases,p[5],q[5]);
    return 0;
}
