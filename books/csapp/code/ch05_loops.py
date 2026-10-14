import struct

MASK = (1 << 64) - 1

def require(condition, message):
    if not condition:
        raise RuntimeError("loop check failed: " + message)

def combine5(a):
    r = i = 0
    while len(a)-i >= 5:
        for j in range(5):
            r = (r + a[i+j]) & MASK
        i += 5
    for x in a[i:]:
        r = (r+x) & MASK
    return r

def dot6(u, v, mode):
    r = [0]*6
    i = 0
    while len(u)-i >= 6:
        products = [(u[i+j]*v[i+j]) & MASK for j in range(6)]
        if mode == "6x6":
            r = [(x+y) & MASK for x,y in zip(r, products)]
        elif mode == "6x1a":
            r[0] = (r[0]+sum(products)) & MASK
        else:
            for x in products:
                r[0] = (r[0]+x) & MASK
        i += 6
    for j in range(i,len(u)):
        r[0] = (r[0]+u[j]*v[j]) & MASK
    return sum(r) & MASK

def merge(a,b):
    i=j=0
    d=[]
    while i<len(a) and j<len(b):
        take = int(a[i]<b[j])
        d.append(a[i] if take else b[j])
        i+=take
        j+=1-take
    return d+a[i:]+b[j:]

def f32(x):
    return struct.unpack("f",struct.pack("f",x))[0]

def prefix(a,grouped=False,p=None):
    # A separate result list, or the exact input list for in-place operation.
    # C pointer ranges that partially overlap require a separate contract.
    s=0.0
    if p is None:p=[0.0]*len(a)
    i=0
    if grouped:
        while len(a)-i>=3:
            b0=a[i];b1=f32(b0+a[i+1]);b2=f32(b1+a[i+2])
            p[i]=f32(s+b0);p[i+1]=f32(s+b1);s=f32(s+b2);p[i+2]=s
            i+=3
    while i<len(a):
        s=f32(s+a[i]);p[i]=s;i+=1
    return p

a=[i*17+3 for i in range(130)];a[0]=MASK
b=[i*9+1 for i in range(130)]
lengths=prefix_cases=inplace_cases=0
for n in range(131):
    combined=combine5(a[:n])
    require(combined == sum(a[:n]) & MASK, "combine5 modulo 2^64")
    expected=sum(x*y for x,y in zip(a[:n],b[:n])) & MASK
    for mode in ("6x1","6x6","6x1a"):
        actual=dot6(a[:n],b[:n],mode)
        require(actual==expected, "dot " + mode)
    lengths+=1
x=list(range(1000));y=x.copy()
for i in range(999):x[i]=x[i+1]
for i in range(999):y[i+1]=y[i]
require((x[0],x[998],y[999])==(1,999,0), "forward copy overlap")
merged=merge([-4,0,3,9],[-3,0,7,8])
require(merged==[-4,-3,0,0,3,7,8,9], "merged order")
f=[(i%17-8)/4 for i in range(130)]
for n in range(131):
    serial=prefix(f[:n]);grouped=prefix(f[:n],True)
    require(serial==grouped, "exact prefix input")
    a=f[:n];b=f[:n]
    inplace1=prefix(a,p=a);inplace3=prefix(b,True,b)
    require(inplace1==serial and inplace3==grouped, "in-place prefix")
    prefix_cases+=1;inplace_cases+=1
hard=[16777216.0,0.0,0.0,1.0,-16777216.0,1.0]
serial=prefix(hard);grouped=prefix(hard,True)
require(serial[-1]==1 and grouped[-1]==2, "binary32 regrouping counterexample")
print(f"lengths={lengths} modular-reductions=ok merge=ok overlap=ok")
print(f"prefix-exact={prefix_cases} inplace={inplace_cases} serial-last={serial[-1]:.0f} grouped-last={grouped[-1]:.0f}")
