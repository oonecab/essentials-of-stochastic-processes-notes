/* Separate-array transpose and in-place Boolean symmetric closure. */
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static size_t minimum(size_t a,size_t b) { return a<b?a:b; }
static void transpose(uint32_t *restrict dst,const uint32_t *restrict src,size_t n,size_t tile) {
    for (size_t ii=0;ii<n;ii+=tile) for (size_t jj=0;jj<n;jj+=tile)
        for (size_t i=ii;i<minimum(ii+tile,n);++i) for (size_t j=jj;j<minimum(jj+tile,n);++j)
            dst[j*n+i]=src[i*n+j];
}
static void undirect(uint32_t *g,size_t n,size_t tile) {
    for (size_t ii=0;ii<n;ii+=tile) for (size_t jj=ii;jj<n;jj+=tile)
        for (size_t i=ii;i<minimum(ii+tile,n);++i)
            for (size_t j=jj>i+1?jj:i+1;j<minimum(jj+tile,n);++j) {
                uint32_t v=g[i*n+j]|g[j*n+i]; g[i*n+j]=v;g[j*n+i]=v;
            }
}
static void graph_plain(uint32_t *g,size_t n) {
    for (size_t i=0;i<n;++i) for (size_t j=0;j<n;++j) g[j*n+i]=g[j*n+i]||g[i*n+j];
}
static void fill(uint32_t *a,size_t n,int graph) {
    for (size_t i=0;i<n;++i) for (size_t j=0;j<n;++j)
        a[i*n+j]=(uint32_t)(graph?((i*3+j*7)%11==0):((i*17+j*3)%1024));
}
static struct timespec timestamp(void) {
    struct timespec t; if (timespec_get(&t,TIME_UTC)!=TIME_UTC) exit(2);
    return t;
}
static double elapsed_since(struct timespec start) {
    struct timespec end=timestamp();
    return (double)(end.tv_sec-start.tv_sec)+(double)(end.tv_nsec-start.tv_nsec)*1e-9;
}
static int verify(void) {
    const size_t dims[]={0,1,2,3,7,16,17,31,32,33,64},tiles[]={1,2,7,16,32};
    uint32_t a[4096],d[4096]; size_t count=0;
    for (size_t u=0;u<sizeof dims/sizeof *dims;++u) for (size_t v=0;v<sizeof tiles/sizeof *tiles;++v) {
        size_t n=dims[u];fill(a,n,0);transpose(d,a,n,tiles[v]);
        for (size_t i=0;i<n;++i) for (size_t j=0;j<n;++j) if (d[j*n+i]!=a[i*n+j]) return 1;
        fill(a,n,1);memcpy(d,a,n*n*sizeof *a);undirect(d,n,tiles[v]);
        for (size_t i=0;i<n;++i) for (size_t j=0;j<n;++j) if (d[i*n+j]!=(a[i*n+j]|a[j*n+i])) return 1;
        ++count;
    }
    printf("dimensions=11 tile-cases=%zu transpose=PASS undirect=PASS\n",count);return 0;
}
static int parse(const char *s,size_t max,size_t *out) {
    if (!*s || *s=='-' || *s=='+') return 0;
    char *end;errno=0;uintmax_t n=strtoumax(s,&end,10);
    if (errno||*end||!n||n>max) return 0;
    *out=(size_t)n;return 1;
}
int main(int argc,char **argv) {
    if (argc==1) return verify();
    size_t n,reps;
    if (argc!=4||strcmp(argv[1],"--bench")||!parse(argv[2],2048,&n)||!parse(argv[3],31,&reps)) return 2;
    /* Batch tiny kernels above the wall clock's resolution. Volatile function
       pointers preserve every call. Each graph call gets its own original
       directed input; all copies are prepared outside the timed interval. */
    size_t cells=n*n;
    size_t batch=n<256?65536/(n*n):1;
    uint32_t *a=malloc(cells*sizeof *a),*d=malloc(batch*cells*sizeof *d);
    if (!a||!d) {free(a);free(d);return 2;}
    void (*volatile trans_call)(uint32_t *,const uint32_t *,size_t,size_t)=transpose;
    void (*volatile graph_call)(uint32_t *,size_t,size_t)=undirect;
    void (*volatile plain_call)(uint32_t *,size_t)=graph_plain;
    const char *names[]={"transpose_plain","transpose_tiled16","transpose_tiled32","graph_plain","graph_triangle","graph_tiled16"};
    for (int mode=0;mode<6;++mode) {
        fill(a,n,mode>=3);double best=1e30;uint64_t sum=0;
        for (size_t r=0;r<reps;++r) {
            if (mode>=3)
                for (size_t z=0;z<batch;++z) memcpy(d+z*cells,a,cells*sizeof *a);
            struct timespec start=timestamp();
            for (size_t z=0;z<batch;++z) {
                if (mode<3) trans_call(d,a,n,mode==0?n:mode==1?16:32);
                else {
                    uint32_t *g=d+z*cells;
                    if (mode==3) plain_call(g,n);else graph_call(g,n,mode==4?n:16);
                }
            }
            double elapsed=elapsed_since(start)/(double)batch;
            if (elapsed<=0) {free(a);free(d);return 2;}
            if (elapsed<best) best=elapsed;
        }
        for (size_t i=0;i<n*n;++i) sum+=d[i];
        printf("%s n=%zu best_ms=%.3f checksum=%"PRIu64"\n",names[mode],n,best*1000,sum);
    }
    free(a);free(d);return 0;
}
