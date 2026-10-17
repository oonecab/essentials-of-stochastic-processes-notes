#!/usr/bin/env python3
"""Chapter 5: permutations of 1..n, with p*q meaning p THEN q."""
import math
import sys


def parse(text):
    fields = text.split(',')
    if not 1 <= len(fields) <= 8 or any(not x.isascii() or not x.isdecimal() for x in fields):
        raise ValueError('use 1..8 comma-separated positive integers')
    p = tuple(int(x) - 1 for x in fields)
    if sorted(p) != list(range(len(p))):
        raise ValueError('each value 1..n must occur exactly once')
    return p


def compose(p, q):
    """Array entries are destinations; visit p[x], then q[p[x]]."""
    return tuple(q[x] for x in p)


def inverse(p):
    q = [0] * len(p)
    for source, destination in enumerate(p):
        q[destination] = source
    return tuple(q)


def cycles(p):
    seen = set()
    result = []
    for start in range(len(p)):
        if start in seen:
            continue
        cycle = []
        x = start
        while x not in seen:
            seen.add(x)
            cycle.append(x)
            x = p[x]
        result.append(cycle)
    return result


def describe(label, p):
    parts = cycles(p)
    text = ''.join('(' + ' '.join(str(x + 1) for x in part) + ')'
                   for part in parts if len(part) > 1) or '()'
    order = math.lcm(*(len(part) for part in parts))
    inversions = sum(p[i] > p[j] for i in range(len(p)) for j in range(i + 1, len(p)))
    print(label, ','.join(str(x + 1) for x in p), text,
          'order=' + str(order), 'sign=' + str(-1 if inversions % 2 else 1))


def main(args):
    if not args:
        args = ['2,3,4,1', '2,1,3,4']
    if len(args) != 2:
        raise ValueError('usage: permutations.py p q; e.g. 2,3,4,1 2,1,3,4')
    p, q = map(parse, args)
    if len(p) != len(q):
        raise ValueError('p and q must have the same degree')
    for label, permutation in [('p', p), ('q', q), ('p*q', compose(p, q)),
                               ('q*p', compose(q, p)), ('p^-1', inverse(p)),
                               ('p^2', compose(p, p))]:
        describe(label, permutation)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print('error:', error, file=sys.stderr)
        sys.exit(2)
