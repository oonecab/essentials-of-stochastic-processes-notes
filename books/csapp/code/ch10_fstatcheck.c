#define _POSIX_C_SOURCE 200809L
/* Exercise 10.8: inherited descriptor, not a filename. */
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
int main(int argc,char **argv) {
    if (argc!=2 || argv[1][0]<'0' || argv[1][0]>'9') {
        fprintf(stderr,"usage: ch10_fstatcheck FD\n");
        return 2;
    }
    char *end;
    errno=0;
    long value=strtol(argv[1],&end,10);
    if (errno==ERANGE || *end || value>INT_MAX) {
        fprintf(stderr,"invalid descriptor\n");
        return 2;
    }
    struct stat st;
    if (fstat((int)value,&st)<0) { perror("fstat"); return 1; }
    const char *type=S_ISREG(st.st_mode) ? "regular" : S_ISDIR(st.st_mode) ? "directory" : "other";
    /* The owner's read bit is not an effective-access authorization test. */
    if (printf("type: %s, read: %s\n",type,(st.st_mode&S_IRUSR) ? "yes" : "no")<0 || fflush(stdout)==EOF) {
        perror("stdout");
        return 1;
    }
    return 0;
}
