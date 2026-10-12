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
    const int jumps=100000;double time[2]={0,0};int visits[2]={0,0},s=0;
    for (int i=0;i<jumps;i++) {
        visits[s]++;time[s]+=-log(uniform01())/(s?1:2);s=1-s;
    }
    for (int i=0;i<2;i++)
        printf("%d %.12g %.12g %.12g\n",i,(double)visits[i]/jumps,
               time[i]/(time[0]+time[1]),time[i]/visits[i]);
    return 0;
}
