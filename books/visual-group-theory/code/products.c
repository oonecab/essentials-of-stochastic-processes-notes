/* Chapter 7. C_n semidirect C_m; t*r*t^-1=r^u. */
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
static int number(const char *s, int *out) {
    int n = 0;
    if (!*s) return 0;
    for (; *s; ++s) {
        if (!isdigit((unsigned char)*s) || n > 24) return 0;
        n = 10*n + *s - '0';
    }
    *out = n; return 1;
}
static int gcd(int a, int b) {
    while (b) { int r = a%b; a=b; b=r; }
    return a;
}
static int modpow(int u, int j, int n) {
    int v = 1;
    for (int k=0; k<j; ++k) v = v*u%n;
    return v;
}
static int multiply(int a, int b, int n, int m, int u) {
    int i=a%n, j=a/n, k=b%n, ell=b/n;
    return (i+modpow(u,j,n)*k)%n + n*((j+ell)%m);
}
static int element_order(int a, int n, int m, int u) {
    int x=0;
    for (int k=1; k<=n*m; ++k) {
        x=multiply(x,a,n,m,u);
        if (!x) return k;
    }
    return 0;
}
int main(int argc, char **argv) {
    int n=4,m=2,u=3;
    if (argc != 1 && (argc != 4 || !number(argv[1],&n) ||
                     !number(argv[2],&m) || !number(argv[3],&u))) {
        fprintf(stderr,"error: expected n m u\n"); return 2;
    }
    if (n<2 || n>12 || m<1 || m>6 || n*m>24 || u<0 || u>=n ||
        gcd(u,n)!=1 || modpow(u,m,n)!=1) {
        fprintf(stderr,"error: require bounded n,m and unit u with u^m=1 mod n\n"); return 2;
    }
    int size=n*m;
    printf("n=%d m=%d u=%d; id=i+n*j represents r^i t^j\n",n,m,u);
    for (int a=0; a<size; ++a)
        printf("%d (%d,%d) order=%d quotient=%d\n",a,a%n,a/n,element_order(a,n,m,u),a/n);
    printf("TABLE\n");
    for (int a=0; a<size; ++a) {
        for (int b=0; b<size; ++b) printf("%s%d",b?" ":"",multiply(a,b,n,m,u));
        printf("\n");
    }
    printf("QUOTIENT C%d\n",m);
    for (int j=0; j<m; ++j) {
        printf("%d: ",j);
        for (int i=0; i<n; ++i) printf("%s%d",i?",":"",i+n*j);
        printf("\n");
    }
    return 0;
}
