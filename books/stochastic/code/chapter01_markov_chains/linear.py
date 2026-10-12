import sys, math, re
class NumericalError(ValueError):
    pass
def main():
    if len(sys.argv)!=2: raise ValueError('one mode required')
    mode=sys.argv[1]
    if mode not in {'pstation','qstation','ptime','qtime','pprob','qprob','psteps'}:
        raise ValueError('unknown mode')
    vals=iter(sys.stdin.read().split())
    def integer():
        s=next(vals)
        if len(s)>127 or not re.fullmatch(r'[+-]?[0-9]+',s): raise ValueError('integer')
        return int(s)
    def real():
        s=next(vals)
        if len(s)>127 or not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',s):
            raise ValueError('number')
        v=float(s)
        if not math.isfinite(v): raise ValueError('finite number required')
        return v
    def end():
        if next(vals,None) is not None: raise ValueError('extra input')
    n=integer()
    if not 1<=n<=64: raise ValueError('size')
    p=[[real() for _ in range(n)] for _ in range(n)];q=mode.startswith('q')
    def accumulate(values):
        total=0.0
        for x in values: total+=x
        return total
    for i,row in enumerate(p):
        if any((x<0 and (not q or i!=j)) or (q and i==j and x>0) for j,x in enumerate(row)):
            raise ValueError('matrix sign')
        scale=max(map(abs,row))
        if q:
            if scale and abs(accumulate(x/scale for x in row))>1e-8*accumulate(abs(x/scale) for x in row):
                raise ValueError('generator row sum')
        elif abs(accumulate(row)-1)>1e-8: raise ValueError('probability row sum')
    def solve(a,b):
        for i in range(n):
            scale=max(map(abs,a[i]))
            if scale==0: raise NumericalError('singular system')
            a[i]=[x/scale for x in a[i]];b[i]/=scale
        for k in range(n):
            j=max(range(k,n),key=lambda i:abs(a[i][k]))
            if abs(a[j][k])<1e-12: raise NumericalError('singular or ill-conditioned system')
            a[k],a[j]=a[j],a[k];b[k],b[j]=b[j],b[k]
            pivot=a[k][k];a[k]=[x/pivot for x in a[k]];b[k]/=pivot
            for i in range(n):
                if i!=k:
                    t=a[i][k];a[i]=[x-t*y for x,y in zip(a[i],a[k])];b[i]-=t*b[k]
        return b
    if mode=='psteps':
        k=integer();v=[real() for _ in range(n)];end()
        if not 0<=k<=100000 or any(x<0 for x in v) or abs(accumulate(v)-1)>1e-8:
            raise ValueError('initial distribution or step count')
        for _ in range(k):v=[accumulate(v[i]*p[i][j] for i in range(n)) for j in range(n)]
    elif 'station' in mode:
        end();a=[[(-accumulate(p[i][k] for k in range(n) if k!=i) if not q and i==j else p[j][i]) for j in range(n)] for i in range(n)]
        a[-1]=[1.0]*n;v=solve(a,[0.0]*(n-1)+[1.0])
    else:
        fixed=[real() for _ in range(n)];end();time='time' in mode
        if not any(x>=0 for x in fixed) or any(x!=-1 and (x<0 or (time and x!=0) or (not time and x>1)) for x in fixed):
            raise ValueError('boundary: -1 for interior, 0 for exit time, [0,1] for probability')
        a=[];b=[]
        for i in range(n):
            if fixed[i]>=0:a.append([float(i==j) for j in range(n)]);b.append(fixed[i])
            else:
                a.append([(accumulate(p[i][k] for k in range(n) if k!=i) if not q and i==j else -p[i][j]) for j in range(n)])
                b.append(float(time))
        v=solve(a,b)
    if any(not math.isfinite(x) or x < -1e-8 for x in v): raise NumericalError('invalid numerical result')
    if 'time' not in mode and (any(x>1+1e-8 for x in v) or (('station' in mode or mode=='psteps') and abs(accumulate(v)-1)>1e-6)):
        raise NumericalError('invalid probability result')
    print(' '.join(format(x,'.12g') for x in v))
if __name__=='__main__':
    try: main()
    except (NumericalError, OverflowError, ZeroDivisionError) as exc:
        print('numerical error: '+str(exc), file=sys.stderr); sys.exit(3)
    except (ValueError, StopIteration) as exc:
        print('input error: '+str(exc or 'missing field'), file=sys.stderr); sys.exit(2)
    except MemoryError:
        print('resource error: allocation failed', file=sys.stderr); sys.exit(4)
