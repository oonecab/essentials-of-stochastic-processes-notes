#!/usr/bin/env python3
"""Independently regenerate numeric references from inputs, without importing programs."""
from fractions import Fraction as F
from pathlib import Path
import argparse
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def solve(a, b):
    n = len(b)
    rows = [list(row)+[value] for row, value in zip(a, b)]
    for col in range(n):
        pivot = next(i for i in range(col,n) if rows[i][col])
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [v/scale for v in rows[col]]
        for i in range(n):
            if i != col:
                scale = rows[i][col]
                rows[i] = [x-scale*y for x,y in zip(rows[i],rows[col])]
    return [row[-1] for row in rows]


def linear_reference(case):
    p = [[F(str(v)) for v in row] for row in case['matrix']]
    n, mode = len(p), case['mode']
    if mode == 'psteps':
        v = [F(str(x)) for x in case['initial']]
        for _ in range(case['steps']):
            v = [sum((v[i]*p[i][j] for i in range(n)),F(0)) for j in range(n)]
        return [float(x) for x in v]
    q = mode.startswith('q')
    if 'station' in mode:
        a = [[p[j][i]-int(not q and i==j) for j in range(n)] for i in range(n-1)]+[[F(1)]*n]
        b = [F(0)]*(n-1)+[F(1)]
    else:
        fixed = case['fixed']
        a = [[F(int(i==j)) if fixed[i]>=0 else F(int(not q and i==j))-p[i][j]
              for j in range(n)] for i in range(n)]
        b = [F(str(fixed[i])) if fixed[i]>=0 else F(int(mode.endswith('time'))) for i in range(n)]
    return [float(x) for x in solve(a,b)]


def finance_reference(case):
    fields = case['input'].split()
    n, kind, american = int(fields[0]), int(fields[6]), int(fields[7])
    s0,u,d,r,k,barrier = map(F,[fields[i] for i in [1,2,3,4,5,8]])
    R = 1+r; p = (R-d)/(u-d)
    layers = []
    for depth in range(n+1):
        layer = {}
        for index in range(1<<depth):
            path = ''.join('H' if (index>>(depth-j-1))&1==0 else 'T' for j in range(depth))
            stocks = [s0]
            for turn in path:
                stocks.append(stocks[-1]*(u if turn=='H' else d))
            s = stocks[-1]
            payoffs = [max(s-k,0),max(k-s,0),max(sum(stocks,F(0))/len(stocks)-k,0),
                       max(stocks)-s,s-min(stocks),int(s>k),min(max(s-k,0),60),
                       0 if max(stocks)>=barrier else max(k-s,0)]
            layer[path] = {'s':s, 'immediate':payoffs[kind]}
        layers.append(layer)
    for depth in range(n,-1,-1):
        for path,row in layers[depth].items():
            if depth == n:
                row.update(v=row['immediate'],delta=F(0),action=2)
            else:
                up,down = layers[depth+1][path+'H']['v'],layers[depth+1][path+'T']['v']
                cv = (p*up+(1-p)*down)/R
                action = int(american and row['immediate']>0 and row['immediate']>=cv)
                row.update(v=row['immediate'] if action else cv,
                           delta=(up-down)/(row['s']*(u-d)),action=action)
    return [dict(path=path or '-',s=float(row['s']),v=float(row['v']),delta=float(row['delta']),action=row['action'])
            for layer in layers for path,row in layer.items()]


def bs_reference(case):
    s,k,t,r,vol = map(float,case['input'].split())
    discounted = k*math.exp(-r*t)
    if t==0 or vol==0:
        return [max(s-discounted,0),max(discounted-s,0),1 if s>discounted else 0 if s<discounted else 0.5]
    z = vol*math.sqrt(t)
    d1 = (math.log(s)-math.log(k))/z + r*math.sqrt(t)/vol + z/2
    d2 = d1-z
    normal = lambda x: math.erfc(-x/math.sqrt(2))/2
    return [s*normal(d1)-discounted*normal(d2), discounted*normal(-d2)-s*normal(-d1), normal(d1)]


def reference(case):
    return {'linear':linear_reference,'finance':finance_reference,'bs':bs_reference}[case['program']](case)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Replace expected numbers after reviewing input cases')
    args = parser.parse_args()
    path = ROOT/'tools/notes_cases.json'; cases = json.loads(path.read_text())
    for i,case in enumerate(cases):
        regenerated = reference(case)
        if args.write:
            case['expected'] = regenerated
        elif case['program']=='finance':
            for a,b in zip(case['expected'],regenerated):
                if a['path']!=b['path'] or a['action']!=b['action'] or any(not math.isclose(a[k],b[k],abs_tol=5e-12,rel_tol=8e-12) for k in ['s','v','delta']):
                    raise ValueError('Fixture reference differs: '+str(i))
            if len(case['expected'])!=len(regenerated):raise ValueError('Fixture node count differs')
        elif len(case['expected'])!=len(regenerated) or any(not math.isclose(a,b,abs_tol=5e-12,rel_tol=8e-12) for a,b in zip(case['expected'],regenerated)):
            raise ValueError('Fixture reference differs: '+str(i))
    if args.write:path.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'independent_references':len(cases),'status':'pass','arithmetic':'Fraction elimination/path enumeration; analytic normal CDF'},ensure_ascii=False))


if __name__=='__main__':main()
