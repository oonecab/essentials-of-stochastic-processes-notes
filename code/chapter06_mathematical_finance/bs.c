#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
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
static int real(double *x){
    char s[128],*end;if(!token(s))return 0;
    if(strspn(s,"+-0123456789.eE")!=strlen(s))return 0;
    *x=strtod(s,&end);return end!=s&&!*end&&isfinite(*x);
}
static double phi(double x){return 0.5*erfc(-x/sqrt(2.0));}
static double crr(int n,double s,double k,double t,double r,double vol){
    double h=t/n,a=vol*sqrt(h),u=exp(a),d=exp(-a),R=exp(r*h);
    if(!(0<d&&d<R&&R<u)||!isfinite(u)||!isfinite(R))return NAN;
    double p=(R-d)/(u-d),*v=malloc((size_t)(n+1)*sizeof(*v));if(!v)return NAN;
    for(int j=0;j<=n;j++){
        double stock=exp(log(s)+(2*j-n)*a);
        if(!isfinite(stock)||stock<=0){free(v);return NAN;}
        v[j]=fmax(stock-k,0);
    }
    for(int m=n-1;m>=0;m--)for(int j=0;j<=m;j++)v[j]=(p*v[j+1]+(1-p)*v[j])/R;
    double answer=v[0];free(v);return answer;
}
static int run(int argc,char **argv){
    if(argc>2||(argc==2&&strcmp(argv[1],"convergence")!=0))return 2;
    double s,k,t,r,vol;char extra;
    if(!real(&s)||!real(&k)||!real(&t)||!real(&r)||!real(&vol)||scanf(" %c",&extra)!=EOF)return 2;
    if(s<=0||k<=0||t<0||vol<0)return 2;
    double disc=exp(-r*t),kd=k*disc,c,put,delta;
    if(!isfinite(kd)||disc==0)return 3;
    if(t==0||vol==0){double gap=s-kd;c=fmax(gap,0);put=fmax(-gap,0);delta=gap>0?1:(gap<0?0:0.5);}
    else{
        double z=vol*sqrt(t);if(!isfinite(z)||z==0)return 3;
        double d1=(log(s)-log(k)+r*t)/z+z/2,d2=d1-z;
        if(!isfinite(d1)||!isfinite(d2))return 3;
        c=s*phi(d1)-kd*phi(d2);put=kd*phi(-d2)-s*phi(-d1);delta=phi(d1);
    }
    if(!isfinite(c)||!isfinite(put)||!isfinite(delta))return 3;
    double values[6];
    if(argc==2){
        if(t==0||vol==0)return 2;
        for(int i=0,n=16;i<6;i++,n*=2){values[i]=crr(n,s,k,t,r,vol);if(!isfinite(values[i]))return 3;}
    }
    printf("%.12g %.12g %.12g\n",c,put,delta);
    if(argc==2)for(int i=0,n=16;i<6;i++,n*=2)printf("%d %.12g\n",n,values[i]);
    return 0;
}

int main(int argc,char **argv) {
    int status=run(argc,argv);
    if(status==2)fputs("input error: check field count, token length and model parameters\n",stderr);
    if(status==3)fputs("numerical error: singular/ill-conditioned system or finite range exceeded\n",stderr);
    if(status==4)fputs("resource error: allocation failed\n",stderr);
    return status;
}
