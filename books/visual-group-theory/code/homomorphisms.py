#!/usr/bin/env python3
"""List every homomorphism C_m -> C_n, with kernel, image and quotient fibers."""
import sys


def maps(m, n):
    # The image k of 1 must respect the relation m*1 = 0.
    for k in range(n):
        if m * k % n == 0:
            values = [x * k % n for x in range(m)]
            kernel = [x for x, y in enumerate(values) if y == 0]
            image = sorted(set(values))
            fibers = [(y, [x for x, value in enumerate(values) if value == y])
                      for y in image]
            yield k, values, kernel, image, fibers


def show(xs):
    return '{' + ','.join(map(str, xs)) + '}'


def main(argv):
    if len(argv) not in (0, 2):
        raise ValueError('usage: homomorphisms.py [m n], 1 <= m,n <= 12')
    if any(len(s) > 2 or not s.isascii() or not s.isdecimal() for s in argv):
        raise ValueError('m and n must be decimal integers')
    m, n = map(int, argv) if argv else (12, 8)
    if not (1 <= m <= 12 and 1 <= n <= 12):
        raise ValueError('m and n must lie between 1 and 12')
    print(f'C{m} -> C{n}')
    count = 0
    for k, values, kernel, image, fibers in maps(m, n):
        count += 1
        print(f'k={k} values={show(values)}')
        print(f'kernel={show(kernel)} image={show(image)} '
              f'injective={"yes" if len(kernel) == 1 else "no"} '
              f'surjective={"yes" if len(image) == n else "no"}')
        for y, fiber in fibers:
            print(f'fiber {show(fiber)} -> {y}')
    print(f'homomorphisms={count}')


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
