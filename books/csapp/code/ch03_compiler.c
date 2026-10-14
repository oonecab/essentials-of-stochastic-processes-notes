/* No headers: suitable for static x86-64 Linux cross-target compilation.
   Every signed arithmetic example requires representable intermediates. */
long exchange(long *p,long y) { long old=*p; *p=y; return old; }
long affine(long x) { return 3*x+7; }
long smaller(long x,long y) { return x<y?x:y; }
long sum_to(long n) { long sum=0; for(long i=1;i<=n;++i) sum+=i; return sum; }
long rfact(long n) { return n<=1?1:n*rfact(n-1); }
long cread_alt(const long *xp) { static const long zero=0; return *(xp?xp:&zero); }
double mixed(double w,int x,float y,long z) { return (double)((float)x*y)-w/(double)z; }
struct Test { short *p; struct {short x,y;} s; struct Test *next; };
void st_init(struct Test *s) { s->s.y=s->s.x;s->p=&s->s.y;s->next=s; }
