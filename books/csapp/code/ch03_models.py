"""Independent arithmetic references; does not execute an x86 ABI."""
import ctypes

MASK=(1<<64)-1

def signed(u, bits):
    return u if u < 1 << (bits-1) else u-(1<<bits)

def layout(fields):
    offsets=[]
    offset=0
    alignment=max(a for _,a in fields)
    for size,align in fields:
        offset=(offset+align-1)//align*align
        offsets.append(offset)
        offset+=size
    return offsets,(offset+alignment-1)//alignment*alignment

def main():
    if ctypes.sizeof(ctypes.c_long)!=8 or ctypes.sizeof(ctypes.c_void_p)!=8:
        raise SystemExit(2)
    count=0
    for a in range(256):
        for b in range(256):
            raw=signed(a,8)-signed(b,8)
            result=raw&255
            sf=result>>7
            of=not -128<=raw<=127
            if bool(sf^of)!=(signed(a,8)<signed(b,8)):
                raise RuntimeError("signed comparison")
            count+=1
    print(f"flags8={count} pass")
    checksum=sum(int(f"{x:016b}"[::-1],2) for x in range(65536))
    print(f"reverse16=65536 checksum={checksum}")
    for name,fields in [
        ("test",[(8,8),(2,2),(2,2),(8,8)]),
        ("P1",[(2,2),(4,4),(8,8),(8,8)]),
        ("P2",[(8,4),(8,1),(8,2),(8,8)]),
        ("P3",[(16,8),(16,8)]),
        ("P4",[(16,1),(16,8)]),
        ("ACE",[(2,2),(8,8)]),
        ("P5",[(64,8),(24,8)]),
        ("rec",[(8,8),(4,4),(1,1),(2,2),(8,8),(8,8),(4,4),(8,8)]),
        ("rec-reordered",[(8,8),(8,8),(8,8),(8,8),(4,4),(4,4),(2,2),(1,1)])]:
        offsets,size=layout(fields)
        print(f"layout-{name}="+','.join(map(str,offsets))+f" size={size}")
    vals=[0,1,2,3,MASK,MASK-1,1<<63,(1<<63)-1,0x0123456789abcdef]
    for a in vals:
        for b in vals:
            product=(signed(a,64)*signed(b,64))&((1<<128)-1)
            print(f"product={a:016x},{b:016x}:{product:032x}")
    for x in range(22):
        value,total=x,0
        while value:
            total+=value
            value//=4
        print(f"rfun={x},{total&MASK}")
    fact=1
    for n in range(1,22):
        value=fact*n
        if value>(1<<63)-1:
            print(f"factorial-overflow={n}")
            break
        fact=value
        if n in (14,20):
            print(f"factorial={n},{fact}")

if __name__=="__main__":
    main()
