#include <stdio.h>
#include <stdint.h>
/* Marsaglia xorshift32 (13/17/5), seed 20261010; fixed for reproducible teaching examples. */
static uint32_t state=UINT32_C(20261010);
static double uniform01(void) {
    state^=state<<13;state^=state>>17;state^=state<<5;
    return ((double)state+0.5)/4294967296.0;
}

int main(void) {
    const int reps=100000,a=5;long total=0,up=0;
    for (int i=0;i<reps;i++) {
        int s=0;long n=0;
        while (s>-a && s<a) { s+=uniform01()<0.5?1:-1;n++; }
        total+=n;if(s==a)up++;
    }
    printf("%.12g %.12g\n",(double)total/reps,(double)up/reps);return 0;
}
