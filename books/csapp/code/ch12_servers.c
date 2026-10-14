/* C11/POSIX concurrent Tiny and proxy laboratory (Exercises 12.22--23,35--39).
 * Reuses the Chapter 11 bounded HTTP parser/response builder as one translation
 * unit. This concurrency lab computes adder in the core; Chapter 11
 * --serve-cgi separately demonstrates actual CGI fork/exec and SIGCHLD reaping. Network event I/O is nonblocking; small local file
 * reads in build_response remain synchronous. This is a teaching boundary.
 * Only 127.0.0.1 listeners and loopback HTTP proxy destinations; no TLS/CONNECT.
 * --serve MODE ROOT PORT CONNECTIONS [FILTER LOG], PORT=0 selects ephemeral port.
 * MODE: process/select/thread/pool/echo/proxy/proxy-serial. Limit 1..128;
 * 120-second acceptance window, then drain accepted connections. Event clients
 * have a 3-second deadline refreshed by each successful read; blocking sockets
 * have 2-second I/O deadlines. A full pool queue can defer the next window check.
 * clang -std=c11 -Wall -Wextra -Werror -pedantic -pthread -fsanitize=address,undefined
 * books/csapp/code/ch12_servers.c -o tmp/csapp/part3/ch12/servers
 */
#define main ch11_http_example_main
#include "ch11_http.c"
#undef main
#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sys/select.h>

