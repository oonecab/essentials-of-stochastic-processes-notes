/* Finite byte-arena allocator. 8-byte teaching alignment, not a libc replacement.
 * Full boundary tags or allocated-footer elision; first-fit or next-fit.
 * Metadata uses memcpy, avoiding misalignment and type-aliasing violations. */
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef __APPLE__
#include <malloc/malloc.h>
#endif
#define CAP 65536u
#define FIRST 12u
#define END (CAP-4u)
#define MINBLOCK 16u
#ifndef ARENA_ALIGNMENT
#define ARENA_ALIGNMENT _Alignof(max_align_t)
#endif
_Alignas(ARENA_ALIGNMENT) static union { max_align_t align; unsigned char b[CAP]; } heap;
static size_t rover;
static bool next_fit, elide;
static unsigned cases[4];
static uint32_t get(size_t h) { uint32_t x; memcpy(&x,heap.b+h,4);return x; }
static void put(size_t h,uint32_t x) { memcpy(heap.b+h,&x,4); }
static size_t size(size_t h) { return get(h)&~(uint32_t)7; }
static bool allocated(size_t h) { return (get(h)&1)!=0; }
static bool previous_allocated(size_t h) { return (get(h)&2)!=0; }
static void block(size_t h,size_t n,bool a,bool pa) {
    uint32_t w=(uint32_t)n|(a?1u:0u)|(pa?2u:0u);put(h,w);
    if(n && (!a || !elide))put(h+n-4,w);
}
static void prevbit(size_t h,bool pa) {
    uint32_t w=(get(h)&~2u)|(pa?2u:0u); put(h,w);
    if(size(h) && (!allocated(h)||!elide))put(h+size(h)-4,w);
}
static void init(bool nf,bool no_alloc_footer) {
    next_fit=nf;elide=no_alloc_footer;rover=FIRST;memset(heap.b,0,CAP);memset(cases,0,sizeof cases);
    block(FIRST,END-FIRST,false,true);block(END,0,true,false);
}
static size_t find_fit(size_t need) {
    size_t start=next_fit?rover:FIRST,h=start;
    do {
        if(!allocated(h)&&size(h)>=need)return h;
        h+=size(h);if(h==END)h=FIRST;
    } while(h!=start);
    return END;
}
static void place(size_t h,size_t need) {
    size_t total=size(h);bool pa=previous_allocated(h);
    if(total-need>=MINBLOCK) {
        block(h,need,true,pa);block(h+need,total-need,false,true);prevbit(h+total,false);
        rover=h+need;
    } else { block(h,total,true,pa);prevbit(h+total,true);rover=h+total; }
    if(rover==END)rover=FIRST;
}
static void *toy_malloc(size_t n) {
    size_t overhead=elide?4u:8u;
    if(!n || n>END-FIRST-overhead)return NULL;
    size_t need=(n+overhead+7u)&~(size_t)7u;if(need<MINBLOCK)need=MINBLOCK;
    size_t h=find_fit(need);if(h==END)return NULL;place(h,need);return heap.b+h+4;
}
/* Like free, accepts NULL or an outstanding pointer returned by toy_malloc. */
static void toy_free(void *p) {
    if(!p)return;
    size_t h=(size_t)((unsigned char *)p-heap.b)-4, n=size(h), old_end=h+n;
    bool pa=previous_allocated(h),na=allocated(old_end);unsigned c=(pa?0u:2u)+(na?0u:1u);cases[c]++;
    if(!pa){size_t pn=get(h-4)&~(uint32_t)7;h-=pn;n+=pn;}
    if(!na)n+=size(old_end);
    block(h,n,false,previous_allocated(h));prevbit(h+n,false);
    if(rover>=h&&rover<h+n)rover=h;
}
static bool check(void) {
    size_t h=FIRST;bool pa=true;
    while(h<END){size_t n=size(h);bool a=allocated(h);
        if(n<MINBLOCK || n%8 || n>END-h || (h+4)%8 || previous_allocated(h)!=pa || (!pa&&!a))return false;
        if((!a||!elide)&&get(h)!=get(h+n-4))return false;
        h+=n;pa=a;
    }
    if(h!=END || get(END)!=(1u|(pa?2u:0u)))return false;
    for(h=FIRST;h<END;h+=size(h))if(h==rover)return true;
    return false;
}
static void require(bool b) { if(!b){fputs("allocator invariant failed\n",stderr);exit(1);} }
static void four_cases(bool nf,bool nofooter) {
    for(unsigned wanted=0;wanted<4;wanted++){
        init(nf,nofooter);void *p[5];for(unsigned i=0;i<5;i++){p[i]=toy_malloc(16);require(p[i]!=NULL);memset(p[i],(int)i,16);}
        if(wanted&2u)toy_free(p[1]);
        if(wanted&1u)toy_free(p[3]);
        unsigned before=cases[wanted];toy_free(p[2]);require(cases[wanted]==before+1);require(check());
    }
}
static void test(bool nf,bool nofooter) {
    four_cases(nf,nofooter);init(nf,nofooter);
    require(toy_malloc(0)==NULL && toy_malloc(SIZE_MAX)==NULL);toy_free(NULL);
    void *p[512];size_t lens[512];size_t count=0;
    for(unsigned i=0;i<512;i++){lens[i]=1+(i*37u)%127u;p[i]=toy_malloc(lens[i]);require(p[i]!=NULL);memset(p[i],(int)(i%251),lens[i]);count++;require(check());}
    for(unsigned parity=0;parity<2;parity++)for(size_t i=parity;i<count;i+=2){for(size_t j=0;j<lens[i];j++)require(((unsigned char *)p[i])[j]==i%251);toy_free(p[i]);require(check());}
    require(size(FIRST)==END-FIRST&&!allocated(FIRST));
    p[0]=toy_malloc(END-FIRST-(nofooter?4u:8u));require(p[0]!=NULL);require(toy_malloc(1)==NULL);toy_free(p[0]);require(check());
    printf("allocator=%s footer=%s cases=4 stress=512 restored=65520\n",nf?"next":"first",nofooter?"free-only":"all");
}
static void bench(void) {
    const unsigned rounds=10000;volatile unsigned long checksum=0;
    for(unsigned mode=0;mode<3;mode++){
        if(mode<2)init(mode==1,false);
        clock_t begin=clock();
        for(unsigned r=0;r<rounds;r++){void *p[64];for(unsigned i=0;i<64;i++){size_t n=8u+(i*13u)%120u;p[i]=mode==2?malloc(n):toy_malloc(n);require(p[i]!=NULL);memset(p[i],(int)i,n);checksum+=((unsigned char *)p[i])[n-1];}for(unsigned i=0;i<64;i++){if(mode==2)free(p[i]);else toy_free(p[i]);}}
        double seconds=(double)(clock()-begin)/CLOCKS_PER_SEC;
        printf("backend=%s operations=%u cpu_seconds=%.6f\n",mode==0?"first":mode==1?"next":"libc",rounds*128,seconds);
    }
    printf("checksum=%lu arena_capacity=%u\n",checksum,CAP);
    size_t requested=0, toy_blocks=0, libc_usable=0;void *p[64];init(false,false);
    for(unsigned i=0;i<64;i++){size_t n=8u+(i*13u)%120u;requested+=n;void *q=toy_malloc(n);require(q!=NULL);toy_blocks+=size((size_t)((unsigned char *)q-heap.b)-4);p[i]=malloc(n);require(p[i]!=NULL);
#ifdef __APPLE__
        libc_usable+=malloc_size(p[i]);
#endif
    }
    printf("peak_payload=%zu toy_live_blocks=%zu toy_peak_utilization=%.6f\n",requested,toy_blocks,(double)requested/CAP);
    if(libc_usable)printf("libc_live_usable=%zu payload_to_usable=%.6f\n",libc_usable,(double)requested/libc_usable);
    else puts("libc_live_usable=unavailable");
    for(unsigned i=0;i<64;i++)free(p[i]);
}
int main(int argc,char **argv) {
    if(argc==2&&!strcmp(argv[1],"--bench")){bench();return 0;}if(argc!=1)return 2;
    test(false,false);test(true,false);test(false,true);test(true,true);return 0;
}
