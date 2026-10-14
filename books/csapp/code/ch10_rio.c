#define _POSIX_C_SOURCE 200809L
/* C11 + POSIX. Blocking descriptors; valid storage of at least n bytes.
 * Default: deterministic injected I/O plus a real pipe check.
 * --copy [FILE]: binary copy; --lines [FILE]: line-buffered byte copy.
 * EINTR injection checks the loop, not host signal delivery. */
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef ssize_t (*reader)(void *, void *, size_t);
typedef ssize_t (*writer)(void *, const void *, size_t);
typedef struct { reader get; void *ctx; size_t pos, count; unsigned char buf[8]; } Rio;

static ssize_t fd_read(void *p, void *b, size_t n) { return read(*(int *)p, b, n); }
static ssize_t fd_write(void *p, const void *b, size_t n) { return write(*(int *)p, b, n); }

static ssize_t readn(reader get, void *ctx, void *buf, size_t n) {
    unsigned char *p = buf;
    size_t done = 0;
    if (n > (size_t)SSIZE_MAX) { errno = EINVAL; return -1; }
    while (done < n) {
        ssize_t k = get(ctx, p + done, n - done);
        if (k < 0) { if (errno == EINTR) continue; return -1; }
        if (k == 0) break;
        done += (size_t)k;
    }
    return (ssize_t)done;
}

static ssize_t writen(writer put, void *ctx, const void *buf, size_t n) {
    const unsigned char *p = buf;
    size_t done = 0;
    if (n > (size_t)SSIZE_MAX) { errno = EINVAL; return -1; }
    while (done < n) {
        ssize_t k = put(ctx, p + done, n - done);
        if (k < 0) { if (errno == EINTR) continue; return -1; }
        if (k == 0) { errno = EIO; return -1; }
        done += (size_t)k;
    }
    return (ssize_t)done;
}

static ssize_t buffered_read(void *ctx, void *buf, size_t n) {
    Rio *r = ctx;
    if (n == 0) return 0;
    while (r->count == 0) {
        ssize_t k = r->get(r->ctx, r->buf, sizeof r->buf);
        if (k < 0) { if (errno == EINTR) continue; return -1; }
        if (k == 0) return 0;
        r->pos = 0;
        r->count = (size_t)k;
    }
    if (n > r->count) n = r->count;
    memcpy(buf, r->buf + r->pos, n);
    r->pos += n;
    r->count -= n;
    return (ssize_t)n;
}

static ssize_t readlineb(Rio *r, void *buf, size_t capacity) {
    unsigned char *p = buf;
    size_t done = 0;
    /* Unlike the textbook, reject capacities that cannot transfer a byte. */
    if (capacity < 2 || capacity - 1 > (size_t)SSIZE_MAX) { errno = EINVAL; return -1; }
    while (done < capacity - 1) {
        ssize_t k = buffered_read(r, p + done, 1);
        if (k < 0) return -1;
        if (k == 0) break;
        if (p[done++] == '\n') break;
    }
    p[done] = 0;
    return (ssize_t)done;
}

typedef struct {
    const unsigned char *src;
    size_t length, offset;
    const int *steps;
    size_t nsteps, next, calls;
    unsigned char output[64];
} Script;

static ssize_t scripted(void *ctx, void *buf, size_t n) {
    Script *s = ctx;
    ++s->calls;
    int k = s->next < s->nsteps ? s->steps[s->next++] : 64;
    if (k < 0) { errno = -k; return -1; }
    if (n > (size_t)k) n = (size_t)k;
    if (n > s->length - s->offset) n = s->length - s->offset;
    memcpy(buf, s->src + s->offset, n);
    s->offset += n;
    return (ssize_t)n;
}

static ssize_t scripted_write(void *ctx, const void *buf, size_t n) {
    Script *s = ctx;
    ++s->calls;
    int k = s->next < s->nsteps ? s->steps[s->next++] : 64;
    if (k < 0) { errno = -k; return -1; }
    if (n > (size_t)k) n = (size_t)k;
    if (n > sizeof s->output - s->offset) { errno = ENOSPC; return -1; }
    memcpy(s->output + s->offset, buf, n);
    s->offset += n;
    return (ssize_t)n;
}

static int require(int condition, const char *name) {
    if (condition) return 1;
    fprintf(stderr, "failed: %s\n", name);
    return 0;
}

