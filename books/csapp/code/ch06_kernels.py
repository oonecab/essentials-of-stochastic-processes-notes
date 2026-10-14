"""Checked tiled transpose and symmetric Boolean closure; Python timing includes interpreter cost."""
import sys
import time


def transpose(dst, src, n, tile=16):
    if n < 0 or tile < 1 or len(src) != n*n or len(dst) != n*n or src is dst:
        raise ValueError('separate square arrays and positive tile required')
    for ii in range(0, n, tile):
        for jj in range(0, n, tile):
            for i in range(ii, min(ii+tile, n)):
                for j in range(jj, min(jj+tile, n)):
                    dst[j*n+i] = src[i*n+j]


def undirect(g, n, tile=16):
    if n < 0 or tile < 1 or len(g) != n*n or any(v not in (0, 1) for v in g):
        raise ValueError('Boolean square array and positive tile required')
    for ii in range(0, n, tile):
        for jj in range(ii, n, tile):
            for i in range(ii, min(ii+tile, n)):
                for j in range(max(jj, i+1), min(jj+tile, n)):
                    v = g[i*n+j] | g[j*n+i]
                    g[i*n+j] = g[j*n+i] = v


def data(n, graph=False):
    return [int((i*3+j*7) % 11 == 0) if graph else (i*17+j*3) % 1024
            for i in range(n) for j in range(n)]


def graph_plain(g, n):
    for i in range(n):
        for j in range(n):
            g[j*n+i] = int(bool(g[j*n+i] or g[i*n+j]))


def verify():
    count = 0
    for n in (0, 1, 2, 3, 7, 16, 17, 31, 32, 33, 64):
        for tile in (1, 2, 7, 16, 32):
            a = data(n)
            dst = [0] * (n*n)
            transpose(dst, a, n, tile)
            expected = [a[i*n+j] for j in range(n) for i in range(n)]
            if dst != expected:
                raise RuntimeError('transpose mismatch')
            a = data(n, True)
            g = a.copy()
            undirect(g, n, tile)
            if any(g[i*n+j] != (a[i*n+j] | a[j*n+i]) for i in range(n) for j in range(n)):
                raise RuntimeError('graph mismatch')
            count += 1
    print(f'dimensions=11 tile-cases={count} transpose=PASS undirect=PASS')


def benchmark(n, repeat):
    if not 1 <= n <= 2048 or not 1 <= repeat <= 31:
        raise ValueError('n 1..2048, repeats 1..31')
    for name, tile in [('transpose_plain', n), ('transpose_tiled16', 16), ('transpose_tiled32', 32)]:
        a, dst = data(n), [0] * (n*n)
        times = []
        for _ in range(repeat):
            start = time.perf_counter()
            transpose(dst, a, n, tile)
            times.append(time.perf_counter()-start)
        print(f'{name} n={n} best_ms={min(times)*1000:.3f} checksum={sum(dst)}')
    for name, tile in [('graph_plain', 0), ('graph_triangle', n), ('graph_tiled16', 16)]:
        a = data(n, True)
        times = []
        for _ in range(repeat):
            g = a.copy()
            start = time.perf_counter()
            if tile:
                undirect(g, n, tile)
            else:
                graph_plain(g, n)
            times.append(time.perf_counter()-start)
        print(f'{name} n={n} best_ms={min(times)*1000:.3f} checksum={sum(g)}')


if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            verify()
        elif len(sys.argv) == 4 and sys.argv[1] == '--bench':
            benchmark(int(sys.argv[2]), int(sys.argv[3]))
        else:
            raise ValueError('usage: [--bench n repeats]')
    except (ValueError, MemoryError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
