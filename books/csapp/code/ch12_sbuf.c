/* Exercise 12.9: remove only the sbuf buffer mutex. Independent counting
 * semaphores still synchronize slot ownership. Valid cases: SPSC any n,
 * or n=1 with any producer/consumer counts. No unsynchronized shared count.
 * C11/POSIX; counting semaphores use mutex+condition for macOS portability. */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
enum { TOTAL=1000, MAX_CAP=7, PEERS=3 };
typedef struct {unsigned value;pthread_mutex_t m;pthread_cond_t cv;} semaphore;
static semaphore slots,items;
static int buffer[MAX_CAP],capacity,front,rear;
static void check(int e){if(e){fprintf(stderr,"pthread: %s\n",strerror(e));exit(1);}}
static void init(semaphore *s,unsigned v){s->value=v;check(pthread_mutex_init(&s->m,NULL));check(pthread_cond_init(&s->cv,NULL));}
static void down(semaphore *s){check(pthread_mutex_lock(&s->m));while(!s->value)check(pthread_cond_wait(&s->cv,&s->m));--s->value;check(pthread_mutex_unlock(&s->m));}
static void up(semaphore *s){check(pthread_mutex_lock(&s->m));++s->value;check(pthread_cond_signal(&s->cv));check(pthread_mutex_unlock(&s->m));}
static void destroy(semaphore *s){check(pthread_cond_destroy(&s->cv));check(pthread_mutex_destroy(&s->m));}
static void put(int value){down(&slots);rear=(rear+1)%capacity;buffer[rear]=value;up(&items);}
static int take(void){down(&items);front=(front+1)%capacity;int v=buffer[front];up(&slots);return v;}
typedef struct {int first,last;unsigned seen[TOTAL+1];} job;
static void *producer(void *arg){job *j=arg;for(int i=j->first;i<j->last;++i)put(i);return NULL;}
static void *consumer(void *arg){job *j=arg;for(;;){int v=take();if(!v)break;if(v<1||v>TOTAL)exit(1);++j->seen[v];}return NULL;}
static void run(int n,int count){
    capacity=n;front=rear=0;init(&slots,(unsigned)n);init(&items,0);
    pthread_t producers[PEERS],consumers[PEERS];job p[PEERS]={0},c[PEERS]={0};
    for(int i=0;i<count;++i){p[i].first=1+TOTAL*i/count;p[i].last=1+TOTAL*(i+1)/count;
        check(pthread_create(&consumers[i],NULL,consumer,&c[i]));check(pthread_create(&producers[i],NULL,producer,&p[i]));}
    for(int i=0;i<count;++i)check(pthread_join(producers[i],NULL));
    for(int i=0;i<count;++i)put(0);
    for(int i=0;i<count;++i)check(pthread_join(consumers[i],NULL));
    for(int v=1;v<=TOTAL;++v){unsigned seen=0;for(int i=0;i<count;++i)seen+=c[i].seen[v];if(seen!=1)exit(1);}
    destroy(&slots);destroy(&items);
    printf("sbuf no_buffer_mutex capacity=%d producers=%d consumers=%d items=%d exactly_once=YES\n",n,count,count,TOTAL);
}
int main(void){run(7,1);run(1,1);run(1,3);return 0;}
