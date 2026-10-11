#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
typedef struct{double s,v,delta;int action;char path[14];}Node;
static Node *nodes;static int N,kind,american;static double u,d,R,K,barrier,p;
static int token(char s[128]) {
    int c; size_t n=0;
    do { c=getchar(); } while(c!=EOF && isspace((unsigned char)c));
    if(c==EOF)return 0;
    do {
        if(n==127)return 0; /* Reject the whole field rather than split it. */
        s[n++]=(char)c; c=getchar();
    } while(c!=EOF && !isspace((unsigned char)c));
    s[n]='\0'; return 1;
}
static int integer(int *x){
    char s[128],*end;if(!token(s))return 0;
    const char *z=s;if(*z=='+'||*z=='-')z++;
    if(!*z||strspn(z,"0123456789")!=strlen(z))return 0;
    errno=0;long v=strtol(s,&end,10);
    if(errno||*end||v<INT_MIN||v>INT_MAX)return 0;
    *x=(int)v;return 1;
}
static int real(double *x){
    char s[128],*end;if(!token(s))return 0;
    if(strspn(s,"+-0123456789.eE")!=strlen(s))return 0;
    *x=strtod(s,&end);return end!=s&&!*end&&isfinite(*x);
}
static double payoff(const double *ss,int n){
    double s=ss[n],lo=s,hi=s,mean=0;
    for(int i=0;i<=n;i++){lo=fmin(lo,ss[i]);hi=fmax(hi,ss[i]);mean+=ss[i]/(n+1);}
    switch(kind){
    case 0:return fmax(s-K,0);case 1:return fmax(K-s,0);
    case 2:return fmax(mean-K,0);case 3:return hi-s;case 4:return s-lo;
    case 5:return s>K?1:0;case 6:return fmin(fmax(s-K,0),60);
    case 7:return hi>=barrier?0:fmax(K-s,0);default:return NAN;
    }
}
static double build(int id,int n,double *ss){
    Node *z=&nodes[id];z->s=ss[n];if(!isfinite(z->s)||z->s<=0)return NAN;
    if(n==N){z->v=payoff(ss,n);z->action=2;return z->v;}
    int h=2*id+1,t=h+1;size_t len=n==0?0:strlen(z->path);
    if(len){memcpy(nodes[h].path,z->path,len);memcpy(nodes[t].path,z->path,len);}
    nodes[h].path[len]='H';nodes[t].path[len]='T';
    nodes[h].path[len+1]='\0';nodes[t].path[len+1]='\0';
    ss[n+1]=z->s*u;double vh=build(h,n+1,ss);
    ss[n+1]=z->s*d;double vt=build(t,n+1,ss);
    if(!isfinite(vh)||!isfinite(vt))return NAN;
    double cv=(p*vh+(1-p)*vt)/R,iv=payoff(ss,n);
    z->delta=(vh-vt)/z->s/(u-d);
    if(!isfinite(cv)||!isfinite(iv)||!isfinite(z->delta))return NAN;
    /* A tie within rounding noise follows the earliest positive-exercise convention. */
    double tolerance=32*DBL_EPSILON*fmax(fabs(iv),fabs(cv));
    z->action=american&&iv>0&&iv>=cv-tolerance;
    z->v=z->action?iv:cv;return z->v;
}
static int run(int argc,char **argv){
    (void)argv;double s0,r;char extra;
    if(argc!=1||!integer(&N)||!real(&s0)||!real(&u)||!real(&d)||!real(&r)||!real(&K)||
       !integer(&kind)||!integer(&american)||!real(&barrier)||scanf(" %c",&extra)!=EOF)return 2;
    if(N<0||N>12||s0<=0||d<=0||u<=d||K<0||kind<0||kind>7||(american!=0&&american!=1))return 2;
    R=1+r;if(!(d<R&&R<u))return 2;p=(R-d)/(u-d);
    int size=(1<<(N+1))-1;nodes=calloc((size_t)size,sizeof(*nodes));if(!nodes)return 4;
    double ss[13]={0};ss[0]=s0;
    if(!isfinite(build(0,0,ss))){free(nodes);return 3;}
    for(int id=0;id<size;id++)printf("%s %.12g %.12g %.12g %d\n",id?nodes[id].path:"-",nodes[id].s,nodes[id].v,nodes[id].delta,nodes[id].action);
    free(nodes);return 0;
}

int main(int argc,char **argv) {
    int status=run(argc,argv);
    if(status==2)fputs("input error: check field count, token length and model parameters\n",stderr);
    if(status==3)fputs("numerical error: singular/ill-conditioned system or finite range exceeded\n",stderr);
    if(status==4)fputs("resource error: allocation failed\n",stderr);
    return status;
}
