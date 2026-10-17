"""Exact dyadic lower approximation for a nonnegative rational input."""
import json
import re
import sys


def approximate(p, q, level):
    if not 0 <= p <= 1000000 or not 1 <= q <= 1000000 or not 1 <= level <= 20:
        raise ValueError('require 0<=p<=1000000, 1<=q<=1000000, 1<=level<=20')
    scale = 1 << level
    grid = min(level * scale, p * scale // q)
    return {'grid': grid, 'scale': scale}


def integer(token):
    if not re.fullmatch(r'[0-9]+', token):
        raise ValueError('expected unsigned ASCII integer')
    return int(token)


if __name__ == '__main__':
    try:
        if len(sys.argv) != 4:
            raise ValueError('usage: simple_approx.py numerator denominator level')
        print(json.dumps(approximate(*map(integer, sys.argv[1:])), separators=(',', ':')))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