enum { MAX_CLIENTS=128, QUEUE_CAPACITY=4, MAX_WORKERS=8, MAX_THREAD_IDS=256 };
static void pcheck(int e){if(e){fprintf(stderr,"pthread: %s\n",strerror(e));exit(1);}}
static pthread_mutex_t log_mutex=PTHREAD_MUTEX_INITIALIZER;
static const char *filter_path,*log_path;
static void socket_deadline(int fd){
    int flags=fcntl(fd,F_GETFL,0);
    if(flags>=0)(void)fcntl(fd,F_SETFL,flags & ~O_NONBLOCK);
    struct timeval timeout={2,0};
    (void)setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
    (void)setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
}
static int listen_loopback(int port){
    int fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return -1;
    int yes=1;(void)setsockopt(fd,SOL_SOCKET,SO_REUSEADDR,&yes,sizeof(yes));
    struct sockaddr_in addr;memset(&addr,0,sizeof(addr));addr.sin_family=AF_INET;
    addr.sin_addr.s_addr=htonl(INADDR_LOOPBACK);addr.sin_port=htons((unsigned short)port);
    if(bind(fd,(struct sockaddr *)&addr,sizeof(addr)) || listen(fd,32)){close(fd);return -1;}
    int flags=fcntl(fd,F_GETFL,0);
    if(flags<0 || fcntl(fd,F_SETFL,flags|O_NONBLOCK)<0){close(fd);return -1;}
    socklen_t size=sizeof(addr);if(getsockname(fd,(struct sockaddr *)&addr,&size)){close(fd);return -1;}
    printf("LISTEN 127.0.0.1 %u\n",(unsigned)ntohs(addr.sin_port));fflush(stdout);return fd;
}
static void proxy_error(int fd,int code){
    char response[256];const char *msg=code==403?"Forbidden":"Bad Gateway";
    int n=snprintf(response,sizeof(response),"HTTP/1.0 %d %s\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n%s",code,msg,strlen(msg),msg);
    if(n>0 && (size_t)n<sizeof(response))(void)write_all(fd,response,(size_t)n);
}
static int blocked_and_log(const char *url){
    int blocked=0;char line[2048];
    /* Both paths are caller-selected lab files; filter is read-only. */
    pcheck(pthread_mutex_lock(&log_mutex));
    FILE *filter=fopen(filter_path,"r");
    if(!filter){pcheck(pthread_mutex_unlock(&log_mutex));return -1;}
    while(fgets(line,sizeof(line),filter)){
        line[strcspn(line,"\r\n")]=0;if(!strcmp(line,url))blocked=1;
    }
    if(ferror(filter))blocked=-1;
    fclose(filter);
    FILE *log=fopen(log_path,"a");
    if(!log)blocked=-1;
    else {if(fprintf(log,"%s %s\n",blocked==1?"BLOCK":"ALLOW",url)<0)blocked=-1;if(fclose(log))blocked=-1;}
    pcheck(pthread_mutex_unlock(&log_mutex));return blocked;
}
static int proxy_handle(int fd){
    char input[CH11_REQUEST_LIMIT+1];size_t used=0,expected=0;long long incoming_end=now_ms()+2000;
    while(used<CH11_REQUEST_LIMIT){
        if(!io_ready(fd,POLLIN,incoming_end))return -1;
        ssize_t n=read(fd,input+used,CH11_REQUEST_LIMIT-used);
        if(n<0 && errno==EINTR)continue;if(n<=0)return -1;
        used+=(size_t)n;int framing=request_size(input,used,&expected);
        if(framing<0){proxy_error(fd,502);return -1;}
        if(framing==1)break;
    }
    if(request_size(input,used,&expected)!=1 || expected!=used){proxy_error(fd,502);return -1;}
    input[used]=0;char method[16],url[2048],version[16],extra;
    char *line_end=strstr(input,"\r\n");if(!line_end)return -1;*line_end=0;
    if(sscanf(input,"%15s %2047s %15s %c",method,url,version,&extra)!=3 || strcmp(method,"GET") ||
       strncmp(url,"http://",7) || (strcmp(version,"HTTP/1.0") && strcmp(version,"HTTP/1.1"))){proxy_error(fd,502);return -1;}
    for(const char *p=url;*p;++p)if((unsigned char)*p<=32 || (unsigned char)*p>=127){proxy_error(fd,502);return -1;}
    int blocked=blocked_and_log(url);if(blocked){proxy_error(fd,blocked==1?403:502);return 0;}
    char host[128],path[2048];const char *slash=strchr(url+7,'/');
    size_t hn=slash?(size_t)(slash-(url+7)):strlen(url+7);
    if(hn>=sizeof(host)){proxy_error(fd,502);return -1;}
    memcpy(host,url+7,hn);host[hn]=0;strcpy(path,slash?slash:"/");
    int port=80;char *colon=strchr(host,':');
    if(colon){*colon++=0;char *end;long p=strtol(colon,&end,10);if(!*colon||*end||p<1||p>65535){proxy_error(fd,502);return -1;}port=(int)p;}
    if(strcmp(host,"127.0.0.1") && strcmp(host,"localhost")){proxy_error(fd,403);return 0;}
    int upstream=socket(AF_INET,SOCK_STREAM,0);if(upstream<0){proxy_error(fd,502);return -1;}
    socket_deadline(upstream);struct sockaddr_in address;memset(&address,0,sizeof(address));
    address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);address.sin_port=htons((unsigned short)port);
    int flags=fcntl(upstream,F_GETFL,0);if(flags<0 || fcntl(upstream,F_SETFL,flags|O_NONBLOCK)<0){close(upstream);return -1;}
    int rc=connect(upstream,(struct sockaddr *)&address,sizeof(address));
    if(rc<0 && errno==EINPROGRESS){
        int error=0;socklen_t n=sizeof(error);
        rc=io_ready(upstream,POLLOUT,now_ms()+2000) && !getsockopt(upstream,SOL_SOCKET,SO_ERROR,&error,&n) && !error?0:-1;
    }
    if(rc<0 || fcntl(upstream,F_SETFL,flags)<0){close(upstream);proxy_error(fd,502);return -1;}
    char request[2304];int n=snprintf(request,sizeof(request),"GET %s HTTP/1.0\r\nHost: %s:%d\r\nConnection: close\r\n\r\n",path,host,port);
    if(n<0 || (size_t)n>=sizeof(request) || write_all(upstream,request,(size_t)n)){close(upstream);proxy_error(fd,502);return -1;}
    char response[131072];size_t total=0;long long deadline=now_ms()+2000;
    for(;;){
        if(total==sizeof(response) || !io_ready(upstream,POLLIN,deadline)){close(upstream);proxy_error(fd,502);return -1;}
        ssize_t got=read(upstream,response+total,sizeof(response)-total);
        if(got<0 && errno==EINTR)continue;
        if(got<0){close(upstream);proxy_error(fd,502);return -1;}
        if(!got)break;total+=(size_t)got;
    }
    close(upstream);return write_all(fd,response,total);
}
typedef struct {int fd;const char *root;int proxy;} connection;
static void *serve_thread(void *arg){
    connection *c=arg;socket_deadline(c->fd);
    if(c->proxy)(void)proxy_handle(c->fd);else(void)handle(c->fd,c->root);
    close(c->fd);free(c);return NULL;
}
/* Dynamic bounded pool. Threads never disappear while holding a connection. */
typedef struct {
    int fd[QUEUE_CAPACITY],head,count,live,target,stopping;
    const char *root;pthread_mutex_t lock;pthread_cond_t ready,space;
    pthread_t ids[MAX_THREAD_IDS];int created;
} worker_pool;
static void *pool_worker(void *arg){
    worker_pool *p=arg;
    for(;;){
        pcheck(pthread_mutex_lock(&p->lock));
        while(!p->count && !p->stopping && p->live<=p->target)pcheck(pthread_cond_wait(&p->ready,&p->lock));
        if(!p->count && (p->stopping || p->live>p->target)){
            p->live--;pcheck(pthread_mutex_unlock(&p->lock));return NULL;
        }
        int fd=p->fd[p->head];p->head=(p->head+1)%QUEUE_CAPACITY;p->count--;
        pcheck(pthread_cond_signal(&p->space));pcheck(pthread_mutex_unlock(&p->lock));
        socket_deadline(fd);(void)handle(fd,p->root);close(fd);
        pcheck(pthread_mutex_lock(&p->lock));
        if(!p->count && p->live>1){
            int target=p->live/2;if(target<1)target=1;
            if(target<p->target){fprintf(stderr,"pool shrink target=%d\n",target);p->target=target;}
            pcheck(pthread_cond_broadcast(&p->ready));
        }
        pcheck(pthread_mutex_unlock(&p->lock));
    }
}
static void pool_grow(worker_pool *p,int target){
    if(target>MAX_WORKERS)target=MAX_WORKERS;p->target=target;
    int before=p->live;
    while(p->live<target && p->created<MAX_THREAD_IDS){
        pcheck(pthread_create(&p->ids[p->created++],NULL,pool_worker,p));p->live++;
    }
    if(before!=p->live)fprintf(stderr,"pool grow %d -> %d\n",before,p->live);
}
static void pool_enqueue(worker_pool *p,int fd){
    pcheck(pthread_mutex_lock(&p->lock));
    if(p->count==QUEUE_CAPACITY)pool_grow(p,p->live*2);
    while(p->count==QUEUE_CAPACITY)pcheck(pthread_cond_wait(&p->space,&p->lock));
    p->fd[(p->head+p->count)%QUEUE_CAPACITY]=fd;p->count++;
    if(p->count==QUEUE_CAPACITY)pool_grow(p,p->live*2);
    pcheck(pthread_cond_signal(&p->ready));pcheck(pthread_mutex_unlock(&p->lock));
}
typedef struct {
    int fd,eof;char in[CH11_REQUEST_LIMIT];size_t used;
    char *out;size_t length,sent;long long deadline;
} event_client;
static void event_close(event_client *c){close(c->fd);free(c->out);memset(c,0,sizeof(*c));c->fd=-1;}
/* Owns listener, including closing it when accepting ends. stop is an absolute
 * acceptance deadline, independent of existing clients' progress deadlines. */
