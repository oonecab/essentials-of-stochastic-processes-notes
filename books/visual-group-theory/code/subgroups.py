#!/usr/bin/env python3
"""Chapter 6: all subgroups and both coset partitions of D_n, 1 <= n <= 6."""
import sys


def multiply(a, b, n):
    i, j = a % n, a // n
    k, ell = b % n, b // n
    return (i + (-1 if j else 1) * k) % n + n * ((j + ell) % 2)


def members(mask, size):
    return [a for a in range(size) if mask & (1 << a)]


def cosets(subgroup, n, right=False):
    result = set()
    for g in range(2 * n):
        image = [multiply(h, g, n) if right else multiply(g, h, n)
                 for h in subgroup]
        result.add(sum(1 << x for x in image))
    return sorted(result)


def set_text(mask, size):
    return '{' + ','.join(map(str, members(mask, size))) + '}'


def main(args):
    if len(args) > 1 or (args and (not args[0].isascii() or not args[0].isdecimal())):
        raise ValueError('expected an integer n in 1..6')
    n = int(args[0]) if args else 4
    if not 1 <= n <= 6:
        raise ValueError('n must be in 1..6 (subset enumeration is exponential)')
    size = 2 * n
    print(f'D{n}: index i+n*j means r^i f^j; identity=0')
    count = 0
    for mask in range(1, 1 << size, 2):  # only sets containing identity 0
        subgroup = members(mask, size)
        if any(not mask & (1 << multiply(a, b, n)) for a in subgroup for b in subgroup):
            continue
        # For a nonempty FINITE subset, product closure implies inverse closure.
        left, right = cosets(subgroup, n), cosets(subgroup, n, True)
        count += 1
        print('H=' + set_text(mask, size), f'order={len(subgroup)}',
              f'index={size // len(subgroup)}', 'normal=' + ('yes' if left == right else 'no'))
        print('L', '|'.join(set_text(x, size) for x in left))
        print('R', '|'.join(set_text(x, size) for x in right))
    print('subgroups=' + str(count))


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print('error:', error, file=sys.stderr)
        sys.exit(2)
