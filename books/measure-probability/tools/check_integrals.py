#!/usr/bin/env python3
"""Independent level-set, subset and defining-integral checks for finite models."""
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def level_integral(weights, values):
    # Integrate the step-function survival curve, rather than summing w_i f_i.
    def positive(vals):
        levels = sorted({0, *(max(x, 0) for x in vals)})
        return sum((b-a)*sum(w for w, x in zip(weights, vals) if x >= b)
                   for a, b in zip(levels, levels[1:]))
    return positive(values)-positive([-x for x in values])


def verify(row, result):
    weights, values, groups, signed = row
    n, mass = len(weights), sum(weights)
    integral = level_integral(weights, values)
    require(result['mass'] == mass and result['integral'] == integral, 'level-set integral differs')
    require(result['positive_integral'] == level_integral(weights, [max(x, 0) for x in values]), 'positive integral')
    require(result['negative_integral'] == level_integral(weights, [max(-x, 0) for x in values]), 'negative integral')
    require(result['second_moment_integral'] == level_integral(weights, [x*x for x in values]), 'second moment')
    require(F(*result['expectation']) == F(integral, mass), 'normalization')
    cond, density = [F(*v) for v in result['conditional']], [F(*v) for v in result['density']]
    subsets = [tuple(i for i in range(n) if mask >> i & 1) for mask in range(1 << n)]
    for a in subsets:
        sub = [sum(signed[i] for i in b) for b in subsets if set(b) <= set(a)]
        require(sum(result['jordan_positive'][i] for i in a) == max(sub), 'Jordan supremum formula')
        require(sum(result['jordan_negative'][i] for i in a) == -min(sub), 'Jordan infimum formula')
        require(sum(weights[i]*density[i] for i in a) == sum(result['ac_masses'][i] for i in a), 'RN integral definition')
        require(sum(signed[i] for i in a) == sum(result['ac_masses'][i]+result['singular_masses'][i] for i in a), 'Lebesgue sum')
        if all((groups[i] == groups[j]) <= ((i in a) == (j in a)) for i in range(n) for j in range(n)):
            require(sum(weights[i]*cond[i] for i in a) == sum(weights[i]*values[i] for i in a), 'conditional event identity')
    require(result['variation_total'] == max(sum(signed[i] for i in a) for a in subsets)-min(sum(signed[i] for i in a) for a in subsets), 'total variation')
    require(result['absolute_continuous'] == all(sum(signed[i] for i in a) == 0 for a in subsets if sum(weights[i] for i in a) == 0), 'null-set absolute continuity')
    for i in range(n):
        block = [j for j in range(n) if groups[j] == groups[i]]
        require(result['block_mass'][i] == sum(weights[j] for j in block), 'block mass')
        require(all(cond[i] == cond[j] for j in block), 'conditional measurability')
        if result['block_mass'][i] == 0:
            require(cond[i] == 0, 'zero-block version')
        require(weights[i] == 0 or result['singular_masses'][i] == 0, 'singular support')
        require(weights[i] != 0 or result['ac_masses'][i] == 0, 'AC null point')
    require(sum(weights[i]*values[i]*values[i] for i in range(n)) ==
            sum(weights[i]*(values[i]-cond[i])**2 for i in range(n))+sum(weights[i]*cond[i]**2 for i in range(n)), 'L2 projection identity')
    for pair in [result['expectation'], *result['conditional'], *result['density']]:
        value = F(*pair)
        require(pair == [value.numerator, value.denominator], 'fraction is not normalized')


