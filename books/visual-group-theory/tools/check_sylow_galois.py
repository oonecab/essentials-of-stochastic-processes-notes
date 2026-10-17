"""Independent exact, finite and CLI checks for chapters 9--10."""
from fractions import Fraction as Q
import itertools
import json
import math
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace
from check_algebra import module, need
from check_structures import all_subgroups, closure, table_from_permutations, perm_closure

ROOT = Path(__file__).resolve().parents[1]


def sylow_checks(mod=None):
    mod = mod or module('sylow')
    need(mod.compose((1, 0, 2), (0, 2, 1)) == (2, 0, 1), 'temporal product reversed')
    results = []
    for n in range(2, 6):
        ps = list(itertools.permutations(range(n)))
        table = table_from_permutations(ps)
        # This enumerates every subgroup by adjoining elements, without Sylow conjugation.
        subs = all_subgroups(table)
        for p in (2, 3, 5):
            if p > n:
                continue
            order = math.factorial(n)
            target = 1
            while order % (target * p) == 0:
                target *= p
            expected = {h for h in subs if len(h) == target}
            perms, groups, norms = mod.model(n, p)
            need(perms == ps and {frozenset(g) for g in groups} == expected,
                 'Sylow enumeration does not equal independently generated subgroups')
            need(all(x * len(groups) == order for x in norms), 'normalizer index failed')
            need(len(groups) % p == 1 and (order // target) % len(groups) == 0,
                 'Sylow counting congruence failed')
            results.append({'n': n, 'p': p, 'order': target, 'count': len(groups),
                            'all_subgroups': len(subs)})
    return results


def cubic(a, b):
    """Hand-expanded product in Q[t]/(t^3-2), independent of exponent-loop code."""
    return (a[0]*b[0]+2*(a[1]*b[2]+a[2]*b[1]),
            a[0]*b[1]+a[1]*b[0]+2*a[2]*b[2],
            a[0]*b[2]+a[1]*b[1]+a[2]*b[0])


def pair_product(a, b):
    uu, vv = cubic(a[:3], b[:3]), cubic(a[3:], b[3:])
    uv, vu = cubic(a[:3], b[3:]), cubic(a[3:], b[:3])
    return tuple(x-3*y for x, y in zip(uu, vv)) + tuple(x+y for x, y in zip(uv, vu))


def matrix_image(v, k, sign):
    a, b, c, d, e, f = map(Q, v)
    d, e, f = sign*d, sign*e, sign*f
    for _ in range(k):
        b, c, e, f = (-b-3*e)/2, (-c+3*f)/2, (b-e)/2, (-c-f)/2
    return a, b, c, d, e, f


def galois_checks(mod=None):
    mod = mod or module('galois')
    basis = [tuple(Q(i == j) for j in range(6)) for i in range(6)]
    vectors = basis + [(Q(1),)*6, tuple(map(Q, (-100, 99, 0, 1, 100, -7)))]
    checked = 0
    for a, b in itertools.product(vectors, repeat=2):
        product = pair_product(a, b)
        need(mod.mul(a, b) == product, 'field product disagrees with pair reference')
        for k, sign in itertools.product(range(3), (1, -1)):
            need(mod.automorphism(a, k, sign) == matrix_image(a, k, sign), 'wrong automorphism matrix')
            need(mod.automorphism(product, k, sign) == mod.mul(
                mod.automorphism(a, k, sign), mod.automorphism(b, k, sign)), 'automorphism not multiplicative')
            checked += 1
    for k, e, l, d in itertools.product(range(3), (1, -1), range(3), (1, -1)):
        for v in basis:
            need(mod.automorphism(mod.automorphism(v, l, d), k, e) ==
                 matrix_image(v, (k+e*l) % 3, e*d), 'automorphism composition law failed')
            checked += 1
    need(matrix_image((1,)*6, 1, 1) == (1, -2, 1, 1, 0, -1), 'hand reference invalid')
    return {'multiplication_and_composition_cases': checked, 'basis_dimension': 6}


def trim(a):
    a = list(map(Q, a))
    while a and not a[-1]:
        a.pop()
    return a


def pmul(a, b):
    out = [Q(0)] * max(0, len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return trim(out)


def padd(a, b):
    return trim([(a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0)
                 for i in range(max(len(a), len(b)))])


def pdiv(a, b):
    a, b = trim(a), trim(b)
    q = [Q(0)] * max(0, len(a)-len(b)+1)
    while a and len(a) >= len(b):
        d, c = len(a)-len(b), a[-1]/b[-1]
        q[d] += c
        a = padd(a, [Q(0)]*d+[-c*x for x in b])
    return trim(q), a


def sturm_real_roots(f):
    seq = [trim(f), [Q(i)*x for i, x in enumerate(f)][1:]]
    while seq[-1]:
        rem = pdiv(seq[-2], seq[-1])[1]
        if not rem:
            break
        seq.append([-x for x in rem])
    def variations(direction):
        signs = [(1 if p[-1] > 0 else -1)*direction**(len(p)-1) for p in seq]
        return sum(a != b for a, b in zip(signs, signs[1:]))
    return variations(-1)-variations(1)


def source_checks():
    data = json.loads((ROOT/'notes/sylow_galois_inputs.json').read_text())
    division = [([-1,0,0,1],[-1,1],[1,1,1],[]),
                ([2,0,0,-10,-38,0,20,76],[0,0,0,-2,0,0,4],[5,19],[2]),
                ([-10,16,-7,9],[2,0,1],[-7,9],[4,-2]),
                ([5,-6,0,2],[-4,1],[26,8,2],[109])]
    for a, b, q, r in division:
        need(pdiv(a,b) == (trim(q),trim(r)), 'polynomial long division failed')
    left = pmul(pmul(pmul([12,-1],[26,1]),[-1,1]),[-9,1])
    right = pmul([-40,36],[-850,100])
    need(padd(right,[-x for x in left]) == [31192,-31354,3157,4,1], 'printed 223 rational equation changed')
    factors = [[2,1],[-3,2],[-3,1],[5,-4,4]]
    product = [1]
    for f in factors:
        product = pmul(product,f)
    need(product == [90,-117,83,-6,-28,8], '10.6 factorization wrong')
    need(pmul([1,3],[17,-16,4]) == [17,35,-44,12], '10.24 factorization wrong')
    # psi(x+2) for the real cyclotomic example, using Horner composition.
    translated = []
    for c in reversed([1,3,-3,-4,1,1]):
        translated = padd(pmul(translated,[2,1]),[c])
    need(translated == data['quintics']['five_real'], 'cyclotomic translation wrong')
    counts = {name: sturm_real_roots(f) for name, f in data['quintics'].items()}
    need(counts == {'one_real':1,'three_real':3,'five_real':5}, 'real-root count failed')
    for name, prime in [('one_real',2),('three_real',2),('five_real',11)]:
        f = data['quintics'][name]
        need(f[-1] % prime and all(x % prime == 0 for x in f[:-1]) and f[0] % (prime*prime),
             'Eisenstein condition failed')
    fig = data['figure_10_26']; labels = fig['labels']
    def arrow(cycles):
        out = list(range(len(labels)))
        for cycle in cycles:
            for a,b in zip(cycle,cycle[1:]+cycle[:1]):
                out[labels.index(a)] = labels.index(b)
        return tuple(out)
    a, b = arrow(fig['red_cycles']), arrow(fig['blue_cycles'])
    then = lambda x,y: tuple(y[t] for t in x)
    def power(x,n):
        z = tuple(range(len(x)))
        for _ in range(n): z = then(z,x)
        return z
    e = tuple(range(24))
    need(power(a,4)==e and power(a,2)!=e and power(b,12)==e and power(b,6)!=e, 'source arrow order changed')
    need(power(a,2)==power(b,6) and then(then(a,b),power(a,3))==power(b,11), 'Dic6 relations fail')
    generated = perm_closure([a,b])
    need(len(generated)==24 and len({p[0] for p in generated})==24, 'source diagram not regular Dic6')
    # A5 class equation, found from actual even permutations.
    even = [p for p in itertools.permutations(range(5)) if sum(p[i]>p[j] for i in range(5) for j in range(i+1,5))%2==0]
    table = table_from_permutations(even); inv=[r.index(0) for r in table]
    classes={frozenset(table[table[g][x]][inv[g]] for g in range(60)) for x in range(60)}
    need(sorted(map(len,classes))==[1,12,12,15,20], 'A5 conjugacy class sizes failed')
    sizes=[12,12,15,20]
    normal_sizes={1+sum(s for s,flag in zip(sizes,flags) if flag) for flags in itertools.product([0,1],repeat=4)}
    need({n for n in normal_sizes if 60%n==0}=={1,60}, 'A5 normal subgroup exclusion failed')
    fields=[]
    for q in (3,4,7,8,11):
        def times(a,b):
            if q not in (4,8): return a*b%q
            modulus=7 if q==4 else 11
            out=0
            while b:
                if b&1: out^=a
                b>>=1;a<<=1
                if a&q:a^=modulus
            return out
        plus=(lambda a,b:a^b) if q in (4,8) else (lambda a,b:(a+b)%q)
        for a,b,c in itertools.product(range(q),repeat=3):
            need(times(a,plus(b,c))==plus(times(a,b),times(a,c)), 'finite-field distributivity failed')
            need(times(times(a,b),c)==times(a,times(b,c)), 'finite-field associativity failed')
        need(all(any(times(a,b)==1 for b in range(1,q)) for a in range(1,q)), 'finite-field inverse absent')
        gen=3 if q==7 else 2; orbit=[];x=1
        while x not in orbit: orbit.append(x);x=times(x,gen)
        need(len(orbit)==q-1, 'multiplicative generator wrong')
        if q in (4,8):need(orbit==data['figure_10_29'][f'F{q}']['multiplication_cycle'],'source field arrow mismatch')
        fields.append({'order':q,'multiplicative_cycle':orbit})
    return {'polynomial_divisions':len(division),'quintic_real_roots':counts,
            'source_10_26_order':len(generated),'A5_class_sizes':sorted(map(len,classes)),'finite_fields':fields}


def cli_checks(run_dir):
    rng=random.Random(910)
    good={'sylow':[[],*[list(map(str,(n,p))) for n in range(2,6) for p in (2,3,5) if p<=n]],
          'galois':[[],['0']*6,['100']*6,['-100']*6,*[[str(int(i==j)) for j in range(6)] for i in range(6)],
                    *[[str(rng.randint(-100,100)) for _ in range(6)] for _ in range(20)]]}
    bad={'sylow':[['0','2'],['6','2'],['3','4'],['2','3'],['4'],['4','2','2'],['４','2'],['04','2'],[' 4','2']],
         'galois':[['0'],['0']*5,['0']*7,['101']*6,['-101']*6,['+1']*6,['1.0']*6,['１']*6,['0000']*6,['']*6,['-']*6]}
    builds=[];cases=0
    registered={p['id']:p for p in json.loads((ROOT/'code/programs.json').read_text())['programs']}
    for name in good:
        py=[sys.executable,str(ROOT/f'code/{name}.py')]
        expected=[]
        for args in good[name]:
            result=subprocess.run(py+args,capture_output=True,text=True,check=True)
            need(not result.stderr,'Python stderr for legal input')
            if not args:need(result.stdout==registered[name]['expected_stdout'],'registered default drifted')
            if name=='galois':
                a=tuple(map(Q,args)) if args else (Q(1),)*6
                for k,s in itertools.product(range(3),(1,-1)):
                    value='['+','.join(map(str,matrix_image(a,k,s)))+']'
                    need(f'value={value}\n' in result.stdout,'CLI disagrees with exact matrix')
                value='['+','.join(map(str,pair_product(a,matrix_image(a,0,-1))))+']'
                need(f'z*conjugate(z)={value}\n' in result.stdout,'CLI product disagrees with reference')
            expected.append(result.stdout);cases+=1
        drivers=[py]
        for flags,label in [(['-O2'],'O2'),(['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'],'san')]:
            binary=run_dir/f'{name}-{label}'
            command=['clang','-std=c11','-Wall','-Wextra','-Werror','-pedantic']+flags+[str(ROOT/f'code/{name}.c'),'-o',str(binary)]
            subprocess.run(command,capture_output=True,text=True,check=True);builds.append(' '.join(command))
            drivers.append([str(binary)])
            for args,answer in zip(good[name],expected):
                result=subprocess.run([str(binary)]+args,capture_output=True,text=True)
                need(result.returncode==0 and result.stdout==answer and not result.stderr,'C/Python output mismatch')
                cases+=1
        for driver in drivers:
            for args in bad[name]:
                result=subprocess.run(driver+args,capture_output=True,text=True)
                need(result.returncode==2 and not result.stdout and result.stderr,'invalid CLI input accepted')
                cases+=1
    return {'cases':cases,'builds':builds}


def mutations():
    rejected=[]
    for name,old,new,check in [
        ('sylow','tuple(b[x] for x in a)','tuple(a[x] for x in b)',sylow_checks),
        ('sylow','length = 4 if p == 2 and n >= 4 else p','length = p',sylow_checks),
        ('galois','factor *= -3','factor *= 3',galois_checks),
        ('galois','factor *= 2','factor *= 1',galois_checks)]:
        original=(ROOT/f'code/{name}.py').read_text();changed=original.replace(old,new)
        need(original!=changed,'mutation not applied');namespace={'__name__':'mutant'}
        exec(compile(changed,'mutant','exec'),namespace)
        try:check(SimpleNamespace(**namespace))
        except ValueError:rejected.append(name+': '+old)
        else:raise ValueError('incorrect implementation survived independent oracle')
    return rejected


def run(run_dir):
    return {'sylow':sylow_checks(),'galois':galois_checks(),'source_math':source_checks(),
            'mutations_rejected':mutations(),'cli':cli_checks(run_dir)}
