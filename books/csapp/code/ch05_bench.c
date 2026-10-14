/* Build: clang -std=c11 -O3 -ffp-contract=off -fno-vectorize
   -fno-slp-vectorize ch05_bench.c -o ch05_bench */
#define main polynomial_checks
#include "ch05_polynomial.c"
#undef main
#define main loop_checks
#include "ch05_loops.c"
#undef main
#include <time.h>

static volatile double observed;
static volatile double argument=0.999;
static double now(void) {
    struct timespec t;
    if(timespec_get(&t,TIME_UTC)!=TIME_UTC) return -1;
    return (double)t.tv_sec+(double)t.tv_nsec*1e-9;
}
int main(void) {
    enum {N=8192,R=4000};
    double a[N];float f[N],p[N];
    for(size_t i=0;i<N;++i) {a[i]=(double)((int)(i%9)-4);f[i]=(float)(i%5)/4;}
    double (*poly[])(const double *,double,size_t)={direct,horner,split8};
    const char *names[]={"direct","horner","split8"};
    puts("unit=ns/element n=8192 repetitions=4000 scalar no-fma");
    for(size_t j=0;j<3;++j) {
        observed=poly[j](a,0.999,N-1);
        double begin=now();
        for(size_t k=0;k<R;++k) observed=poly[j](a,argument,N-1);
        double elapsed=now()-begin;
        if(elapsed<=0) return 2;
        printf("%s %.3f\n",names[j],elapsed*1e9/(N*(double)R));
    }
    void (*prefixes[])(const float *,float *,size_t)={prefix1,prefix3};
    for(size_t j=0;j<2;++j) {
        prefixes[j](f,p,N);observed=p[N-1];
        double begin=now();
        for(size_t k=0;k<R;++k) {prefixes[j](f,p,N);observed=p[N-1];}
        double elapsed=now()-begin;
        if(elapsed<=0) return 2;
        printf("prefix%u %.3f\n",j?3u:1u,elapsed*1e9/(N*(double)R));
    }
    return 0;
}
