#!/usr/bin/env python3
"""Chapter 7: C_n semidirect C_m, with t*r*t^-1 = r^u."""
import math
import sys


def multiply(a, b, n, m, u):
    i, j = a % n, a // n
    k, ell = b % n, b // n
    return (i + pow(u, j, n) * k) % n + n * ((j + ell) % m)


def element_order(a, n, m, u):
    x = 0
    for k in range(1, n * m + 1):
        x = multiply(x, a, n, m, u)
        if x == 0:
            return k
    raise ValueError('invalid group parameters')


def main(args):
    if not args:
        args = ['4', '2', '3']
    if len(args) != 3 or any(not s.isascii() or not s.isdecimal() for s in args):
        raise ValueError('usage: products.py n m u')
    n, m, u = map(int, args)
    if not (2 <= n <= 12 and 1 <= m <= 6 and n * m <= 24 and 0 <= u < n):
        raise ValueError('require 2<=n<=12, 1<=m<=6, n*m<=24, 0<=u<n')
    if math.gcd(u, n) != 1 or pow(u, m, n) != 1:
        raise ValueError('u must be a unit modulo n with u^m=1 mod n')
    size = n * m
    print(f'n={n} m={m} u={u}; id=i+n*j represents r^i t^j')
    for a in range(size):
        print(f'{a} ({a%n},{a//n}) order={element_order(a,n,m,u)} quotient={a//n}')
    print('TABLE')
    for a in range(size):
        print(' '.join(str(multiply(a,b,n,m,u)) for b in range(size)))
    print('QUOTIENT C' + str(m))
    for j in range(m):
        print(str(j) + ': ' + ','.join(str(i + n*j) for i in range(n)))


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print('error:', error, file=sys.stderr)
        sys.exit(2)
