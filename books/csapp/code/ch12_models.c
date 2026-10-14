/* Sequential C11 state model. It never executes a C data race or blocks on locks.
 * P(x) consumes an available token; V(x) returns it. Explore reachable states.
 * Input is fixed textbook programs: finite binary locks, at most three threads. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int pc[3]; unsigned tokens; } state;
static unsigned char visited[7][7][7][8];
static const char *program[3];
static int threads, lengths[3], deadlocks, finishes;
static void explore(state s) {
    if (visited[s.pc[0]][s.pc[1]][s.pc[2]][s.tokens]) return;
    visited[s.pc[0]][s.pc[1]][s.pc[2]][s.tokens] = 1;
    int enabled = 0, complete = 1;
    for (int t = 0; t < threads; ++t) {
        if (s.pc[t] == lengths[t]) continue;
        complete = 0;
        char op = program[t][s.pc[t]];
        unsigned bit = 1u << (unsigned)((op >= 'a' ? op-'a' : op-'A'));
        int take = op >= 'a';
        if (take && !(s.tokens & bit)) continue;
        if (!take && (s.tokens & bit)) { fputs("non-binary release\n",stderr); exit(1); }
        state next = s; next.pc[t]++;
        next.tokens = take ? s.tokens & ~bit : s.tokens | bit;
        enabled = 1; explore(next);
    }
    if (complete) finishes++;
    else if (!enabled) deadlocks++;
}
static void locks(const char *name, const char *a, const char *b,
                  const char *c, unsigned initial, int expected) {
    program[0]=a;program[1]=b;program[2]=c;threads=c?3:2;
    for (int i=0;i<threads;++i) lengths[i]=(int)strlen(program[i]);
    memset(visited,0,sizeof(visited));deadlocks=finishes=0;
    explore((state){{0,0,0},initial});
    if ((deadlocks>0)!=expected) exit(1);
    printf("%s deadlocks=%d completed=%d\n",name,deadlocks,finishes);
}
static int outcomes[3];
static void counter(int p0,int p1,int r0,int r1,int value) {
    if (p0==3 && p1==3) { outcomes[value]++; return; }
    if (p0<3) counter(p0+1,p1,p0==0?value:p0==1?r0+1:r0,r1,p0==2?r0:value);
    if (p1<3) counter(p0,p1+1,r0,p1==0?value:p1==1?r1+1:r1,p1==2?r1:value);
}
int main(void) {
    counter(0,0,0,0,0);
    if (outcomes[1]!=18 || outcomes[2]!=2) return 1;
    printf("counter schedules=20 final1=%d final2=%d\n",outcomes[1],outcomes[2]);
    locks("12.15-original","aAbB","aAbB",NULL,1,1);
    locks("12.15-fixed","aAbB","aAbB",NULL,3,0);
    locks("12.28-case1","abAB","abAB",NULL,3,0);
    locks("12.28-case2","abAB","abBA",NULL,3,0);
    locks("12.28-case3","abBA","abAB",NULL,3,0);
    locks("12.28-case4","abBA","abBA",NULL,3,0);
    locks("12.29","abBcCA","cbBC",NULL,7,0);
    locks("12.30","abBcCA","cbBCaA","cCbaAB",7,1);
    return 0;
}
