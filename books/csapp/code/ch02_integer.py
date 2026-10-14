"""Chapter 2, the same 32-bit algorithms as ch02_integer.c.
C object byte views use ctypes; integer models always mask to 32 bits.
"""
import ctypes
import sys
MASK = (1 << 32) - 1
MIN, MAX = -(1 << 31), (1 << 31) - 1

def decode(u):
    u &= MASK
    return u if u <= MAX else u - (1 << 32)

def show_bytes(obj):
    return bytes(obj).hex(" ")

def show_short(x): return show_bytes(ctypes.c_short(x))
def show_long(x): return show_bytes(ctypes.c_long(x))
def show_double(x): return show_bytes(ctypes.c_double(x))
def is_little_endian(): return int(bytes(ctypes.c_uint(1))[0] == 1)

def inplace_swap(a, i, j):
    a[j] = a[i] ^ a[j]
    a[i] = a[i] ^ a[j]
    a[j] = a[i] ^ a[j]

def reverse_array(a):
    first, last = 0, len(a) - 1
    while first < last:
        inplace_swap(a, first, last)
        first, last = first + 1, last - 1

def bis(x, m): return (x | m) & MASK
def bic(x, m): return x & ~m & MASK
def bool_or(x, y): return bis(x, y)
def bool_xor(x, y): return bis(bic(x, y), bic(y, x))
def sum_elements(a):
    s = 0.0
    for x in a: s = ctypes.c_float(s + x).value
    return s

def strlonger(s, t): return int(len(s) > len(t))
def uadd_ok(x, y): return int(((x + y) & MASK) >= x)
def tadd_ok(x, y): return int(not (y > 0 and x > MAX-y) and not (y < 0 and x < MIN-y))
def tsub_ok(x, y): return int(not (y > 0 and x < MIN+y) and not (y < 0 and x > MAX+y))
def tmult_ok(x, y): return int(MIN <= x*y <= MAX)
def div16(x): return (x + ((x >> 31) & 15)) >> 4
def replace_byte(x, i, b):
    shift = i << 3
    return ((x & ~(255 << shift)) | (b << shift)) & MASK

def any_one(x): return int(bool(x))
def any_zero(x): return int(bool((~x) & MASK))
def low_any_one(x): return int(bool(x & 255))
def high_any_zero(x): return int(bool((~x >> 24) & 255))
def int_shifts_are_arithmetic(): return int((-1 >> 1) == -1)
def srl(x, k):
    xsra = decode(x) >> k
    high = ((MASK << (31-k)) << 1) & MASK
    return xsra & ~high & MASK

def sra(x, k):
    xsrl = (x & MASK) >> k
    high = ((MASK << (31-k)) << 1) & MASK
    sign = -int(bool((x & MASK) & (1 << 31))) & MASK
    return decode(xsrl | (high & sign))

def any_odd_one(x): return int(bool(x & 0xAAAAAAAA))
def odd_ones(x):
    x ^= x >> 16; x ^= x >> 8; x ^= x >> 4; x ^= x >> 2; x ^= x >> 1
    return x & 1

def leftmost_one(x):
    x |= x >> 1; x |= x >> 2; x |= x >> 4; x |= x >> 8; x |= x >> 16
    return decode(x & ~(x >> 1))

def int_size_is_32():
    x = 1 << 15
    x = (x << 15) & MASK
    x = (x << 1) & MASK
    return int(bool(x) and not ((x << 1) & MASK))

def lower_one_mask(n): return decode(MASK >> (32-n))
def rotate_left(x, n): return ((x << n) | ((x >> (31-n)) >> 1)) & MASK
def fits_bits(x, n):
    t = x >> (n-1)
    return int(not t or not ~t)

def xbyte(word, bytenum): return decode(word << ((3-bytenum) << 3)) >> 24

def copy_int(val, buf, maxbytes):
    data = bytes(ctypes.c_int(val))
    if maxbytes >= 0 and maxbytes >= len(data):
        buf[:len(data)] = data
        return 1
    return 0

def saturating_add(x, y):
    ux, uy = x & MASK, y & MASK
    s = (ux + uy) & MASK
    sx, sy, ss = ux >> 31, uy >> 31, s >> 31
    overflow = (~(sx ^ sy) & (sx ^ ss)) & 1
    mask = -overflow & MASK
    bound = MAX + sx
    return decode((s & ~mask) | (bound & mask))

def signed_high_prod(x, y): return decode(((x*y) & ((1 << 64)-1)) >> 32)
def unsigned_high_prod(x, y):
    sx, sy = -(x >> 31) & MASK, -(y >> 31) & MASK
    return (signed_high_prod(decode(x), decode(y)) + (sx & y) + (sy & x)) & MASK

def checked_calloc(nmemb, size):
    """Return zeroed storage, or None when its length or allocation is invalid."""
    size_max = (1 << (8*ctypes.sizeof(ctypes.c_size_t))) - 1
    if nmemb <= 0 or size <= 0 or nmemb > size_max // size: return None
    total = nmemb * size
    if total > sys.maxsize: return None
    try: return bytearray(total)
    except (MemoryError, OverflowError): return None

