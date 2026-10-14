"""Integer-only binary32 transformations matching ch02_float.c."""
import math
import struct
import sys
MASK = (1 << 32) - 1
MIN = -(1 << 31)
def float_negate(f): return f if f & 0x7FFFFFFF > 0x7F800000 else f ^ 0x80000000
def float_absval(f): return f if f & 0x7FFFFFFF > 0x7F800000 else f & 0x7FFFFFFF

def float_twice(f):
    sign, exp, frac = f & 0x80000000, f >> 23 & 255, f & 0x7FFFFF
    if exp == 255: return f
    if exp == 0: return sign | (frac << 1)
    if exp == 254: return sign | 0x7F800000
    return f + 0x00800000

def float_half(f):
    sign, exp, frac = f & 0x80000000, f >> 23 & 255, f & 0x7FFFFF
    if exp == 255: return f
    if exp > 1: return f - 0x00800000
    m = (exp << 23) | frac
    return sign | ((m >> 1) + int((m & 3) == 3))

def float_f2i(f):
    sign, exp, frac = f >> 31, f >> 23 & 255, f & 0x7FFFFF
    e = exp - 127
    if e < 0: return 0
    if e > 30: return MIN
    m = 0x800000 | frac
    mag = m << (e-23) if e >= 23 else m >> (23-e)
    return -mag if sign else mag

def float_i2f(i):
    if not i: return 0
    sign = (i & MASK) & 0x80000000
    mag = (-(i & MASK) & MASK) if sign else i
    t, p = mag, 0
    if t >> 16: p += 16; t >>= 16
    if t >> 8: p += 8; t >>= 8
    if t >> 4: p += 4; t >>= 4
    if t >> 2: p += 2; t >>= 2
    if t >> 1: p += 1
    exp = p + 127
    if p <= 23: sig = mag << (23-p)
    else:
        d = p-23
        sig, rem, half = mag >> d, mag & ((1 << d)-1), 1 << (d-1)
        if rem > half or (rem == half and sig & 1): sig += 1
        if sig == 0x1000000: sig >>= 1; exp += 1
    return sign | (exp << 23) | (sig & 0x7FFFFF)

def fpwr2_bits(x):
    if x < -149: exp, frac = 0, 0
    elif x < -126: exp, frac = 0, 1 << (x+149)
    elif x < 128: exp, frac = x+127, 0
    else: exp, frac = 255, 0
    return (exp << 23) | frac

def float_le_bits(ux, uy):
    sx, sy = ux >> 31, uy >> 31
    return int((ux & 0x7FFFFFFF == 0 and uy & 0x7FFFFFFF == 0)
               or (sx if sx != sy else ux >= uy if sx else ux <= uy))

def u2f(u): return struct.unpack('>f', u.to_bytes(4, 'big'))[0]
def f2u(f):
    try: return int.from_bytes(struct.pack('>f', f), 'big')
    except OverflowError: return 0xFF800000 if f < 0 else 0x7F800000

def test_one(u):
    i = u if u < (1 << 31) else u-(1 << 32)
    if float_i2f(i) != f2u(float(i)): raise RuntimeError(('i2f',u))
    a = u & 0x7FFFFFFF
    if a > 0x7F800000:
        if any(fn(u) != u for fn in (float_negate,float_absval,float_twice,float_half)) or float_f2i(u) != MIN:
            raise RuntimeError(('NaN',u))
        return
    f = u2f(u)
    ref_int = int(f) if -2147483648.0 <= f < 2147483648.0 else MIN
    if (float_negate(u) != f2u(-f) or float_absval(u) != f2u(abs(f))
        or float_twice(u) != f2u(f*2.0) or float_half(u) != f2u(f*0.5) or float_f2i(u) != ref_int):
        raise RuntimeError(('float',u))

def main():
    count = 0
    if sys.argv[1:] == ['--exhaustive']:
        for u in range(1 << 32): test_one(u)
        count = 1 << 32
    elif not sys.argv[1:]:
        fracs = [0,1,2,3,4,0x3FFFFF,0x400000,0x400001,0x7FFFFC,0x7FFFFD,0x7FFFFE,0x7FFFFF]
        for s in range(2):
            for e in range(256):
                for f in fracs: test_one((s << 31)|(e << 23)|f); count += 1
        rng = 0x27182818
        for _ in range(100000):
            rng = (rng*1664525+1013904223) & MASK
            test_one(rng); count += 1
    else: raise SystemExit('usage: ch02_float.py [--exhaustive]')
    cases = [0,0x80000000,0x3F800000,0xBF800000,0x7F800000,0xFF800000,1,0x80000001]
    for x in cases:
        for y in cases:
            if float_le_bits(x,y) != int(u2f(x) <= u2f(y)): raise RuntimeError('le')
    print(f'float_cases={count} operations=6 comparison_pairs=64 status=ok')
    for u in [0,1,3,0x007FFFFF,0x00800000,0x3F800000,0x7F7FFFFF,0x7F800000,0x7FC12345]:
        print(f'bits={u:08x} twice={float_twice(u):08x} half={float_half(u):08x} int={float_f2i(u)}')
    print('powers='+','.join(f'{fpwr2_bits(x):08x}' for x in [-150,-149,-126,128]))

if __name__ == '__main__': main()
