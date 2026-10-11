import math
# Marsaglia xorshift32 (13/17/5), seed 20261010; fixed for reproducible teaching examples.
state=20261010
def uniform01():
    global state
    state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff
    return (state+0.5)/4294967296.0

def main():
    jumps=100000;times=[0.,0.];visits=[0,0];s=0
    for _ in range(jumps):
        visits[s]+=1;times[s]+=-math.log(uniform01())/(1 if s else 2);s=1-s
    for i in range(2):
        print(i,format(visits[i]/jumps,".12g"),format(times[i]/sum(times),".12g"),format(times[i]/visits[i],".12g"))
if __name__=="__main__":main()
