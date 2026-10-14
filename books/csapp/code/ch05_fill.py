import ctypes

K=ctypes.sizeof(ctypes.c_ulong)

def fill(a,start,c,n):
    # Python models the region; native address alignment is exercised in C.
    byte=c & 255
    i=start
    while n and i % K:a[i]=byte;i+=1;n-=1
    while n>=K:a[i:i+K]=bytes([byte])*K;i+=K;n-=K
    while n:a[i]=byte;i+=1;n-=1

cases=0
for offset in range(16):
    for n in range(65):
        for c in (-257,0,257):
            a=bytearray([0xa5]*96)
            fill(a,offset,c,n)
            expected=bytes([0xa5])*offset+bytes([c & 255])*n+bytes([0xa5])*(96-offset-n)
            if a!=expected:
                raise RuntimeError(f"fill check failed: offset={offset} count={n} byte={c & 255}")
            cases+=1
print(f"fill-cases={cases} word-bytes={K} guards=ok")
