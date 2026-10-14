from fractions import Fraction

def direct(a,x):
    r=a[0];power=x
    for c in a[1:]:r=r+c*power;power=x*power
    return r

def horner(a,x):
    r=a[-1]
    for c in reversed(a[:-1]):r=c+x*r
    return r

def split8(a,x):
    x2=x*x;x4=x2*x2;x8=x4*x4
    r=[0.0]*8
    blocks,tail=divmod(len(a),8)
    r[:tail]=a[blocks*8:]
    for k in reversed(range(blocks)):
        r=[a[k*8+j]+x8*r[j] for j in range(8)]
    return horner(r,x)

a=[float(i%9-4) for i in range(129)]
count=0
for n in range(129):
    for x in (-1.0,-.5,0.0,.5,1.0):
        exact=float(sum(Fraction(c)*Fraction(x)**i for i,c in enumerate(a[:n+1])))
        for f in (direct,horner,split8):
            actual=f(a[:n+1],x)
            if not abs(actual-exact)<=1e-12:
                raise RuntimeError(f"polynomial check failed: {f.__name__} degree={n} x={x}")
        count+=1
print(f"polynomial-cases={count} sample={split8([1.,2.,3.,4.],2.):.0f}")
