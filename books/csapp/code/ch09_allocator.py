"""Independent interval reference, not a byte-header or C-pointer emulation."""
def require(condition, message):
    if not condition:
        raise RuntimeError("allocator check failed: " + message)


class Heap:
    def __init__(self, next_fit=False, elide=False):
        self.blocks = [[12,65520,False]]
        self.rover = 12
        self.nf, self.elide = next_fit, elide
        self.cases = [0]*4
    def alloc(self,n):
        if n <= 0 or n > 65520-(4 if self.elide else 8):
            return None
        need=max(16,((n+(4 if self.elide else 8)+7)//8)*8)
        start=next(i for i,b in enumerate(self.blocks) if b[0]==self.rover) if self.nf else 0
        for index in [(start+j)%len(self.blocks) for j in range(len(self.blocks))]:
            at,total,used=self.blocks[index]
            if used or total<need:
                continue
            if total-need>=16:
                self.blocks[index:index+1]=[[at,need,True],[at+need,total-need,False]]
                self.rover=at+need
            else:
                self.blocks[index][2]=True
                self.rover=at+total if at+total<65532 else 12
            return at+4
        return None
    def free(self,p):
        if p is None:
            return
        i=next(i for i,b in enumerate(self.blocks) if b[0]+4==p and b[2])
        left=i>0 and not self.blocks[i-1][2]
        right=i+1<len(self.blocks) and not self.blocks[i+1][2]
        self.cases[2*left+right]+=1
        lo=i-1 if left else i
        hi=i+2 if right else i+1
        at=self.blocks[lo][0]
        total=sum(b[1] for b in self.blocks[lo:hi])
        self.blocks[lo:hi]=[[at,total,False]]
        if at<=self.rover<at+total:
            self.rover=at
    def check(self):
        at=12;prev=True
        for h,n,a in self.blocks:
            require(h==at and n>=16 and n%8==0 and (prev or a), "block partition")
            at+=n;prev=a
        require(at==65532 and self.rover in [b[0] for b in self.blocks], "extent and rover")
def test(nf,elide):
    cases=0
    for case in range(4):
        h=Heap(nf,elide);p=[h.alloc(16) for _ in range(5)]
        require(all(x is not None for x in p), "coalescing fixtures allocated")
        if case&2:h.free(p[1])
        if case&1:h.free(p[3])
        before=h.cases[case];h.free(p[2])
        require(h.cases[case]==before+1, "coalescing case")
        h.check();cases+=1
    h=Heap(nf,elide)
    zero=h.alloc(0);oversize=h.alloc(2**64-1)
    require(zero is None and oversize is None, "zero and oversize rejected")
    h.free(None)
    p=[h.alloc(1+(i*37)%127) for i in range(512)]
    require(all(x is not None for x in p), "stress allocations")
    stress=len(p)
    for parity in range(2):
        for i in range(parity,512,2):h.free(p[i]);h.check()
    require(h.blocks==[[12,65520,False]], "whole arena restored")
    p=h.alloc(65520-(4 if elide else 8))
    extra=h.alloc(1)
    require(p is not None and extra is None, "full arena and exhaustion")
    h.free(p);h.check()
    print(f'allocator={"next" if nf else "first"} footer={"free-only" if elide else "all"} cases={cases} stress={stress} restored={h.blocks[0][1]}')
if __name__=='__main__':
    import sys
    if len(sys.argv)!=1:sys.exit(2)
    for nf,elide in [(False,False),(True,False),(False,True),(True,True)]:test(nf,elide)
