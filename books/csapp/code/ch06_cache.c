/* Configurable LRU trace model. A line stores tags/state, not actual data. */
#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct line { uint64_t tag, age; bool valid, dirty; };
struct cache {
    size_t sets, ways, block; bool wb, wa; struct line *lines;
    uint64_t clock, operations, hits, misses, evictions, writebacks;
    uint64_t read_bytes, write_bytes;
};
static bool number(const char *s, int base, uint64_t *value) {
    if (!*s || *s == '-' || *s == '+') return false;
    char *end; errno = 0; uintmax_t v = strtoumax(s, &end, base);
    if (errno || *end || v > UINT64_MAX) return false;
    *value = (uint64_t)v; return true;
}
static bool access_cache(struct cache *c, char op, uint64_t a, uint64_t size) {
    if ((op != 'R' && op != 'W') || !size || size > 4096 || a > UINT64_MAX-size+1) return false;
    ++c->operations;
    while (size) {
        uint64_t count = c->block-a%c->block;
        if (count > size) count = size;
        uint64_t block = a/c->block, tag = block/c->sets;
        struct line *row = c->lines + (block%c->sets)*c->ways, *item = NULL;
        ++c->clock;
        for (size_t i=0; i<c->ways; ++i)
            if (row[i].valid && row[i].tag == tag) { item = row+i; break; }
        if (item) ++c->hits;
        else {
            ++c->misses;
            if (op == 'W' && !c->wa) { c->write_bytes += count; a += count; size -= count; continue; }
            item = row;
            for (size_t i=0; i<c->ways; ++i) {
                if (!row[i].valid) { item=row+i; break; }
                if (row[i].age < item->age) item=row+i;
            }
            if (item->valid) {
                ++c->evictions;
                if (item->dirty) { ++c->writebacks; c->write_bytes += c->block; }
            }
            c->read_bytes += c->block;
            *item = (struct line){.tag=tag,.valid=true};
        }
        item->age = c->clock;
        if (op == 'W') { if (c->wb) item->dirty=true; else c->write_bytes+=count; }
        a += count; size -= count;
    }
    return true;
}
int main(int argc, char **argv) {
    uint64_t v[5]={4,1,2,1,1};
    if (argc != 1 && argc != 7) return 2;
    if (argc == 7) for (int i=0; i<5; ++i) if (!number(argv[i+1],10,v+i)) return 2;
    if (!v[0] || (v[0]&(v[0]-1)) || !v[1] || v[1]>1048576 || v[0]>1048576/v[1] ||
        !v[2] || v[2]>1048576 || (v[2]&(v[2]-1)) || v[3]>1 || v[4]>1) return 2;
    struct cache c={.sets=(size_t)v[0],.ways=(size_t)v[1],.block=(size_t)v[2],.wb=v[3]!=0,.wa=v[4]!=0};
    c.lines=calloc(c.sets*c.ways,sizeof *c.lines); if (!c.lines) return 2;
    bool ok=true;
    if (argc==1) {
        uint64_t a[]={0,1,13,8,0};
        for (size_t i=0; i<sizeof a/sizeof *a; ++i) ok=access_cache(&c,'R',a[i],1)&&ok;
    } else {
        FILE *f=fopen(argv[6],"r"); if (!f) { free(c.lines); return 2; }
        char text[256],op[2],addr[80],size[80],extra;
        while (ok && fgets(text,sizeof text,f)) {
            uint64_t a,n;
            ok=sscanf(text,"%1s %79s %79s %c",op,addr,size,&extra)==3 &&
               strncmp(addr,"0x",2)==0 && number(addr,16,&a) && number(size,10,&n) && access_cache(&c,op[0],a,n);
        }
        if (ferror(f)) ok=false;
        fclose(f);
    }
    if (ok) {
        uint64_t dirty=0;
        for (size_t i=0;i<c.sets*c.ways;++i) dirty+=c.lines[i].dirty;
        printf("operations=%"PRIu64" hits=%"PRIu64" misses=%"PRIu64" evictions=%"PRIu64" writebacks=%"PRIu64"\n",c.operations,c.hits,c.misses,c.evictions,c.writebacks);
        printf("read_bytes=%"PRIu64" write_bytes=%"PRIu64" dirty_lines=%"PRIu64"\n",c.read_bytes,c.write_bytes,dirty);
    }
    free(c.lines); return ok?0:2;
}
