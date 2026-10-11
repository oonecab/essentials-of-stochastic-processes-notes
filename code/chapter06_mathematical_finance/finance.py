import sys, math, re
class NumericalError(ValueError):
    pass
def main():
    data=sys.stdin.read().split()
    if len(sys.argv)!=1 or len(data)!=9:raise ValueError('nine fields, no arguments')
    def integer(s):
        if len(s)>127 or not re.fullmatch(r'[+-]?[0-9]+',s):raise ValueError('integer')
        return int(s)
    def real(s):
        if len(s)>127 or not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',s):raise ValueError('number')
        return float(s)
    n=integer(data[0]);s0,u,d,r,k=map(real,data[1:6]);kind=integer(data[6]);american=integer(data[7]);barrier=real(data[8])
    if not 0<=n<=12 or not all(map(math.isfinite,[s0,u,d,r,k,barrier])) or s0<=0 or d<=0 or u<=d or k<0 or kind not in range(8) or american not in [0,1]:raise ValueError('parameters')
    R=1+r
    if not d<R<u:raise ValueError('arbitrage in stock model')
    p=(R-d)/(u-d);nodes=[None]*((1<<(n+1))-1)
    def payoff(ss):
        s=ss[-1]
        if kind==0:return max(s-k,0)
        if kind==1:return max(k-s,0)
        if kind==2:
            mean=0.0
            for x in ss: mean+=x/len(ss)
            return max(mean-k,0)
        if kind==3:return max(ss)-s
        if kind==4:return s-min(ss)
        if kind==5:return float(s>k)
        if kind==6:return min(max(s-k,0),60)
        return 0 if max(ss)>=barrier else max(k-s,0)
    def build(i,path,ss):
        s=ss[-1]
        if not math.isfinite(s) or s<=0:raise NumericalError('stock outside numerical range')
        if len(path)==n:v=payoff(ss);delta=0.;act=2
        else:
            vh=build(2*i+1,path+'H',ss+[s*u]);vt=build(2*i+2,path+'T',ss+[s*d])
            cv=(p*vh+(1-p)*vt)/R;iv=payoff(ss)
            delta=(vh-vt)/s/(u-d)
            tolerance=32*sys.float_info.epsilon*max(abs(iv),abs(cv))
            act=int(bool(american and iv>0 and iv>=cv-tolerance))
            v=iv if act else cv
        if not math.isfinite(v) or not math.isfinite(delta):raise NumericalError('value outside numerical range')
        nodes[i]=(path or '-',s,v,delta,act);return v
    build(0,'',[s0])
    for path,s,v,delta,act in nodes:print(path,format(s,'.12g'),format(v,'.12g'),format(delta,'.12g'),act)
if __name__=='__main__':
    try: main()
    except (NumericalError, OverflowError, ZeroDivisionError) as exc:
        print('numerical error: '+str(exc), file=sys.stderr); sys.exit(3)
    except (ValueError, StopIteration) as exc:
        print('input error: '+str(exc or 'missing field'), file=sys.stderr); sys.exit(2)
    except MemoryError:
        print('resource error: allocation failed', file=sys.stderr); sys.exit(4)
