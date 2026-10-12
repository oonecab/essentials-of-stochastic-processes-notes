#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <limits.h>
#define MAX 64
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
static int integer(int *x) {
    char s[128],*end; if(!token(s))return 0;
    const char *p=s; if(*p=='+'||*p=='-')p++;
    if(!*p||strspn(p,"0123456789")!=strlen(p))return 0;
    errno=0;long v=strtol(s,&end,10);
    if(errno||*end||v<INT_MIN||v>INT_MAX)return 0;
    *x=(int)v;return 1;
}
static int real(double *x) {
    char s[128],*end;if(!token(s))return 0;
    if(strspn(s,"+-0123456789.eE")!=strlen(s))return 0;
    *x=strtod(s,&end);return end!=s&&!*end&&isfinite(*x);
}
static int eof(void) {char c;return scanf(" %c",&c)==EOF;}
static int solve(int n,double a[MAX][MAX],double b[MAX]) {
    for(int i=0;i<n;i++) {
        double scale=0;for(int j=0;j<n;j++)scale=fmax(scale,fabs(a[i][j]));
        if(scale==0)return 0;
        for(int j=0;j<n;j++)a[i][j]/=scale;
        b[i]/=scale;
    }
    for(int k=0;k<n;k++) {
        int p=k;for(int i=k+1;i<n;i++)if(fabs(a[i][k])>fabs(a[p][k]))p=i;
        if(fabs(a[p][k])<1e-12)return 0;
        for(int j=0;j<n;j++){double t=a[k][j];a[k][j]=a[p][j];a[p][j]=t;}
        double t=b[k];b[k]=b[p];b[p]=t;
        t=a[k][k];for(int j=0;j<n;j++)a[k][j]/=t;b[k]/=t;
        for(int i=0;i<n;i++)if(i!=k){
            t=a[i][k];for(int j=0;j<n;j++)a[i][j]-=t*a[k][j];b[i]-=t*b[k];
        }
    }
    return 1;
}
static int run(int argc,char **argv) {
    if(argc!=2)return 2;const char *m=argv[1];
    int q=m[0]=='q',st=strstr(m,"station")!=NULL,ti=strstr(m,"time")!=NULL;
    int steps=strcmp(m,"psteps")==0;
    if(!(strcmp(m,"pstation")==0||strcmp(m,"qstation")==0||strcmp(m,"ptime")==0||
         strcmp(m,"qtime")==0||strcmp(m,"pprob")==0||strcmp(m,"qprob")==0||steps))return 2;
    int n;if(!integer(&n)||n<1||n>MAX)return 2;
    double p[MAX][MAX]={{0}},a[MAX][MAX]={{0}},b[MAX]={0},v[MAX]={0};
    for(int i=0;i<n;i++) {
        double scale=0,sum=0,norm=0;
        for(int j=0;j<n;j++){
            if(!real(&p[i][j])||((!q||i!=j)&&p[i][j]<0)||(q&&i==j&&p[i][j]>0))return 2;
            scale=fmax(scale,fabs(p[i][j]));
        }
        for(int j=0;j<n;j++){
            double x=q?(scale?p[i][j]/scale:0):p[i][j];sum+=x;norm+=fabs(x);
        }
        if(!isfinite(sum)||(q?fabs(sum)>1e-8*norm:fabs(sum-1)>1e-8))return 2;
    }
    if(steps){
        int k;if(!integer(&k)||k<0||k>100000)return 2;
        double sum=0;
        for(int i=0;i<n;i++){if(!real(&v[i])||v[i]<0)return 2;sum+=v[i];}
        if(!eof()||fabs(sum-1)>1e-8)return 2;
        for(int h=0;h<k;h++){
            for(int j=0;j<n;j++){b[j]=0;for(int i=0;i<n;i++)b[j]+=v[i]*p[i][j];}
            for(int i=0;i<n;i++)v[i]=b[i];
        }
    }else if(st){
        if(!eof())return 2;
        for(int i=0;i<n;i++)for(int j=0;j<n;j++) {
            if(!q && i==j) {
                double outgoing=0;for(int k=0;k<n;k++)if(k!=i)outgoing+=p[i][k];
                a[i][j]=-outgoing; /* Avoid subtracting a diagonal close to one. */
            }else a[i][j]=p[j][i];
        }
        for(int j=0;j<n;j++)a[n-1][j]=1;
        b[n-1]=1;if(!solve(n,a,b))return 3;
        for(int i=0;i<n;i++)v[i]=b[i];
    }else{
        double fixed[MAX];int boundary=0;
        for(int i=0;i<n;i++){
            if(!real(&fixed[i])||(fixed[i]!=-1&&(fixed[i]<0||(ti&&fixed[i]!=0)||(!ti&&fixed[i]>1))))return 2;
            boundary+=fixed[i]>=0;
        }
        if(!boundary||!eof())return 2;
        for(int i=0;i<n;i++){
            if(fixed[i]>=0){a[i][i]=1;b[i]=fixed[i];}
            else{
                for(int j=0;j<n;j++)a[i][j]=-p[i][j];
                if(!q){a[i][i]=0;for(int j=0;j<n;j++)if(j!=i)a[i][i]+=p[i][j];}
                b[i]=ti?1:0;
            }
        }
        if(!solve(n,a,b))return 3;
        for(int i=0;i<n;i++)v[i]=b[i];
    }
    double sum=0;
    for(int i=0;i<n;i++){
        if(!isfinite(v[i])||v[i]<-1e-8||(!ti&&v[i]>1+1e-8))return 3;
        sum+=v[i];
    }
    if((st||steps)&&fabs(sum-1)>1e-6)return 3;
    for(int i=0;i<n;i++)printf("%s%.12g",i?" ":"",v[i]);
    putchar('\n');return 0;
}

int main(int argc,char **argv) {
    int status=run(argc,argv);
    if(status==2)fputs("input error: check field count, token length and model parameters\n",stderr);
    if(status==3)fputs("numerical error: singular/ill-conditioned system or finite range exceeded\n",stderr);
    if(status==4)fputs("resource error: allocation failed\n",stderr);
    return status;
}
