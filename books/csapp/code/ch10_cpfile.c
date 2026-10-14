#define _POSIX_C_SOURCE 200809L
/* Exercise 10.10. Reuse the verified Rio implementation without its CLI main.
 * Capitalized wrappers terminate on error, as in the textbook csapp library.
 * Lines from Figure 10.5 retain their original declarations and copy loop. */
#define main ch10_rio_demonstration_main
#include "ch10_rio.c"
#undef main
#define MAXLINE 8192
typedef struct { Rio inner; int descriptor; } rio_t;
static void die(const char *what) { perror(what); exit(1); }
static int Open(const char *name,int flags,mode_t mode) {
    int fd=open(name,flags,mode);
    if (fd<0) die("open");
    return fd;
}
static void Dup2(int oldfd,int newfd) { if (dup2(oldfd,newfd)<0) die("dup2"); }
static void Close(int fd) { if (close(fd)<0) die("close"); }
static void Rio_readinitb(rio_t *r,int fd) {
    r->descriptor=fd;
    r->inner=(Rio){fd_read,&r->descriptor,0,0,{0}};
}
static int Rio_readlineb(rio_t *r,void *b,size_t n) {
    ssize_t got=readlineb(&r->inner,b,n);
    if (got<0) die("read");
    /* MAXLINE limits this exercise's return count to INT_MAX. */
    if (got>INT_MAX) { errno=EOVERFLOW; die("line length"); }
    return (int)got;
}
static void Rio_writen(int fd,const void *b,int n) {
    if (writen(fd_write,&fd,b,(size_t)n)<0) die("write");
}
int main(int argc, char **argv)
{
    int n;
    rio_t rio;
    char buf[MAXLINE];

    /* Inserted before the unchanged lines 9-11. */
    if (argc>2) {
        fprintf(stderr,"usage: ch10_cpfile [infile]\n");
        return 2;
    }
    if (argc==2) {
        int fd=Open(argv[1],O_RDONLY,0);
        if (fd!=STDIN_FILENO) {
            Dup2(fd,STDIN_FILENO);
            Close(fd);
        }
    }
    /* Original Figure 10.5 copy loop. */
    Rio_readinitb(&rio, STDIN_FILENO);
    while((n = Rio_readlineb(&rio, buf, MAXLINE)) != 0)
        Rio_writen(STDOUT_FILENO, buf, n);
}
