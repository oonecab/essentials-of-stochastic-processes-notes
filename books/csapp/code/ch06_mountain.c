/* Portable memory-mountain experiment. Wall-clock bandwidth, not load latency. */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static volatile uint64_t sink;
static uint64_t scan(const volatile uint64_t *a,size_t n,size_t stride) {
    size_t i=0;uint64_t x=0,y=0,z=0,w=0;
    for (;i+3*stride<n;i+=4*stride) {
        x+=a[i];y+=a[i+stride];z+=a[i+2*stride];w+=a[i+3*stride];
    }
    for (;i<n;i+=stride) x+=a[i];
    return (x+y)+(z+w);
}
static double seconds(void) {
    struct timespec t;if (timespec_get(&t,TIME_UTC)!=TIME_UTC) exit(2);
    return (double)t.tv_sec+(double)t.tv_nsec*1e-9;
}
int main(int argc,char **argv) {
    if (argc==1) {
        uint64_t a[65];size_t checks=0;
        for (size_t i=0;i<65;++i) a[i]=i;
        for (size_t n=0;n<65;++n) for (size_t stride=1;stride<=17;++stride) {
            uint64_t expected=0;for (size_t i=0;i<n;i+=stride) expected+=i;
            if (scan(a,n,stride)!=expected) return 1;
            ++checks;
        }
        printf("scan-cases=%zu checksum=PASS\n",checks);return 0;
    }
    if (argc!=2||strcmp(argv[1],"--bench")) return 2;
    const size_t maximum=128u*1024u*1024u, strides[]={1,2,4,8,16};
    uint64_t *a=malloc(maximum);if (!a) return 2;
    for (size_t i=0;i<maximum/sizeof *a;++i) a[i]=i;
    puts("size_bytes,stride_elements,useful_bytes_per_scan,MB_per_second");
    for (size_t bytes=16384;bytes<=maximum;bytes*=2) for (size_t k=0;k<sizeof strides/sizeof *strides;++k) {
        size_t stride=strides[k],n=bytes/sizeof *a,count=(n+stride-1)/stride;
        size_t reps=(32u*1024u*1024u)/(count*sizeof *a);if (!reps) reps=1;
        double best=1e30;sink=scan(a,n,stride);
        for (int trial=0;trial<3;++trial) {
            double start=seconds();
            for (size_t r=0;r<reps;++r) sink=scan(a,n,stride);
            double elapsed=seconds()-start;if (elapsed<=0) {free(a);return 2;}
            if (elapsed<best) best=elapsed;
        }
        printf("%zu,%zu,%zu,%.2f\n",bytes,stride,count*sizeof *a,(double)(count*sizeof *a)*reps/best/1e6);
    }
    free(a);return 0;
}
