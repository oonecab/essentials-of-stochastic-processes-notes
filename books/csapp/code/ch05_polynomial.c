#include <math.h>
#include <stddef.h>
#include <stdio.h>

static double direct(const double *a,double x,size_t degree) {
    double r=a[0],power=x;
    for(size_t i=1;i<=degree;++i) {r=r+a[i]*power;power=x*power;}
    return r;
}
static double horner(const double *a,double x,size_t degree) {
    double r=a[degree];
    for(size_t i=degree;i>0;--i) r=a[i-1]+x*r;
    return r;
}
/* Partition exponents by residue modulo eight; each chain is Horner in x^8. */
static double split8(const double *a,double x,size_t degree) {
    double x2=x*x,x4=x2*x2,x8=x4*x4,r[8]={0};
    size_t count=degree+1,blocks=count/8,tail=count%8;
    for(size_t j=0;j<tail;++j) r[j]=a[blocks*8+j];
    while(blocks>0) {
        --blocks;
        for(size_t j=0;j<8;++j) r[j]=a[blocks*8+j]+x8*r[j];
    }
    double result=r[7];
    for(size_t j=7;j>0;--j) result=r[j-1]+x*result;
    return result;
}
int main(void) {
    double a[129];size_t count=0;
    const double xs[]={-1,-0.5,0,0.5,1};
    for(size_t i=0;i<129;++i) a[i]=(double)((int)(i%9)-4);
    for(size_t n=0;n<129;++n) for(size_t j=0;j<5;++j) {
        double r=direct(a,xs[j],n),s=horner(a,xs[j],n),t=split8(a,xs[j],n);
        if(!(fabs(r-s)<=1e-12 && fabs(r-t)<=1e-12)) {
            fprintf(stderr,"polynomial check failed: degree=%zu x=%g\n",n,xs[j]);
            return 1;
        }
        ++count;
    }
    const double sample[]={1,2,3,4};
    printf("polynomial-cases=%zu sample=%.0f\n",count,split8(sample,2,3));
    return 0;
}
