#include <stdio.h>
#include <math.h>
#include <stdint.h>
/* Marsaglia xorshift32 (13/17/5), seed 20261010; fixed for reproducible teaching examples. */
static uint32_t state=UINT32_C(20261010);
static double uniform01(void) {
    state^=state<<13;state^=state>>17;state^=state<<5;
    return ((double)state+0.5)/4294967296.0;
}

int main(void) {
    const int reps=100000, cap=16;int counts[17]={0};
    for (int i=0;i<reps;i++) {
        double t=0;int n=0;
        for (;;) { t+=-log(uniform01())/3.0;if(t>2)break;n++; }
        counts[n<cap?n:cap]++;
    }
    double theory=exp(-6), sum=0;
    for (int k=0;k<=cap;k++) {
        double p=k==cap?1-sum:theory;
        printf("%d %.12g %.12g\n",k,p,(double)counts[k]/reps);
        sum+=theory;theory*=6.0/(k+1);
    }
    return 0;
}
