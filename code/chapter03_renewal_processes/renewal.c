#include <stdio.h>
#include <stdint.h>
/* Marsaglia xorshift32 (13/17/5), seed 20261010; fixed for reproducible teaching examples. */
static uint32_t state=UINT32_C(20261010);
static double uniform01(void) {
    state^=state<<13;state^=state>>17;state^=state<<5;
    return ((double)state+0.5)/4294967296.0;
}

int main(void) {
    const int reps=100000;long cycles[2]={0},time[2]={0};
    for (int i=0;i<reps;i++) {
        int j=uniform01()<0.5?0:1;cycles[j]++;time[j]+=j?9:1;
    }
    for (int j=0;j<2;j++)
        printf("%d %.12g %.12g\n",j?9:1,(double)cycles[j]/reps,
               (double)time[j]/(time[0]+time[1]));
    return 0;
}
