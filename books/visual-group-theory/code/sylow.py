#!/usr/bin/env python3
"""Explicit Sylow subgroups in S_n, only for 2 <= n <= 5."""
import itertools
import sys


def compose(a, b):
    """Execute a first, then b, as in the book."""
    return tuple(b[x] for x in a)


def model(n, p):
    if n not in range(2, 6) or p not in (2, 3, 5) or p > n:
        raise ValueError("2 <= n <= 5; p must be a prime <= n")
    perms = list(itertools.permutations(range(n)))
    index = {x: i for i, x in enumerate(perms)}
    table = [[index[compose(a, b)] for b in perms] for a in perms]
    inv = [row.index(0) for row in table]
    cycle = list(range(n))
    length = 4 if p == 2 and n >= 4 else p
    for i in range(length):
        cycle[i] = (i + 1) % length
    gens = [index[tuple(cycle)]]
    if length == 4:
        flip = list(range(n))
        flip[0], flip[2] = flip[2], flip[0]
        gens.append(index[tuple(flip)])
    seed = {0}
    queue = [0]
    for a in queue:
        for b in gens:
            x = table[a][b]
            if x not in seed:
                seed.add(x)
                queue.append(x)
    subgroups = sorted({tuple(sorted(table[table[g][h]][inv[g]] for h in seed))
                        for g in range(len(perms))})
    normalizers = []
    for h in subgroups:
        normalizers.append(sum(tuple(sorted(table[table[g][x]][inv[g]] for x in h)) == h
                               for g in range(len(perms))))
    return perms, subgroups, normalizers


def output(n, p):
    perms, groups, normalizers = model(n, p)
    lines = [f"S{n} order={len(perms)} p={p} sylow_order={len(groups[0])}"]
    for i, x in enumerate(perms):
        lines.append(f"perm {i}: " + ",".join(str(y + 1) for y in x))
    for h, norm in zip(groups, normalizers):
        lines.append("H={" + ",".join(map(str, h)) + f"}} normalizer={norm}")
    lines.append(f"sylow_count={len(groups)}")
    lines.append(f"point_orbit={n} point_stabilizer={sum(x[0] == 0 for x in perms)}")
    return "\n".join(lines) + "\n"


def main(args):
    try:
        if not args:
            n, p = 4, 2
        elif len(args) == 2 and all(len(x) == 1 and x in "2345" for x in args):
            n, p = map(int, args)
        else:
            raise ValueError("usage: sylow [n p]")
        result = output(n, p)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    print(result, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
