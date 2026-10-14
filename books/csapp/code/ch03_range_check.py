"""Binary32 classification oracle. Python validates the value model, not x86 ABI.
Default: 16 boundary encodings. --exhaustive iterates all 2**32 encodings.
The full assembly execution evidence is produced by ch03_range_check.c.
"""
import math
import struct
import sys

def from_bits(u):
    magnitude=u&0x7fffffff
    if magnitude>0x7f800000:
        return 3
    if magnitude==0:
        return 1
    return 0 if u>>31 else 2

def main():
    if sys.argv[1:] not in ([],["--exhaustive"]):
        return 2
    cases=range(1<<32) if sys.argv[1:] else [
        0,0x80000000,1,0x80000001,0x007fffff,0x00800000,
        0x3f800000,0xbf800000,0x7f7fffff,0xff7fffff,
        0x7f800000,0xff800000,0x7f800001,0xff800001,0x7fc00000,0xffffffff]
    counts=[0,0,0,0]
    for u in cases:
        x=struct.unpack('<f',struct.pack('<I',u))[0]
        expected=3 if math.isnan(x) else 0 if x<0 else 2 if x>0 else 1
        if from_bits(u)!=expected:
            return 1
        counts[expected]+=1
    print(f"checked={sum(counts)} model=pass")
    print(" ".join(f"{name}={n}" for name,n in zip(["NEG","ZERO","POS","OTHER"],counts)))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
