/* C11 + POSIX. clang -std=c11 -Wall -Wextra -Werror -pedantic -pthread
 * -fsanitize=address,undefined ch12_threads.c -o ch12_threads
 * No deliberately racing C accesses: bad schedules live in ch12_models.
 * --hello N joins N peers; --bench measures the same matrix kernel. */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>

enum { CAP = 7, ITEMS = 1000, WORKERS = 3, DIM = 96 };
static void check(int error) {
    if (error) { fprintf(stderr, "pthread: %s\n", strerror(error)); exit(1); }
}
static void require(int ok) { if (!ok) { fputs("invariant failed\n", stderr); exit(1); } }
typedef struct {
    int data[CAP]; size_t head, tail, count;
    pthread_mutex_t lock;
    pthread_cond_t not_empty, not_full;
} queue;
static queue q = { .lock = PTHREAD_MUTEX_INITIALIZER,
    .not_empty = PTHREAD_COND_INITIALIZER, .not_full = PTHREAD_COND_INITIALIZER };
static void put(int value) {
    check(pthread_mutex_lock(&q.lock));
    while (q.count == CAP) check(pthread_cond_wait(&q.not_full, &q.lock));
    q.data[q.tail] = value; q.tail = (q.tail + 1) % CAP; q.count++;
    require(q.count <= CAP);
    check(pthread_cond_signal(&q.not_empty));
    check(pthread_mutex_unlock(&q.lock));
}
static int take(void) {
    check(pthread_mutex_lock(&q.lock));
    while (!q.count) check(pthread_cond_wait(&q.not_empty, &q.lock));
    int value = q.data[q.head]; q.head = (q.head + 1) % CAP; q.count--;
    check(pthread_cond_signal(&q.not_full));
    check(pthread_mutex_unlock(&q.lock));
    return value;
}
typedef struct { long sum; unsigned seen[ITEMS + 1]; } consumer_state;
static void *consume(void *arg) {
    consumer_state *s = arg;
    for (;;) {
        int value = take();
        if (!value) break;
        require(value >= 1 && value <= ITEMS);
        s->sum += value; s->seen[value]++;
    }
    return NULL;
}
static pthread_mutex_t counter_lock = PTHREAD_MUTEX_INITIALIZER;
static long counter;
static void *increment(void *unused) {
    (void)unused;
    for (int i = 0; i < 10000; ++i) {
        check(pthread_mutex_lock(&counter_lock));
        counter++;
        check(pthread_mutex_unlock(&counter_lock));
    }
    return NULL;
}
typedef struct { size_t id; size_t result; } hello_arg;
static void *hello(void *arg) {
    hello_arg *a = arg; a->result = a->id;
    if (printf("Hello from thread %zu\n", a->id) < 0) exit(1);
    return NULL;
}
static void hello_n(size_t n) {
    pthread_t *ids = calloc(n, sizeof(*ids));
    hello_arg *args = calloc(n, sizeof(*args));
    require(ids && args);
    for (size_t i = 0; i < n; ++i) {
        args[i].id = i;
        check(pthread_create(&ids[i], NULL, hello, &args[i]));
    }
    for (size_t i = 0; i < n; ++i) {
        check(pthread_join(ids[i], NULL)); require(args[i].result == i);
    }
    free(args); free(ids);
}
/* A: N x K, B: K x M, C: N x M. Each worker owns disjoint rows of C. */
typedef struct {
    const double *a, *b; double *c;
    size_t m, k, first, limit;
} matrix_job;
static void *multiply(void *arg) {
    matrix_job *j = arg;
    for (size_t row = j->first; row < j->limit; ++row)
        for (size_t col = 0; col < j->m; ++col) {
            double sum = 0;
            for (size_t k = 0; k < j->k; ++k)
                sum += j->a[row*j->k+k] * j->b[k*j->m+col];
            j->c[row*j->m+col] = sum;
        }
    return NULL;
}
static void parallel_matrix(const double *a, const double *b, double *c,
                            size_t n, size_t k, size_t m, size_t workers) {
    pthread_t ids[WORKERS]; matrix_job jobs[WORKERS];
    require(workers >= 1 && workers <= WORKERS);
    for (size_t i = 0; i < workers; ++i) {
        jobs[i] = (matrix_job){a,b,c,m,k,n*i/workers,n*(i+1)/workers};
        check(pthread_create(&ids[i], NULL, multiply, &jobs[i]));
    }
    for (size_t i = 0; i < workers; ++i) check(pthread_join(ids[i], NULL));
}
static double now(void) {
    struct timespec t; require(clock_gettime(CLOCK_MONOTONIC, &t) == 0);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}
static void matrix_test(int bench) {
    static double a[DIM*DIM], b[DIM*DIM], reference[DIM*DIM], result[DIM*DIM];
    for (size_t i=0; i<DIM*DIM; ++i) { a[i]=(double)(i%7); b[i]=(double)(i%5); }
    /* Non-square case: 5 x 7 multiplied by 7 x 4, remainder rows included. */
    matrix_job small = {a,b,reference,4,7,0,5}; (void)multiply(&small);
    parallel_matrix(a,b,result,5,7,4,3);
    require(memcmp(reference,result,20*sizeof(double)) == 0);
    matrix_job full = {a,b,reference,DIM,DIM,0,DIM};
    double t0=now(); (void)multiply(&full); double serial=now()-t0;
    t0=now(); parallel_matrix(a,b,result,DIM,DIM,DIM,3); double parallel=now()-t0;
    require(memcmp(reference,result,sizeof(reference)) == 0);
    puts("matrix cases=2 exact=YES workers=3");
    if (bench) printf("matrix=96x96x96 serial_seconds=%.9f parallel_seconds=%.9f speedup=%.3f\n",
                      serial,parallel,serial/parallel);
}
int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1],"--hello") == 0) {
        char *end; errno=0; unsigned long n=strtoul(argv[2],&end,10);
        if (errno || !*argv[2] || *end || argv[2][0]=='-' || n<1 || n>64) return 2;
        hello_n((size_t)n); return 0;
    }
    int bench=argc==2 && strcmp(argv[1],"--bench")==0;
    if (argc!=1 && !bench) return 2;
    pthread_t threads[WORKERS];
    for (int i=0;i<WORKERS;++i) check(pthread_create(&threads[i],NULL,increment,NULL));
    for (int i=0;i<WORKERS;++i) check(pthread_join(threads[i],NULL));
    require(counter==30000); printf("mutex counter=%ld\n",counter);
    consumer_state states[WORKERS] = {{0,{0}}};
    for (int i=0;i<WORKERS;++i) check(pthread_create(&threads[i],NULL,consume,&states[i]));
    for (int i=1;i<=ITEMS;++i) put(i);
    for (int i=0;i<WORKERS;++i) put(0);
    long sum=0;
    for (int i=0;i<WORKERS;++i) { check(pthread_join(threads[i],NULL)); sum+=states[i].sum; }
    for (int value=1;value<=ITEMS;++value) {
        unsigned count=0; for (int i=0;i<WORKERS;++i) count+=states[i].seen[value];
        require(count==1);
    }
    require(sum==500500 && q.count==0);
    printf("queue items=%d sum=%ld exactly_once=YES\n",ITEMS,sum);
    matrix_test(bench);
    check(pthread_mutex_destroy(&counter_lock)); check(pthread_mutex_destroy(&q.lock));
    check(pthread_cond_destroy(&q.not_empty)); check(pthread_cond_destroy(&q.not_full));
    return 0;
}
