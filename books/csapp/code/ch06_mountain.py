"""Same scan and byte accounting as C. Python timings include interpreter overhead."""
from array import array
import sys
import time


def scan(a, n, stride):
    if stride < 1 or not 0 <= n <= len(a):
        raise ValueError('invalid scan bounds')
    i = x = y = z = w = 0
    while i + 3*stride < n:
        x += a[i]
        y += a[i+stride]
        z += a[i+2*stride]
        w += a[i+3*stride]
        i += 4*stride
    while i < n:
        x += a[i]
        i += stride
    return (x+y+z+w) & ((1 << 64)-1)


def verify():
    a = list(range(65))
    checks = 0
    for n in range(65):
        for stride in range(1, 18):
            if scan(a, n, stride) != sum(range(0, n, stride)):
                raise RuntimeError('scan mismatch')
            checks += 1
    print(f'scan-cases={checks} checksum=PASS')


def benchmark():
    a = array('Q', range(128*1024*1024//8))
    if a.itemsize != 8:
        raise RuntimeError('8-byte elements required')
    print('size_bytes,stride_elements,useful_bytes_per_scan,MB_per_second')
    for power in range(14, 28):
        size = 1 << power
        for stride in (1, 2, 4, 8, 16):
            n = size//8
            count = (n+stride-1)//stride
            reps = max(1, (32*1024*1024)//(count*8))
            expected = scan(a, n, stride)
            times = []
            for _ in range(3):
                start = time.perf_counter()
                for _ in range(reps):
                    result = scan(a, n, stride)
                times.append(time.perf_counter()-start)
                if result != expected:
                    raise RuntimeError('scan changed')
            print(f'{size},{stride},{count*8},{count*8*reps/min(times)/1e6:.2f}')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        verify()
    elif sys.argv[1:] == ['--bench']:
        benchmark()
    else:
        sys.exit(2)