static int selftest(void) {
    const unsigned char bytes[] = {'A', 0, 'B', '\n', 'C', 'D'};
    const int steps[] = {-EINTR, 2, 1, 3};
    Script s = {bytes, sizeof bytes, 0, steps, 4, 0, 0, {0}};
    unsigned char b[16];
    if (!require(readn(scripted, &s, b, 9) == 6 && !memcmp(b, bytes, 6), "short/EINTR/EOF")) return 1;
    if (!require(s.calls == 5, "retry and EOF calls")) return 1;
    printf("readn short+EINTR+EOF bytes=6 calls=5\n");
    size_t calls = s.calls;
    if (!require(readn(scripted, &s, b, 0) == 0 && s.calls == calls, "zero request")) return 1;
    Script w = {NULL, 0, 0, steps, 4, 0, 0, {0}};
    if (!require(writen(scripted_write, &w, bytes, 6) == 6 && !memcmp(w.output, bytes, 6), "short write")) return 1;
    printf("writen short+EINTR bytes=6 calls=4\n");
    const int fail[] = {2, -EIO};
    s = (Script){bytes, 6, 0, fail, 2, 0, 0, {0}};
    if (!require(readn(scripted, &s, b, 6) == -1 && errno == EIO && s.offset == 2, "partial then error")) return 1;
    const int zero[] = {0};
    w = (Script){NULL, 0, 0, zero, 1, 0, 0, {0}};
    if (!require(writen(scripted_write, &w, bytes, 6) == -1 && errno == EIO, "zero write fails")) return 1;
    const int again[] = {-EAGAIN};
    s = (Script){bytes, 6, 0, again, 1, 0, 0, {0}};
    if (!require(readn(scripted, &s, b, 6) == -1 && errno == EAGAIN && s.calls == 1, "nonblocking error")) return 1;
    printf("errors partial=2 zero-write=EIO nonblocking=EAGAIN\n");
    const unsigned char mixed[] = {'h','i','\n',0,'X','\n','Y','Z','Q'};
    s = (Script){mixed, sizeof mixed, 0, NULL, 0, 0, 0, {0}};
    Rio r = {scripted, &s, 0, 0, {0}};
    if (!require(readlineb(&r, b, sizeof b) == 3 && !memcmp(b,"hi\n",3) && r.count == 5 && s.offset == 8, "buffer ahead")) return 1;
    if (!require(readn(buffered_read, &r, b, 4) == 4 && !memcmp(b,mixed+3,4), "mixed body")) return 1;
    if (!require(readlineb(&r,b,sizeof b) == 2 && !memcmp(b,"ZQ",2) && readlineb(&r,b,sizeof b) == 0, "partial final line")) return 1;
    printf("buffer mixed line=3 body=4 tail=2 retained-after-line=5\n");
    s = (Script){(const unsigned char *)"abcde\n", 6, 0, NULL, 0, 0, 0, {0}};
    r = (Rio){scripted, &s, 0, 0, {0}};
    if (!require(readlineb(&r,b,4)==3 && !memcmp(b,"abc",3) && readlineb(&r,b,4)==3 && !memcmp(b,"de\n",3),"long line chunks")) return 1;
    if (!require(readlineb(&r,b,1)==-1 && errno==EINVAL, "capacity boundary")) return 1;
    printf("long-line fragments=abc|de\\n capacity1=EINVAL\n");
    int fds[2];
    if (pipe(fds) < 0) { perror("pipe"); return 1; }
    if (writen(fd_write,&fds[1],bytes,6)!=6 || close(fds[1])<0) { perror("pipe write"); close(fds[0]); return 1; }
    ssize_t n = readn(fd_read,&fds[0],b,sizeof b);
    int closed = close(fds[0]);
    if (!require(n==6 && !memcmp(b,bytes,6) && closed==0,"real pipe")) return 1;
    printf("host-pipe binary=6 EOF=observed\n");
    return 0;
}

static int copy(int lines, const char *filename) {
    int in = STDIN_FILENO, out = STDOUT_FILENO;
    if (filename) {
        int fd = open(filename,O_RDONLY);
        if (fd < 0) { perror("open"); return 1; }
        if (fd != in) {
            if (dup2(fd,in)<0) { perror("dup2"); close(fd); return 1; }
            if (close(fd)<0) { perror("close"); return 1; }
        }
    }
    Rio r = {fd_read,&in,0,0,{0}};
    unsigned char buf[8192];
    ssize_t n;
    while ((n = lines ? readlineb(&r,buf,sizeof buf) : readn(buffered_read,&r,buf,sizeof buf)) > 0)
        if (writen(fd_write,&out,buf,(size_t)n)<0) { perror("write"); return 1; }
    if (n<0) { perror("read"); return 1; }
    return 0;
}

int main(int argc,char **argv) {
    if (argc==1) return selftest();
    if ((argc==2 || argc==3) && (!strcmp(argv[1],"--copy") || !strcmp(argv[1],"--lines")))
        return copy(!strcmp(argv[1],"--lines"),argc==3 ? argv[2] : NULL);
    fprintf(stderr,"usage: ch10_rio [--copy|--lines [FILE]]\n");
    return 2;
}
