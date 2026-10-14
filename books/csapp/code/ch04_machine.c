/* Bounded little-endian Y86-64 ISA model, not a PIPE circuit simulator. */
#include <stdbool.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

enum { SIZE = 4096, NONE = 15, RSP = 4 };
typedef struct { bool z, s, o; } CC;
typedef struct {
    unsigned char mem[SIZE]; uint64_t reg[15], pc;
    CC cc; const char *stat; unsigned steps, loads, misses, rets, previous_load;
} Machine;
typedef struct { bool f, ds, db, eb, mb, ws; } Control;
static bool member(unsigned x, unsigned bits) { return (bits & (1u << x)) != 0; }
static bool condition(unsigned f, CC c) {
    const bool values[] = {true, (c.s != c.o) || c.z, c.s != c.o, c.z,
                           !c.z, c.s == c.o, (c.s == c.o) && !c.z};
    return values[f];
}
static uint64_t alu(unsigned fn, uint64_t a, uint64_t b, CC *cc) {
    const uint64_t r = fn == 0 ? b + a : fn == 1 ? b - a : fn == 2 ? b & a : b ^ a;
    const bool sa = (a >> 63) != 0, sb = (b >> 63) != 0, sr = (r >> 63) != 0;
    *cc = (CC){r == 0, sr, fn == 0 ? sa == sb && sr != sb : fn == 1 && sa != sb && sr != sb};
    return r;
}
static uint64_t word(const Machine *m, uint64_t a) {
    uint64_t v = 0;
    for (unsigned i = 0; i < 8; ++i) v |= (uint64_t)m->mem[a + i] << (8 * i);
    return v;
}
static void put_word(Machine *m, uint64_t a, uint64_t v) {
    for (unsigned i = 0; i < 8; ++i) m->mem[a + i] = (unsigned char)(v >> (8 * i));
}
static Control control(bool l, bool b, bool r, bool m, bool w) {
    return (Control){l || r, l, b || (r && !l), l || b, m || w, w};
}
static uint64_t forward(unsigned src, uint64_t raw, const unsigned dst[5], const uint64_t val[5]) {
    for (unsigned i = 0; i < 5; ++i) if (src != NONE && src == dst[i]) return val[i];
    return raw;
}
static unsigned check_logic(void) {
    unsigned checks = 0;
    for (unsigned bits = 0; bits < 32; ++bits) {
        const bool l = (bits & 1) != 0, b = (bits & 2) != 0, r = (bits & 4) != 0;
        const bool m = (bits & 8) != 0, w = (bits & 16) != 0;
        if (l && b) continue;
        const Control c = control(l, b, r, m, w);
        if ((c.ds && c.db) || (l && !(c.f && c.ds && c.eb)) || c.mb != (m || w) || c.ws != w) return 0;
        ++checks;
    }
    const unsigned d1[5] = {15,4,4,15,15}, d2[5] = {2,15,2,15,15};
    const uint64_t v1[5] = {0,5,264,0,0}, v2[5] = {3,0,10,0,0};
    return forward(4,0,d1,v1) == 5 && forward(2,0,d2,v2) == 3 ? checks : 0;
}
static void step(Machine *m) {
    const uint64_t p = m->pc;
    if (p >= SIZE) { m->stat = "ADR"; return; }
    const unsigned op = m->mem[p] >> 4, fn = m->mem[p] & 15;
    if (op > 12 || fn > (op == 2 || op == 7 ? 6u : op == 6 ? 3u : 0u)) { m->stat = "INS"; return; }
    const bool nr = member(op, 0x1c7c), nc = member(op, 0x11b8);
    const unsigned len = 1 + (unsigned)nr + 8 * (unsigned)nc;
    if (p > SIZE - len) { m->stat = "ADR"; return; }
    const unsigned a = nr ? m->mem[p + 1] >> 4 : NONE, b = nr ? m->mem[p + 1] & 15 : NONE;
    const bool good = member(op, 0x74) ? a < NONE && b < NONE :
                      member(op, 0x1008) ? a == NONE && b < NONE :
                      member(op, 0xc00) ? a < NONE && b == NONE : true;
    if (!good) { m->stat = "INS"; return; }
    const uint64_t c = nc ? word(m, p + 1 + (unsigned)nr) : 0;
    const unsigned sa = member(op,0x454) ? a : member(op,0xa00) ? RSP : NONE;
    const unsigned sb = member(op,0x1070) ? b : member(op,0xf00) ? RSP : NONE;
    const uint64_t va = sa == NONE ? 0 : m->reg[sa], vb = sb == NONE ? 0 : m->reg[sb];
    unsigned de = member(op,0x104c) ? b : member(op,0xf00) ? RSP : NONE;
    const unsigned dm = member(op,0x820) ? a : NONE;
    const uint64_t aa = member(op,0x44) ? va : member(op,0x1038) ? c :
                        member(op,0x500) ? UINT64_MAX - 7 : member(op,0xa00) ? 8 : 0;
    CC newcc;
    const uint64_t ve = alu(op == 6 ? fn : 0, aa, vb, &newcc);
    const bool taken = op == 2 || op == 7 ? condition(fn,m->cc) : true;
    if (op == 2 && !taken) de = NONE;
    const bool read = member(op,0xa20), write = member(op,0x510);
    const uint64_t addr = member(op,0xa00) ? va : ve;
    if ((read || write) && addr > SIZE - 8) { m->stat = "ADR"; return; }
    const uint64_t vm = read ? word(m,addr) : 0;
    const uint64_t nextpc = op == 8 || (op == 7 && taken) ? c : op == 9 ? vm : p + len;
    if (m->previous_load != NONE && (m->previous_load == sa || m->previous_load == sb)) ++m->loads;
    m->previous_load = dm;
    ++m->steps;
    if (op == 7 && !taken) ++m->misses;
    if (op == 9) ++m->rets;
    if (op == 0) { m->stat = "HLT"; return; }
    if (write) put_word(m,addr,op == 8 ? p + len : va);
    if (de != NONE) m->reg[de] = ve;
    if (dm != NONE) m->reg[dm] = vm; /* M write wins for popq %rsp. */
    if (op == 6 || op == 12) m->cc = newcc;
    m->pc = nextpc;
}
static void report(const Machine *m) {
    static const char *const names[] = {"rax","rcx","rdx","rbx","rsp","rbp","rsi","rdi",
                                       "r8","r9","r10","r11","r12","r13","r14"};
    printf("steps=%u status=%s pc=0x%03" PRIx64 " cc=%d%d%d\n",m->steps,m->stat,m->pc,m->cc.z,m->cc.s,m->cc.o);
    printf("load-use=%u mispredict=%u ret=%u\n",m->loads,m->misses,m->rets);
    for (unsigned i = 0; i < 15; ++i) printf("%s=0x%016" PRIx64 "\n",names[i],m->reg[i]);
    uint64_t digest = UINT64_C(14695981039346656037);
    for (unsigned i = 0; i < SIZE; ++i) digest = (digest ^ m->mem[i]) * UINT64_C(1099511628211);
    printf("memory-fnv64=%016" PRIx64 "\n",digest);
}
int main(int argc, char **argv) {
    static const char demo[] = "30f2090000000000000030f315000000000000006123"
        "30f4800000000000000040436400000000000000a02fb00f"
        "7340000000000000008041000000000000000090";
    Machine m = {.cc={true,false,false}, .stat="AOK", .previous_load=NONE};
    if (argc > 2) { fputs("usage: ch04_machine [image.bin]\n",stderr); return 2; }
    if (argc == 2) {
        FILE *f = fopen(argv[1],"rb");
        if (!f) { perror("image"); return 2; }
        (void)fread(m.mem,1,SIZE,f);
        const int more = fgetc(f);
        const bool bad = more != EOF || ferror(f);
        fclose(f);
        if (bad) { fputs("image exceeds 4096 bytes or read failed\n",stderr); return 2; }
    } else {
        for (unsigned i = 0; i < (sizeof demo - 1) / 2; ++i) {
            unsigned byte;
            if (sscanf(demo + 2 * i,"%2x",&byte) != 1) return 2;
            m.mem[i] = (unsigned char)byte;
        }
    }
    const unsigned checks = check_logic();
    if (checks == 0) { fputs("control self-check failed\n",stderr); return 2; }
    printf("control-cases=%u forwarding-cases=2\n",checks);
    while (strcmp(m.stat,"AOK") == 0 && m.steps < 1000000) step(&m);
    if (strcmp(m.stat,"AOK") == 0) { fputs("instruction limit exceeded\n",stderr); return 2; }
    report(&m);
    return 0;
}