static int event_loop(int listener,const char *root,int limit,int echo,long long stop){
    event_client c[MAX_CLIENTS];memset(c,0,sizeof(c));for(int i=0;i<MAX_CLIENTS;++i)c[i].fd=-1;
    int accepted=0,active=0,commands=echo;
    char command[1024];size_t command_used=0;
    for(;;){
        if(listener>=0 && (accepted>=limit || now_ms()>=stop)){close(listener);listener=-1;}
        if(listener<0 && !active)break;
        fd_set rd,wr;FD_ZERO(&rd);FD_ZERO(&wr);int maximum=-1;
        if(listener>=0){FD_SET(listener,&rd);maximum=listener;}
        if(commands){FD_SET(STDIN_FILENO,&rd);if(STDIN_FILENO>maximum)maximum=STDIN_FILENO;}
        for(int i=0;i<MAX_CLIENTS;++i)if(c[i].fd>=0){
            event_client *x=&c[i];
            if(now_ms()>=x->deadline){event_close(x);active--;continue;}
            if(!x->out){
                size_t expected=0;int ready=0;
                if(echo){char *nl=memchr(x->in,'\n',x->used);expected=nl?(size_t)(nl-x->in)+1:x->used;ready=nl!=NULL || (x->eof && x->used);}
                else ready=request_ready(x->in,x->used) || x->eof;
                if(ready){
                    if(echo){x->out=malloc(expected);if(x->out)memcpy(x->out,x->in,expected);x->length=expected;memmove(x->in,x->in+expected,x->used-expected);x->used-=expected;}
                    else {if(build_response(x->in,x->used,root,&x->out,&x->length))x->out=NULL;}
                    if(!x->out){event_close(x);active--;continue;}
                }else if(x->eof || x->used==sizeof(x->in)){event_close(x);active--;continue;}
            }
            if(x->out)FD_SET(x->fd,&wr);else FD_SET(x->fd,&rd);
            if(x->fd>maximum)maximum=x->fd;
        }
        if(listener<0 && !active)break;
        struct timeval wait={0,100000};int ready=select(maximum+1,&rd,&wr,NULL,&wait);
        if(ready<0){if(errno==EINTR)continue;break;}
        /* The readiness wait may cross stop; recheck before any accept. */
        if(listener>=0 && now_ms()>=stop){close(listener);listener=-1;}
        if(commands && FD_ISSET(STDIN_FILENO,&rd)){
            char input[256];ssize_t n=read(STDIN_FILENO,input,sizeof(input));
            if(n<=0)commands=0;
            else for(ssize_t k=0;k<n;++k){
                if(command_used+1<sizeof(command))command[command_used++]=input[k];
                if(input[k]=='\n'){command[command_used]=0;printf("command: %s",command);fflush(stdout);command_used=0;}
            }
        }
        if(listener>=0 && FD_ISSET(listener,&rd)){
            int fd=accept(listener,NULL,NULL);if(fd>=0){
                int flags=fcntl(fd,F_GETFL,0);
                if(fd>=FD_SETSIZE || flags<0 || fcntl(fd,F_SETFL,flags|O_NONBLOCK)<0){close(fd);continue;}
                int i;for(i=0;i<MAX_CLIENTS && c[i].fd>=0;++i){}
                if(i==MAX_CLIENTS){close(fd);continue;}
                c[i].fd=fd;c[i].deadline=now_ms()+3000;accepted++;active++;
            }
        }
        int echoed=0;
        for(int i=0;i<MAX_CLIENTS;++i)if(c[i].fd>=0){
            event_client *x=&c[i];
            if(FD_ISSET(x->fd,&rd)){
                ssize_t n=read(x->fd,x->in+x->used,sizeof(x->in)-x->used);
                if(n>0){x->used+=(size_t)n;x->deadline=now_ms()+3000;}
                else if(!n)x->eof=1;
                else if(errno!=EAGAIN && errno!=EWOULDBLOCK && errno!=EINTR){event_close(x);active--;continue;}
            }
            if(x->fd>=0 && x->out && FD_ISSET(x->fd,&wr) && (!echo || !echoed)){
                ssize_t n=write(x->fd,x->out+x->sent,x->length-x->sent);
                if(n>0){x->sent+=(size_t)n;echoed=1;}
                else if(n<0 && errno!=EAGAIN && errno!=EWOULDBLOCK && errno!=EINTR){event_close(x);active--;continue;}
                if(x->sent==x->length){
                    if(!echo){event_close(x);active--;}
                    else{free(x->out);x->out=NULL;x->sent=x->length=0;}
                }
            }
        }
    }
    if(listener>=0)close(listener);
    for(int i=0;i<MAX_CLIENTS;++i)if(c[i].fd>=0)event_close(&c[i]);
    return accepted==limit?0:1;
}
/* The regression harness names this entry separately to call event_loop. */
#ifndef CH12_SERVER_MAIN
#define CH12_SERVER_MAIN main
#endif
int CH12_SERVER_MAIN(int argc,char **argv){
    if(argc==1){puts("usage: ch12_servers --serve process|select|thread|pool|echo|proxy|proxy-serial ROOT PORT LIMIT [FILTER LOG]");return 0;}
    if((argc!=6 && argc!=8)||strcmp(argv[1],"--serve"))return 2;
    const char *mode=argv[2],*root=argv[3];char *end;long port=strtol(argv[4],&end,10);
    if(!*argv[4]||*end||port<0||port>65535)return 2;
    long limit=strtol(argv[5],&end,10);if(!*argv[5]||*end||limit<1||limit>MAX_CLIENTS)return 2;
    int proxy=!strcmp(mode,"proxy")||!strcmp(mode,"proxy-serial");
    if(strcmp(mode,"process")&&strcmp(mode,"select")&&strcmp(mode,"thread")&&strcmp(mode,"pool")&&strcmp(mode,"echo")&&!proxy)return 2;
    if(proxy){if(argc!=8)return 2;filter_path=argv[6];log_path=argv[7];}
    (void)signal(SIGPIPE,SIG_IGN);int listener=listen_loopback((int)port);if(listener<0)return 1;
    if(listener>=FD_SETSIZE){close(listener);return 1;}
    if(!strcmp(mode,"select")||!strcmp(mode,"echo")){
        return event_loop(listener,root,(int)limit,!strcmp(mode,"echo"),now_ms()+120000);
    }
    if(!strcmp(mode,"process")){
        struct sigaction action;memset(&action,0,sizeof(action));action.sa_handler=child_handler;
        sigemptyset(&action.sa_mask);action.sa_flags=SA_RESTART;
        if(sigaction(SIGCHLD,&action,NULL)){close(listener);return 1;}
    }
    pthread_t ids[MAX_CLIENTS];pid_t children[MAX_CLIENTS];int count=0;
    worker_pool pool={.root=root,.lock=PTHREAD_MUTEX_INITIALIZER,.ready=PTHREAD_COND_INITIALIZER,.space=PTHREAD_COND_INITIALIZER};
    if(!strcmp(mode,"pool")){pcheck(pthread_mutex_lock(&pool.lock));pool_grow(&pool,1);pcheck(pthread_mutex_unlock(&pool.lock));}
    long long stop=now_ms()+120000;
    while(count<limit && io_ready(listener,POLLIN,stop)){
        int fd=accept(listener,NULL,NULL);if(fd<0){if(errno==EINTR||errno==EAGAIN||errno==EWOULDBLOCK)continue;break;}socket_deadline(fd);
        if(!strcmp(mode,"process")){
            pid_t pid=fork();
            if(!pid){close(listener);int rc=handle(fd,root);close(fd);_exit(rc?1:0);}
            close(fd);if(pid<0)break;children[count]=pid;
        }else if(!strcmp(mode,"pool"))pool_enqueue(&pool,fd);
        else if(!strcmp(mode,"proxy-serial")){(void)proxy_handle(fd);close(fd);}
        else{
            connection *c=malloc(sizeof(*c));if(!c){close(fd);break;}
            *c=(connection){fd,root,proxy};int e=pthread_create(&ids[count],NULL,serve_thread,c);
            if(e){close(fd);free(c);break;}
        }
        count++;
    }
    close(listener);
    if(!strcmp(mode,"process")){
        for(int i=0;i<count;++i)while(waitpid(children[i],NULL,0)<0 && errno==EINTR){}
    }else if(!strcmp(mode,"pool")){
        pcheck(pthread_mutex_lock(&pool.lock));pool.stopping=1;pcheck(pthread_cond_broadcast(&pool.ready));pcheck(pthread_mutex_unlock(&pool.lock));
        for(int i=0;i<pool.created;++i)pcheck(pthread_join(pool.ids[i],NULL));
        pcheck(pthread_mutex_destroy(&pool.lock));pcheck(pthread_cond_destroy(&pool.ready));pcheck(pthread_cond_destroy(&pool.space));
    }else if(strcmp(mode,"proxy-serial")){for(int i=0;i<count;++i)pcheck(pthread_join(ids[i],NULL));}
    return count==limit?0:1;
}
