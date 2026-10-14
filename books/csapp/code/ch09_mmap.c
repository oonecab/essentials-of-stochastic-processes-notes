/* POSIX interfaces with C11 syntax. copy FILE or change FILE; empty files work.
 * A bounded mapping window avoids requiring one contiguous map of a huge file.
 * The input file must remain stable (no concurrent truncation). */
#define _POSIX_C_SOURCE 200809L
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static int write_all(const unsigned char *p,size_t n) {
    while(n){ssize_t done=write(STDOUT_FILENO,p,n);if(done<0&&errno==EINTR)continue;
        if(done<=0)return -1;
        p+=(size_t)done;n-=(size_t)done;
    }return 0;
}
static int copy_file(int fd,off_t length) {
    long page=sysconf(_SC_PAGESIZE);if(page<=0 || (uintmax_t)page>SIZE_MAX)return -1;
    size_t chunk=(64u*1024u*1024u)/(size_t)page*(size_t)page;if(!chunk)chunk=(size_t)page;
    for(off_t off=0;off<length;){uintmax_t remaining=(uintmax_t)(length-off);size_t n=remaining<chunk?(size_t)remaining:chunk;
        void *map=mmap(NULL,n,PROT_READ,MAP_PRIVATE,fd,off);if(map==MAP_FAILED)return -1;
        int rc=write_all(map,n),unmap=munmap(map,n);if(rc<0||unmap<0)return -1;
        off+=(off_t)n;
    }return 0;
}
static int change_file(int fd,off_t length) {
    static const char expected[]="Hello, world!\n";
    if(length!=(off_t)(sizeof expected-1)){errno=EINVAL;return -1;}
    unsigned char *map=mmap(NULL,sizeof expected-1,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
    if(map==MAP_FAILED)return -1;
    int rc=0;if(memcmp(map,expected,sizeof expected-1)){errno=EINVAL;rc=-1;}
    else {map[0]='J';if(msync(map,sizeof expected-1,MS_SYNC)<0)rc=-1;}
    int saved=errno;if(munmap(map,sizeof expected-1)<0)rc=-1;else errno=saved;return rc;
}
int main(int argc,char **argv) {
    if(argc==1){puts("usage: ch09_mmap copy FILE | change FILE");return 0;}
    if(argc!=3 || (strcmp(argv[1],"copy")&&strcmp(argv[1],"change")))return 2;
    int fd=open(argv[2],!strcmp(argv[1],"copy")?O_RDONLY:O_RDWR);if(fd<0){perror("open");return 1;}
    struct stat st;int rc=fstat(fd,&st);
    if(rc==0&&(!S_ISREG(st.st_mode)||st.st_size<0)){errno=EINVAL;rc=-1;}
    if(rc==0)rc=!strcmp(argv[1],"copy")?copy_file(fd,st.st_size):change_file(fd,st.st_size);
    if(rc<0)perror("mmap operation");
    if(close(fd)<0)rc=-1;
    return rc<0?1:0;
}
