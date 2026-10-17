"""Finite sigma fields and cover outer measures; at most eight labelled points."""
import json
import re
import sys


def space(n):
    if not isinstance(n, int) or not 1 <= n <= 8:
        raise ValueError('n must be an integer from 1 to 8')
    return (1 << n) - 1


def sigma_field(n, generators):
    full = space(n)
    if any(not isinstance(g, int) or not 0 <= g <= full for g in generators):
        raise ValueError('generator is outside the finite space')
    atoms = [full]
    for generator in generators:
        atoms = [part for atom in atoms
                 for part in (atom & generator, atom & (full ^ generator)) if part]
    atoms.sort()
    family = [0]
    for atom in atoms:
        family += [member | atom for member in family]
    return {'atoms': atoms, 'sets': sorted(family)}


def outer_measure(n, offers):
    full = space(n)
    if len(offers) > 256:
        raise ValueError("at most 256 cover options")
    for mask, cost in offers:
        if not isinstance(mask, int) or not 0 <= mask <= full:
            raise ValueError('cover is outside the finite space')
        if not isinstance(cost, int) or not 0 <= cost <= 1000000:
            raise ValueError('cost must be an integer from 0 to 1000000')
    infinity = float('inf')
    costs = [infinity] * (full + 1)
    costs[0] = 0
    # Union can only add bits, so nontrivial transitions increase the mask.
    for covered in range(full + 1):
        for mask, cost in offers:
            target = covered | mask
            costs[target] = min(costs[target], costs[covered] + cost)
    tau = [min(costs[covered] for covered in range(full + 1)
               if covered & target == target) for target in range(full + 1)]
    measurable = [a for a in range(full + 1)
                  if all(tau[d] == tau[d & a] + tau[d & (full ^ a)]
                         for d in range(full + 1))]
    return {'outer': [None if x == infinity else x for x in tau],
            'measurable': measurable}


def integer(token):
    if not re.fullmatch(r'-?[0-9]+', token):
        raise ValueError('expected ASCII integer without whitespace or plus')
    return int(token)


def main(argv):
    if len(argv) < 2:
        raise ValueError('usage: sigma n [mask ...] | outer n [mask:cost ...]')
    mode, n = argv[0], integer(argv[1])
    if mode == 'sigma':
        result = sigma_field(n, [integer(x) for x in argv[2:]])
    elif mode == 'outer':
        offers = []
        for item in argv[2:]:
            parts = item.split(':')
            if len(parts) != 2 or len(parts[0]) >= 32:
                raise ValueError('expected mask:cost')
            offers.append(tuple(map(integer, parts)))
        result = outer_measure(n, offers)
    else:
        raise ValueError('mode must be sigma or outer')
    print(json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
