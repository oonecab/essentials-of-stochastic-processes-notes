# Marsaglia xorshift32 (13/17/5), seed 20261010; fixed for reproducible teaching examples.
state=20261010
def uniform01():
    global state
    state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff
    return (state+0.5)/4294967296.0

def main():
    reps=100000;a=5;total=0;up=0
    for _ in range(reps):
        s=0;n=0
        while -a<s<a:s+=1 if uniform01()<0.5 else -1;n+=1
        total+=n;up+=s==a
    print(format(total/reps,".12g"),format(up/reps,".12g"))
if __name__=="__main__":main()