def run(run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    cases = [([1,2,0,1],[-2,1,9,4],[0,0,1,1],[2,-1,3,0]),
             ([0,1],[1000,-1000],[0,1],[5,0]),
             ([1000]*8,[-1000,1000]*4,list(range(8)),[-1000,1000]*4)]
    for weights in itertools.product((0,1,2), repeat=2):
        if sum(weights):
            for groups in ((0,0),(0,1)):
                cases.append((list(weights),[-2,3],list(groups),[1,-2]))
    rng = random.Random(2026101734)
    for n in range(1,6):
        for _ in range(12):
            weights = [rng.randrange(5) for _ in range(n)]
            weights[0] += 1
            cases.append((weights,[rng.randrange(-8,9) for _ in range(n)],
                          [rng.randrange(n) for _ in range(n)],[rng.randrange(-5,6) for _ in range(n)]))
    drivers, builds = [[sys.executable,str(ROOT/'code/finite_integrals.py')]], []
    for suffix, flags in [('release',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
        binary = run_dir/f'finite_integrals-{suffix}'
        command = ['clang','-std=c11','-Wall','-Wextra','-Werror','-pedantic',*flags,str(ROOT/'code/finite_integrals.c'),'-o',str(binary)]
        subprocess.run(command,check=True,capture_output=True,text=True)
        drivers.append([str(binary)])
        builds.append(command)
    malformed = [[],['1','0','0'],['1','0','0','0','0'],['','0','0','0'],
                 ['0','0','0','0'],['-1','0','0','0'],['1001','0','0','0'],
                 ['1','-1001','0','0'],['1','0','1','0'],['1','0','0','1001'],
                 ['1,2','0','0,0','0,0'],['1,','0','0','0'],['+1','0','0','0'],
                 [' 1','0','0','0'],['１','0','0','0'],['1.0','0','0','0'],
                 [','.join(['1']*9),','.join(['0']*9),','.join(['0']*9),','.join(['0']*9)],
                 ['9'*127,'0','0','0'],['0'*127+'1','0','0','0']]
    executions, expected = 0, []
    for driver in drivers:
        for index, row in enumerate(cases):
            args = [','.join(map(str,v)) for v in row]
            proc = subprocess.run(driver+args,capture_output=True,text=True)
            require(proc.returncode == 0 and not proc.stderr,'valid CLI failure: '+proc.stderr[:200])
            result = json.loads(proc.stdout)
            verify(row,result)
            if driver == drivers[0]:
                expected.append(result)
            else:
                require(result == expected[index], 'C/Python output differs')
            executions += 1
        for args in malformed:
            proc = subprocess.run(driver+args,capture_output=True,text=True)
            require(proc.returncode == 2 and not proc.stdout and proc.stderr,'invalid CLI contract differs')
            executions += 1
    require(expected[0]['conditional'] == [[0,1],[0,1],[4,1],[4,1]],'worked conditional table')
    require(expected[0]['integral'] == 4 and expected[0]['second_moment_integral'] == 22,'worked integral table')
    # Correction fixtures are exact counterexamples, separate from general proofs.
    require(F(1,2) > F(1,4) and F(1,2)**2 == F(1,4),'unrooted low-order moments')
    require(len(set([-1,1])) == 2 and {abs(x) for x in [-1,1]} == {1},'moment equality needs absolute value')
    for n in range(1,9):
        for x in [F(-1),F(0),F(1),F(n),F(n+1),F(3,2)]:
            actual = F(sum(k <= x for k in range(1,n+1)),n)
            formula = F(0) if x < 1 else F(1) if x >= n else F(x.numerator//x.denominator,n)
            require(actual == formula,'uniform CDF boundary')
    a, partition = F(2), [F(2), F(5,2), F(4)]
    cdf = lambda x: F(int(x >= a))
    rs_sum = sum(cdf(right)-cdf(left) for left,right in zip(partition,partition[1:]))
    closed_integral = sum(F(1) for atom in [a] if partition[0] <= atom <= partition[-1])
    require(rs_sum == 0 and closed_integral == 1, 'Stieltjes endpoint atom fixture')
    require(sum(F(1,2**n*(1+mass)) for n,mass in enumerate([0,2,0,5],1)) > 0,'zero-measure domination denominator')
    # A wrong conditional value at a zero-weight point in a positive block
    # preserves integrals, but must be rejected because it is not G-measurable.
    mutant = json.loads(json.dumps(expected[0])); mutant['conditional'][2] = [0,1]
    try:
        verify(cases[0],mutant)
    except ValueError as error:
        require(str(error) == 'conditional measurability','wrong mutation reason')
    else:
        raise ValueError('accepted nonmeasurable conditional version')
    return {'cases':len(cases),'invalid_cases':len(malformed),'cli_executions':executions,
            'builds':builds,'oracles':['level-set integral','all-subset Jordan extrema','all conditioning-event identities','RN defining integral','L2 projection'],
            'mutations_rejected':['zero-point conditional measurability'],
            'scope':'finite exact models only; infinite-space proofs reviewed separately'}
