/* C11/POSIX, three bounded tfgets implementations for Exercises 12.31--33.
 * Contract: size >= 2; stream exclusively owns an unbuffered descriptor, with
 * no unread stdio buffer; not mixed with other stdio reads. Text excludes NUL.
 * EOF after bytes returns that partial final line; timeout discards the partial
 * result but cannot undo consumed bytes. proc requires a single-threaded caller
 * and exclusive SIGUSR1 use. It exclusively reaps its timer child: the caller
 * must not auto-reap via SIGCHLD or use another handler/wait to reap it.
 * All helper threads/children are joined/reaped.
 * Build: clang -std=c11 -Wall -Wextra -Werror -pedantic -pthread
 * -fsanitize=address,undefined ch12_tfgets.c -o ch12_tfgets
 * Run: ch12_tfgets proc|select|thread < input (five-second absolute deadline). */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <pthread.h>
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static double monotonic(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC,&t)<0) return -1;
    return (double)t.tv_sec+(double)t.tv_nsec/1e9;
}
static char *read_deadline(char *s,int size,int fd,const sigset_t *mask) {
    if (size<2 || fd<0 || fd>=FD_SETSIZE) { errno=EINVAL; return NULL; }
    double end=monotonic()+5.0; int used=0; s[0]='\0';
    while (used<size-1) {
        double left=end-monotonic();
        if (left<=0) { errno=ETIMEDOUT; return NULL; }
        struct timespec delay={(time_t)left,(long)((left-(double)(time_t)left)*1e9)};
        fd_set ready; FD_ZERO(&ready);FD_SET(fd,&ready);
        int rc=pselect(fd+1,&ready,NULL,NULL,&delay,mask);
        if (rc<0) { if(errno==EINTR) continue; return NULL; }
        if (!rc) { errno=ETIMEDOUT; return NULL; }
        char ch; ssize_t n=read(fd,&ch,1);
        if (n<0) { if(errno==EINTR) continue; return NULL; }
        if (!n) return used?s:NULL;
        s[used++]=ch;s[used]='\0';
        if(ch=='\n') break;
    }
    return s;
}
/* select version uses the same absolute deadline but actual select(2). */
char *tfgets_select(char *s,int size,FILE *stream) {
    int fd=fileno(stream),used=0;
    if(size<2 || fd<0 || fd>=FD_SETSIZE) { errno=EINVAL; return NULL; }
    double end=monotonic()+5.0;s[0]='\0';
    while(used<size-1) {
        double left=end-monotonic();
        if(left<=0) { errno=ETIMEDOUT;return NULL; }
        struct timeval tv={(time_t)left,(suseconds_t)((left-(double)(time_t)left)*1e6)};
        fd_set set;FD_ZERO(&set);FD_SET(fd,&set);
        int n=select(fd+1,&set,NULL,NULL,&tv);
        if(n<0) { if(errno==EINTR) continue; return NULL; }
        if(!n) {errno=ETIMEDOUT;return NULL;}
        char ch;ssize_t got=read(fd,&ch,1);
        if(got<0){if(errno==EINTR)continue;return NULL;}
        if(!got)return used?s:NULL;
        s[used++]=ch;s[used]='\0';if(ch=='\n')break;
    }
    return s;
}
static sigjmp_buf timeout_env;
static void timeout_signal(int sig) { (void)sig; siglongjmp(timeout_env,1); }
char *tfgets_proc(char *s,int size,FILE *stream) {
    sigset_t block,old,waiting,pending; struct sigaction action,previous;
    sigemptyset(&block);sigaddset(&block,SIGUSR1);
    if(sigprocmask(SIG_BLOCK,&block,&old)<0)return NULL;
    if(sigpending(&pending)<0 || sigismember(&pending,SIGUSR1)) {
        (void)sigprocmask(SIG_SETMASK,&old,NULL);errno=EBUSY;return NULL;
    }
    memset(&action,0,sizeof(action));action.sa_handler=timeout_signal;sigemptyset(&action.sa_mask);
    if(sigaction(SIGUSR1,&action,&previous)<0){(void)sigprocmask(SIG_SETMASK,&old,NULL);return NULL;}
    pid_t parent=getpid(), timer=fork();
    if(timer<0){(void)sigaction(SIGUSR1,&previous,NULL);(void)sigprocmask(SIG_SETMASK,&old,NULL);return NULL;}
    if(!timer){
        struct timespec delay={5,0};while(nanosleep(&delay,&delay)<0 && errno==EINTR){}
        (void)kill(parent,SIGUSR1);_exit(0);
    }
    /* s is caller storage; only volatile locals may change across siglongjmp. */
    char *volatile result=NULL;volatile int saved=0;
    waiting=old;sigdelset(&waiting,SIGUSR1);
    if(sigsetjmp(timeout_env,1)==0){result=read_deadline(s,size,fileno(stream),&waiting);saved=errno;}
    else saved=ETIMEDOUT;
    /* SIGUSR1 is blocked here, including after normal pselect return.
     * This function owns the unreaped timer child. SIGKILL cancels it even
     * when the caller ignores or blocks SIGTERM; waitpid still reaps it. */
    if(kill(timer,SIGKILL)<0 && errno!=ESRCH)saved=errno;
    while(waitpid(timer,NULL,0)<0){if(errno!=EINTR){saved=errno;break;}}
    if(sigpending(&pending)==0 && sigismember(&pending,SIGUSR1)){
        int signo;int e=sigwait(&block,&signo);if(e)saved=e;
    }
    (void)sigaction(SIGUSR1,&previous,NULL);(void)sigprocmask(SIG_SETMASK,&old,NULL);
    errno=saved;return result;
}
typedef struct {
    char *s;int size;FILE *stream;char *result;int error,done;
    pthread_mutex_t mutex;pthread_cond_t complete;
} reader_job;
static void *reader(void *arg) {
    reader_job *j=arg;char *value=tfgets_select(j->s,j->size,j->stream);int error=errno;
    (void)pthread_mutex_lock(&j->mutex);
    j->result=value;j->error=error;j->done=1;
    (void)pthread_cond_signal(&j->complete);(void)pthread_mutex_unlock(&j->mutex);
    return NULL;
}
char *tfgets_thread(char *s,int size,FILE *stream) {
    reader_job job={.s=s,.size=size,.stream=stream,.mutex=PTHREAD_MUTEX_INITIALIZER,
                    .complete=PTHREAD_COND_INITIALIZER};
    pthread_t tid;int error=pthread_create(&tid,NULL,reader,&job);
    if(error){errno=error;return NULL;}
    /* The worker owns the five-second deadline. Join prevents any later write
     * to the caller's stack or buffer; no detached timeout thread survives. */
    (void)pthread_mutex_lock(&job.mutex);
    while(!job.done)(void)pthread_cond_wait(&job.complete,&job.mutex);
    (void)pthread_mutex_unlock(&job.mutex);
    error=pthread_join(tid,NULL);
    (void)pthread_cond_destroy(&job.complete);(void)pthread_mutex_destroy(&job.mutex);
    errno=error?error:job.error;return error?NULL:job.result;
}
int main(int argc,char **argv) {
    if(argc==1){puts("usage: ch12_tfgets proc|select|thread (five-second stdin deadline)");return 0;}
    if(argc!=2)return 2;
    char *(*fn)(char *,int,FILE *)=NULL;
    if(strcmp(argv[1],"proc")==0)fn=tfgets_proc;
    if(strcmp(argv[1],"select")==0)fn=tfgets_select;
    if(strcmp(argv[1],"thread")==0)fn=tfgets_thread;
    if(!fn)return 2;
    if(setvbuf(stdin,NULL,_IONBF,0)!=0)return 1;
    char buf[256];errno=0;
    if(fn(buf,sizeof(buf),stdin))fputs(buf,stdout);
    else puts("BOOM!");
    return ferror(stdout)?1:0;
}