def copy_elements(src, n, size):
    """Copy n source objects of at least size bytes; allocation failure returns None."""
    size_max = (1 << (8*ctypes.sizeof(ctypes.c_size_t))) - 1
    if n <= 0 or size <= 0 or n > size_max // size: return None
    total = n * size
    if total > sys.maxsize: return None
    try:
        result = bytearray(total)
        for i in range(n): result[i*size:(i+1)*size] = src[i][:size]
        return result
    except (MemoryError, OverflowError): return None

def divide_power2(x, k): return (x + ((x >> 31) & ((1 << k)-1))) >> k

def mul3div4(x):
    u = x & MASK
    product = decode((u << 1) + u)
    return (product + ((product >> 31) & 3)) >> 2

def threefourths(x):
    q, r = x >> 2, x & 3
    return (q+q+q) + ((r+r+r+((x >> 31) & 3)) >> 2)

def trunc_div(x, d): return x//d if x >= 0 else -((-x)//d)

def check_pair(x, y):
    a, b, p = x+y, x-y, x*y
    if (tadd_ok(x,y) != int(MIN <= a <= MAX) or tsub_ok(x,y) != int(MIN <= b <= MAX)
        or tmult_ok(x,y) != int(MIN <= p <= MAX) or saturating_add(x,y) != min(MAX,max(MIN,a))
        or unsigned_high_prod(x & MASK,y & MASK) != ((x & MASK)*(y & MASK) >> 32)
        or uadd_ok(x & MASK,y & MASK) != int((x & MASK)+(y & MASK) <= MASK)):
        raise RuntimeError((x,y))

def main():
    edge = [MIN,MIN+1,-65535,-129,-128,-1,0,1,127,128,65535,MAX-1,MAX]
    tests = 0
    for x in edge:
        for y in edge: check_pair(x,y); tests += 1
    rng = 0x31415926
    for _ in range(100000):
        rng = (rng*1664525+1013904223) & MASK; u = rng
        rng = (rng*1664525+1013904223) & MASK; x,y = decode(u),decode(rng)
        check_pair(x,y)
        if (threefourths(x) != trunc_div(x*3,4) or mul3div4(x) != trunc_div(decode(u*3),4)
            or div16(x) != trunc_div(x,16) or odd_ones(u) != u.bit_count()%2
            or (leftmost_one(u) & MASK) != (1 << (u.bit_length()-1) if u else 0)):
            raise RuntimeError(x)
        for k in range(32):
            rot = ((u << k) | (u >> (32-k))) & MASK
            if srl(u,k) != u >> k or sra(x,k) != x//(1 << k) or rotate_left(u,k) != rot:
                raise RuntimeError((x,k))
            if k < 31 and divide_power2(x,k) != trunc_div(x,1 << k): raise RuntimeError((x,k))
        for n in range(1,33):
            lim = 1 << (n-1)
            if fits_bits(x,n) != int(-lim <= x < lim) or (lower_one_mask(n) & MASK) != (1 << n)-1:
                raise RuntimeError((x,n))
        tests += 1
    a = [1,2,3,4,5]; reverse_array(a)
    if a != [5,4,3,2,1] or sum_elements([1,2,3]) != 6 or sum_elements([]) != 0 or not strlonger(b'abcd',b'ab'):
        raise RuntimeError('sequence')
    if (replace_byte(0x12345678,2,0xAB) != 0x12AB5678 or xbyte(0x80FF017F,3) != -128
        or any_one(0) or not any_zero(0) or low_any_one(256) or not high_any_zero(0)
        or any_odd_one(0x55555555) or bool_or(0x69,0x55) != 0x7D or bool_xor(0x69,0x55) != 0x3C
        or not int_size_is_32()): raise RuntimeError('bits')
    target = bytearray(4)
    if copy_int(42,target,-1) or not copy_int(42,target,4) or ctypes.c_int.from_buffer(target).value != 42:
        raise RuntimeError('copy')
    size_max = (1 << (8*ctypes.sizeof(ctypes.c_size_t)))-1
    if checked_calloc(17,3) != bytes(51) or checked_calloc(size_max,2) is not None or checked_calloc(0,4) is not None:
        raise RuntimeError('allocation')
    data = copy_elements([bytes(ctypes.c_int(17)),bytes(ctypes.c_int(-4))],2,4)
    if data != bytes(ctypes.c_int(17))+bytes(ctypes.c_int(-4)): raise RuntimeError('elements')
    print(f'integer_cases={tests} shifts={100000*32} widths={100000*32} status=ok')
    print(f'endian={"little" if is_little_endian() else "big"} int={ctypes.sizeof(ctypes.c_int)} long={ctypes.sizeof(ctypes.c_long)} double={ctypes.sizeof(ctypes.c_double)}')
    print('short12345='+show_short(12345)); print('long12345='+show_long(12345));print('double1='+show_double(1.0))
    print(f'reverse=5,4,3,2,1 replace={replace_byte(0x12345678,2,0xAB):08x} xbyte={xbyte(0x80FF017F,3)} threefourths(-7)={threefourths(-7)}')

if __name__ == '__main__': main()
