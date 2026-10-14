#define _POSIX_C_SOURCE 200809L
/* C11 + POSIX host experiment. Only the mkstemp-created file is modified.
 * --list DIR reads a directory; order is not promised. */
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

static int byte(int fd, char *c) {
    ssize_t n;
    do { n=read(fd,c,1); } while (n<0 && errno==EINTR);
    return n==1;
}
static int list(const char *path) {
    DIR *dir=opendir(path);
    if (!dir) { perror("opendir"); return 1; }
    int failed=0;
    for (;;) {
        errno=0;
        struct dirent *entry=readdir(dir);
        if (!entry) { if (errno) { perror("readdir"); failed=1; } break; }
        if (printf("%s\n",entry->d_name)<0) { failed=1; break; }
    }
    if (closedir(dir)<0) { perror("closedir"); failed=1; }
    if (fflush(stdout)==EOF) { perror("stdout"); failed=1; }
    return failed;
}
static int experiment(void) {
    char path[]="/tmp/csapp-ch10-XXXXXX";
    int a=mkstemp(path), b=-1, failed=1;
    char independent='?', shared='?', inherited='?';
    if (a<0) { perror("mkstemp"); return 1; }
    if (write(a,"foobar",6)!=6 || lseek(a,0,SEEK_SET)<0) goto done;
    b=open(path,O_RDONLY);
    if (b<0) goto done;
    char first;
    if (!byte(a,&first) || first!='f' || !byte(b,&independent) || independent!='f') goto done;
    if (dup2(b,a)!=a || !byte(a,&shared) || shared!='o') goto done;
    if (lseek(a,0,SEEK_SET)<0) goto done;
    pid_t child=fork();
    if (child<0) goto done;
    if (child==0) {
        char c;
        int ok=byte(a,&c) && c=='f';
        if (close(a)<0 || close(b)<0) ok=0;
        _exit(ok ? 0 : 1);
    }
    int status;
    pid_t got;
    do { got=waitpid(child,&status,0); } while (got<0 && errno==EINTR);
    if (got!=child || !WIFEXITED(status) || WEXITSTATUS(status)!=0) goto done;
    if (!byte(a,&inherited) || inherited!='o') goto done;
    struct stat st;
    if (fstat(a,&st)<0 || !S_ISREG(st.st_mode) || st.st_size!=6) goto done;
    if (printf("independent=%c dup2-shared=%c fork-shared=%c\n",independent,shared,inherited)<0) goto done;
    if (printf("metadata regular=yes size=6 shared-offset=2\n")<0) goto done;
    /* A duplicate keeps the open file description alive after a is closed. */
    if (close(a)<0) { a=-1; goto done; }
    a=-1;
    if (!byte(b,&first) || first!='o') goto done;
    if (printf("close-one remaining-byte=o\n")<0) goto done;
    failed=0;
done:
    if (a>=0 && close(a)<0) failed=1;
    if (b>=0 && close(b)<0) failed=1;
    if (unlink(path)<0) failed=1;
    if (fflush(stdout)==EOF) failed=1;
    if (failed) fprintf(stderr,"file experiment failed\n");
    return failed;
}
int main(int argc,char **argv) {
    if (argc==1) return experiment();
    if (argc==3 && !strcmp(argv[1],"--list")) return list(argv[2]);
    fprintf(stderr,"usage: ch10_files [--list DIR]\n");
    return 2;
}
