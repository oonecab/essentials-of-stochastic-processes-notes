# Marsaglia xorshift32 (13/17/5), seed 20261010; fixed for reproducible teaching examples.
state=20261010
def uniform01():
    global state
    state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff
    return (state+0.5)/4294967296.0

def main():
    reps=100000;cycles=[0,0];times=[0,0]
    for _ in range(reps):
        j=0 if uniform01()<0.5 else 1;cycles[j]+=1;times[j]+=1 if j==0 else 9
    for j in range(2):
        print(1 if j==0 else 9,format(cycles[j]/reps,".12g"),format(times[j]/sum(times),".12g"))
if __name__=="__main__":main()
