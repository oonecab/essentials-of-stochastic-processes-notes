import math
# Marsaglia xorshift32 (13/17/5), seed 20261010; fixed for reproducible teaching examples.
state=20261010
def uniform01():
    global state
    state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff
    return (state+0.5)/4294967296.0

def main():
    reps=100000;cap=16;counts=[0]*(cap+1)
    for _ in range(reps):
        t=0;n=0
        while True:
            t+=-math.log(uniform01())/3
            if t>2:break
            n+=1
        counts[min(n,cap)]+=1
    theory=math.exp(-6);total=0
    for k in range(cap+1):
        p=1-total if k==cap else theory
        print(k,format(p,".12g"),format(counts[k]/reps,".12g"))
        total+=theory;theory*=6/(k+1)
if __name__=="__main__":main()
