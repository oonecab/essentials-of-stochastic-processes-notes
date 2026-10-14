/* Exercise 12.26: POSIX gethostbyname lock + deep copy.
 * All accesses to this legacy resolver must use the same lock. Each caller owns
 * the returned copy, freed with hostent_free. A mutex makes this thread-safe,
 * but it is not reentrant in the textbook sense and not signal-handler safe.
 * New programs should normally use getaddrinfo/getnameinfo instead. */
#define _POSIX_C_SOURCE 200809L
#include <netdb.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static pthread_mutex_t resolver_lock=PTHREAD_MUTEX_INITIALIZER;
void hostent_free(struct hostent *h) {
    if(!h)return;
    free(h->h_name);
    if(h->h_aliases){for(size_t i=0;h->h_aliases[i];++i)free(h->h_aliases[i]);free(h->h_aliases);}
    if(h->h_addr_list){for(size_t i=0;h->h_addr_list[i];++i)free(h->h_addr_list[i]);free(h->h_addr_list);}
    free(h);
}
static char *string_copy(const char *s){
    size_t n=strlen(s)+1;char *p=malloc(n);if(p)memcpy(p,s,n);return p;
}
/* Some host resolver implementations return packed pointer vectors. Byte-copy
 * each pointer representation before accessing it; destination vectors are aligned. */
static char *vector_at(char *const *vector,size_t i){
    char *value;memcpy(&value,(const unsigned char *)vector+i*sizeof(value),sizeof(value));return value;
}
struct hostent *gethostbyname_ts(const char *name) {
    if(pthread_mutex_lock(&resolver_lock)!=0)return NULL;
    const struct hostent *src=gethostbyname(name);
    struct hostent *dst=NULL;
    if(!src || src->h_length<=0)goto out;
    dst=calloc(1,sizeof(*dst));if(!dst)goto out;
    dst->h_addrtype=src->h_addrtype;dst->h_length=src->h_length;
    dst->h_name=string_copy(src->h_name);if(!dst->h_name)goto fail;
    size_t na=0,nd=0;
    while(vector_at(src->h_aliases,na))++na;
    while(vector_at(src->h_addr_list,nd))++nd;
    dst->h_aliases=calloc(na+1,sizeof(char *));
    dst->h_addr_list=calloc(nd+1,sizeof(char *));
    if(!dst->h_aliases || !dst->h_addr_list)goto fail;
    for(size_t i=0;i<na;++i){dst->h_aliases[i]=string_copy(vector_at(src->h_aliases,i));if(!dst->h_aliases[i])goto fail;}
    for(size_t i=0;i<nd;++i){
        dst->h_addr_list[i]=malloc((size_t)src->h_length);
        if(!dst->h_addr_list[i])goto fail;
        memcpy(dst->h_addr_list[i],vector_at(src->h_addr_list,i),(size_t)src->h_length);
    }
    goto out;
fail:hostent_free(dst);dst=NULL;
out:(void)pthread_mutex_unlock(&resolver_lock);return dst;
}
static void *probe(void *unused){
    (void)unused;
    for(int i=0;i<16;++i){
        struct hostent *a=gethostbyname_ts("localhost");
        struct hostent *b=gethostbyname_ts("localhost");
        if(!a || !b || !a->h_addr_list[0] || !b->h_addr_list[0] || a->h_name==b->h_name ||
           a->h_addr_list[0]==b->h_addr_list[0]){fputs("resolver copy failure\n",stderr);exit(1);}
        /* Mutating one owned copy must not affect another result. */
        unsigned char original=(unsigned char)b->h_addr_list[0][0];
        a->h_addr_list[0][0]=(char)((unsigned char)a->h_addr_list[0][0]^255u);
        if((unsigned char)b->h_addr_list[0][0]!=original)exit(1);
        hostent_free(a);hostent_free(b);
    }
    return NULL;
}
int main(void){
    pthread_t t[3];
    for(int i=0;i<3;++i)if(pthread_create(&t[i],NULL,probe,NULL))return 1;
    for(int i=0;i<3;++i)if(pthread_join(t[i],NULL))return 1;
    if(pthread_mutex_destroy(&resolver_lock))return 1;
    puts("resolver threads=3 copies=96 independent=YES");return 0;
}
