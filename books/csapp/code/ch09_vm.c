/* CS:APP Figure 9.20 snapshot; no TLB refill or OS/hardware measurement. */
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
struct result { unsigned vpn, vpo, ti, tt, ppn, pa, ci, co, ct, byte; bool th, fault, ch; };
static const int pte[16]={0x28,-1,0x33,2,-1,0x16,-1,-1,0x13,0x17,9,-1,-1,0x2d,0x11,0xd};
static const int tlb[4][4][2]={{{9,13},{7,2},{-1,0},{-1,0}},{{3,45},{-1,0},{-1,0},{-1,0}},{{-1,0},{-1,0},{-1,0},{-1,0}},{{3,13},{10,52},{-1,0},{-1,0}}};
static const int tags[16]={0x19,-1,0x1b,-1,0x32,13,-1,0x16,0x24,-1,0x2d,-1,-1,0x16,0x13,-1};
static const unsigned bytes[16][4]={{0x99,0x11,0x23,0x11},{0},{0,2,4,8},{0},{0x43,0x6d,0x8f,9},{0x36,0x72,0xf0,0x1d},{0},{0x11,0xc2,0xdf,3},{0x3a,0,0x51,0x89},{0},{0x93,0x15,0xda,0x3b},{0},{0},{4,0x96,0x34,0x15},{0x83,0x77,0x1b,0xd3},{0}};
static bool translate(unsigned va, struct result *r) {
    if (va >= 0x4000) return false;
    *r=(struct result){0}; r->vpn=va>>6; r->vpo=va&63; r->ti=r->vpn&3; r->tt=r->vpn>>2;
    int ppn=-1;
    for (unsigned i=0;i<4;i++) if(tlb[r->ti][i][0]==(int)r->tt) { r->th=true; ppn=tlb[r->ti][i][1]; }
    if (!r->th) {
        if(r->vpn>=16) return false; /* Snapshot lacks this PTE: unknown, not a fault. */
        ppn=pte[r->vpn];
    }
    if(ppn<0) { r->fault=true; return true; }
    r->ppn=(unsigned)ppn; r->pa=(r->ppn<<6)|r->vpo; r->co=r->pa&3; r->ci=(r->pa>>2)&15; r->ct=r->pa>>6;
    r->ch=tags[r->ci]==(int)r->ct; if(r->ch)r->byte=bytes[r->ci][r->co]; return true;
}
static void show(unsigned va, const struct result *r) {
    printf("va=%04x vpn=%02x vpo=%02x tlbi=%x tlbt=%02x tlb=%c",va,r->vpn,r->vpo,r->ti,r->tt,r->th?'Y':'N');
    if(r->fault) { puts(" fault=Y"); return; }
    printf(" fault=N pa=%03x co=%x ci=%x ct=%02x cache=%c",r->pa,r->co,r->ci,r->ct,r->ch?'Y':'N');
    if(r->ch)printf(" byte=%02x",r->byte);
    putchar('\n');
}
int main(int argc,char **argv) {
    const unsigned examples[]={0x3d7,0x27c,0x3a9,0x40}; struct result r;
    if(argc==1) { for(unsigned i=0;i<4;i++){if(!translate(examples[i],&r))return 1;show(examples[i],&r);}return 0; }
    if(argc!=2 || argv[1][0]=='-' || argv[1][0]=='+' || !argv[1][0])return 2;
    const char *digits=argv[1];
    if(digits[0]=='0'&&(digits[1]=='x'||digits[1]=='X'))digits+=2;
    if(!*digits)return 2;
    for(const char *p=digits;*p;p++)if(!((*p>='0'&&*p<='9')||(*p>='a'&&*p<='f')||(*p>='A'&&*p<='F')))return 2;
    errno=0;char *end;unsigned long value=strtoul(argv[1],&end,16);
    if(errno || *end || value>=0x4000 || !translate((unsigned)value,&r))return 2;
    show((unsigned)value,&r);return 0;
}
