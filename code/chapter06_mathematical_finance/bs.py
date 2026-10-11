import sys, math, re
def phi(x):return 0.5*math.erfc(-x/math.sqrt(2))
class NumericalError(ValueError):
    pass
def main():
    if len(sys.argv)>2 or (len(sys.argv)==2 and sys.argv[1]!='convergence'):raise ValueError('mode')
    data=sys.stdin.read().split()
    pattern=r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
    if len(data)!=5 or any(len(x)>127 or not re.fullmatch(pattern,x) for x in data):raise ValueError('five numbers')
    s,k,t,r,vol=map(float,data)
    if not all(map(math.isfinite,[s,k,t,r,vol])) or s<=0 or k<=0 or t<0 or vol<0:raise ValueError('parameters')
    disc=math.exp(-r*t);kd=k*disc
    if not math.isfinite(kd) or disc==0:raise NumericalError('discount outside numerical range')
    if t==0 or vol==0:
        gap=s-kd;c=max(gap,0);put=max(-gap,0);delta=1 if gap>0 else 0 if gap<0 else 0.5
    else:
        z=vol*math.sqrt(t)
        if not math.isfinite(z) or z==0:raise NumericalError('volatility outside numerical range')
        d1=(math.log(s)-math.log(k)+r*t)/z+z/2;d2=d1-z
        if not math.isfinite(d1) or not math.isfinite(d2):raise NumericalError('d outside numerical range')
        c=s*phi(d1)-kd*phi(d2);put=kd*phi(-d2)-s*phi(-d1);delta=phi(d1)
    if not all(map(math.isfinite,[c,put,delta])):raise NumericalError('result outside numerical range')
    c=0.0 if c==0 else c; put=0.0 if put==0 else put; delta=0.0 if delta==0 else delta
    rows=[f'{c:.12g} {put:.12g} {delta:.12g}']
    if len(sys.argv)==2:
        if t==0 or vol==0:raise ValueError('positive t and volatility for convergence')
        for n in [16,32,64,128,256,512]:
            h=t/n;a=vol*math.sqrt(h);u=math.exp(a);d=math.exp(-a);R=math.exp(r*h)
            if not 0<d<R<u:raise NumericalError('binomial arbitrage or numerical range')
            p=(R-d)/(u-d);stocks=[math.exp(math.log(s)+(2*j-n)*a) for j in range(n+1)]
            if any(not math.isfinite(x) or x<=0 for x in stocks):raise NumericalError('stock outside numerical range')
            v=[max(x-k,0) for x in stocks]
            for m in range(n-1,-1,-1):v=[(p*v[j+1]+(1-p)*v[j])/R for j in range(m+1)]
            if not math.isfinite(v[0]):raise NumericalError('CRR result outside numerical range')
            rows.append(f'{n} {v[0]:.12g}')
    print('\n'.join(rows))
if __name__=='__main__':
    try: main()
    except (NumericalError, OverflowError, ZeroDivisionError) as exc:
        print('numerical error: '+str(exc), file=sys.stderr); sys.exit(3)
    except (ValueError, StopIteration) as exc:
        print('input error: '+str(exc or 'missing field'), file=sys.stderr); sys.exit(2)
    except MemoryError:
        print('resource error: allocation failed', file=sys.stderr); sys.exit(4)
