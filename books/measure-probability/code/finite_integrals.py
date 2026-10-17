#!/usr/bin/env python3
"""Exact finite weighted integration, signed decomposition and conditioning."""
import json
from math import gcd
import re
import sys


def vector(text, low, high):
    if len(text) > 127 or not re.fullmatch(r'-?[0-9]+(?:,-?[0-9]+)*', text):
        raise ValueError('expected comma-separated integers')
    values = [int(x) for x in text.split(',')]
    if not 1 <= len(values) <= 8 or any(not low <= x <= high for x in values):
        raise ValueError('vector length or integer outside allowed range')
    return values


def ratio(numerator, denominator):
    common = gcd(abs(numerator), denominator)
    return [numerator // common, denominator // common]


def calculate(weights, values, groups, signed):
    mass = sum(weights)
    integral = sum(w * v for w, v in zip(weights, values))
    block_mass, conditional = [], []
    for group in groups:
        total = sum(w for w, g in zip(weights, groups) if g == group)
        amount = sum(w * v for w, v, g in zip(weights, values, groups) if g == group)
        block_mass.append(total)
        conditional.append(ratio(amount, total) if total else [0, 1])
    return {
        'mass': mass,
        'integral': integral,
        'positive_integral': sum(w * max(v, 0) for w, v in zip(weights, values)),
        'negative_integral': sum(w * max(-v, 0) for w, v in zip(weights, values)),
        'second_moment_integral': sum(w * v * v for w, v in zip(weights, values)),
        'expectation': ratio(integral, mass),
        'block_mass': block_mass,
        'conditional': conditional,
        'jordan_positive': [max(s, 0) for s in signed],
        'jordan_negative': [max(-s, 0) for s in signed],
        'variation_total': sum(abs(s) for s in signed),
        'ac_masses': [s if w else 0 for w, s in zip(weights, signed)],
        'singular_masses': [0 if w else s for w, s in zip(weights, signed)],
        'density': [ratio(s, w) if w else [0, 1] for w, s in zip(weights, signed)],
        'absolute_continuous': all(w != 0 or s == 0 for w, s in zip(weights, signed)),
    }


def main():
    try:
        if len(sys.argv) != 5:
            raise ValueError('usage: finite_integrals weights values groups signed')
        weights = vector(sys.argv[1], 0, 1000)
        values = vector(sys.argv[2], -1000, 1000)
        groups = vector(sys.argv[3], 0, 7)
        signed = vector(sys.argv[4], -1000, 1000)
        n = len(weights)
        if any(len(v) != n for v in (values, groups, signed)):
            raise ValueError('vector lengths differ')
        if not sum(weights) or any(g >= n for g in groups):
            raise ValueError('positive total mass and group labels below n required')
        result = calculate(weights, values, groups, signed)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
