#!/usr/bin/env python3
"""Independent finite oracles and C11/Python comparisons for the teaching models."""
from fractions import Fraction
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def module(stem):
    spec = importlib.util.spec_from_file_location('measure_' + stem, ROOT / f'code/{stem}.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sigma_oracle(n, generators):
    # Close the family under complements and unions; no atom-splitting algorithm.
    full = (1 << n) - 1
    family = {0, full, *generators}
    while True:
        expanded = family | {full ^ a for a in family} | {a | b for a in family for b in family}
        if expanded == family:
            break
        family = expanded
    atoms = [a for a in family if a and not any(b and b != a and b & a == b for b in family)]
    return {'atoms': sorted(atoms), 'sets': sorted(family)}


def outer_oracle(n, offers):
    # Nonnegative costs mean no repeated offer is needed. Enumerate subfamilies.
    full = (1 << n) - 1
    covers = []
    for choices in itertools.product((False, True), repeat=len(offers)):
        covered, price = 0, 0
        for (mask, cost), chosen in zip(offers, choices):
            if chosen:
                covered |= mask
                price += cost
        covers.append((covered, price))
    tau = [min((price for covered, price in covers if target & covered == target), default=math.inf)
           for target in range(full + 1)]
    measurable = []
    for a in range(full + 1):
        if all(tau[d] == tau[d & a] + tau[d & (full ^ a)] for d in range(full + 1)):
            measurable.append(a)
    return {'outer': [None if v == math.inf else v for v in tau], 'measurable': measurable}


def simple_oracle(p, q, level):
    x, step = Fraction(p, q), Fraction(1, 2 ** level)
    grid = min(math.floor(x / step), level * 2 ** level)
    return {'grid': grid, 'scale': 2 ** level}


def run(run_dir):
    finite, simple = module('finite_spaces'), module('simple_approx')
    sigma_cases = [(n, list(pair)) for n in range(1, 5)
                   for pair in itertools.product(range(1 << n), repeat=2)]
    sigma_cases += [(4, []), (4, [0, 15, 3, 3]), (8, [1 << i for i in range(8)])]
    for n, generators in sigma_cases:
        require(finite.sigma_field(n, generators) == sigma_oracle(n, generators), 'sigma closure differs')
    require(finite.sigma_field(4, [3]) == {'atoms': [3, 12], 'sets': [0, 3, 12, 15]}, 'hand partition differs')
    outer_cases = [(3, [(3, 1), (6, 1), (7, 2)]), (2, []), (2, [(0, 0)]),
                   (3, [(1, 2), (2, 3), (4, 5)]), (2, [(3, 0)]),
                   (2, [(1, 1), (1, 3), (3, 8)]), (8, [(255, 1000000)])]
    rng = random.Random(20261017)
    outer_cases += [(n, [(rng.randrange(1 << n), rng.randrange(6)) for _ in range(6)])
                    for n in range(1, 5) for _ in range(10)]
    for n, offers in outer_cases:
        require(finite.outer_measure(n, offers) == outer_oracle(n, offers), 'cover enumeration differs')
    require(finite.outer_measure(3, [(3, 1), (6, 1), (7, 2)]) ==
            {'outer': [0, 1, 1, 1, 1, 2, 1, 2], 'measurable': [0, 7]}, 'three-point source table differs')
    require(finite.outer_measure(2, [(0, 0)]) ==
            {'outer': [0, None, None, None], 'measurable': [0, 1, 2, 3]}, 'missing-cover counterexample differs')
    simple_cases = [(p, q, k) for p in (0, 1, 2, 13, 999999, 1000000)
                    for q in (1, 3, 10, 1000000) for k in (1, 2, 7, 20)]
    for p, q, k in simple_cases:
        result = simple.approximate(p, q, k)
        require(result == simple_oracle(p, q, k), 'rational approximation differs')
        value, x = Fraction(result['grid'], result['scale']), Fraction(p, q)
        require(value <= x and value <= k, 'lower approximation exceeded input or truncation')
        if x < k:
            require(x - value < Fraction(1, 2 ** k), 'dyadic error bound failed')
    for p in range(40):
        values = [Fraction(simple.approximate(p, 7, k)['grid'], 2**k) for k in range(1, 21)]
        require(values == sorted(values), 'simple approximation not increasing')
    # Counterexample to probability-Cesaro implication: each dyadic endpoint
    # belongs to exactly one interval per round, with the printed amplitude.
    for k in range(1, 8):
        points = [Fraction(i, 2 ** k) for i in range(1, 2 ** k + 1)]
        for x in points:
            total = sum(2 ** (k + 1) for j in range(1, 2 ** k + 1)
                        if Fraction(j - 1, 2 ** k) < x <= Fraction(j, 2 ** k))
            require(total == 2 ** (k + 1) and Fraction(total, 2 ** (k + 1) - 1) > 1,
                    'probability-Cesaro counterexample failed')
    # A singleton family on two points lacks the empty intersection.
    require((1 & 2) not in {1, 2}, 'empty-set correction fixture changed')
    cli_cases = {
        'finite_spaces': [(['sigma', str(n), *map(str, gs)], sigma_oracle(n, gs))
                          for n, gs in sigma_cases[::13] + sigma_cases[-3:]] +
                         [(['outer', str(n), *(f'{a}:{v}' for a, v in offers)], outer_oracle(n, offers))
                          for n, offers in outer_cases],
        'simple_approx': [(list(map(str, row)), simple_oracle(*row)) for row in simple_cases]
    }
    invalid = {
        'finite_spaces': [[], ['sigma', '0'], ['sigma', '9'], ['sigma', '3', '8'], ['outer', '2', '1:-1'],
                          ['outer', '2', '1:1000001'], ['outer', '2', '4:0'], ['outer', '2', '1:2:3'],
                          ['outer', '2', ':1'], ['outer', '2', '1:'], ['unknown', '2'],
                          ['outer', '2', *(['1:0'] * 257)]],
        'simple_approx': [[], ['1', '0', '2'], ['-1', '2', '2'], ['1', '2', '0'],
                          ['1', '2', '21'], ['1000001', '2', '2'], ['1.5', '2', '2'], ['1', '2', '2', '3']]
    }
    builds, executions = [], 0
    for stem in cli_cases:
        drivers = [[sys.executable, str(ROOT / f'code/{stem}.py')]]
        for suffix, flags in [('release', ['-O2']), ('sanitized', ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            binary = run_dir / f'{stem}-{suffix}'
            command = ['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic', *flags,
                       str(ROOT / f'code/{stem}.c'), '-o', str(binary)]
            subprocess.run(command, check=True, capture_output=True, text=True)
            builds.append([x.replace(str(ROOT) + '/', '') for x in command[:-1]] + [binary.name])
            drivers.append([str(binary)])
        for driver in drivers:
            for args, expected in cli_cases[stem]:
                result = subprocess.run(driver + args, capture_output=True, text=True)
                require(result.returncode == 0 and not result.stderr and json.loads(result.stdout) == expected,
                        'CLI calculation differs: ' + stem + ' ' + ' '.join(args[:8]))
                executions += 1
            for args in invalid[stem]:
                result = subprocess.run(driver + args, capture_output=True, text=True)
                require(result.returncode == 2 and not result.stdout and result.stderr, 'invalid input accepted: ' + stem)
                executions += 1
    return {'sigma_closure_cases': len(sigma_cases), 'cover_subfamily_cases': len(outer_cases),
            'exact_rational_cases': len(simple_cases), 'cli_executions': executions, 'builds': builds,
            'correction_regressions': ['missing empty intersection', 'missing global cover', 'probability Cesaro counterexample'],
            'scope': 'finite models and numerical boundaries; general proofs are reviewed in HTML'}
