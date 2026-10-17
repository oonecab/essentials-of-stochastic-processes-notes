#!/usr/bin/env python3
"""Exact arithmetic in Q(t,s), t^3=2 and s^2=-3; basis 1,t,t^2,s,ts,t^2s."""
from fractions import Fraction
import re
import sys


def basis(i):
    return tuple(Fraction(int(j == i)) for j in range(6))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, c):
    return tuple(x * c for x in a)


def mul(a, b):
    out = [Fraction(0) for _ in range(6)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            tpower = i % 3 + j % 3
            spower = i // 3 + j // 3
            factor = 1
            if tpower >= 3:
                tpower -= 3
                factor *= 2
            if spower >= 2:
                spower -= 2
                factor *= -3
            out[tpower + 3 * spower] += x * y * factor
    return tuple(out)


def automorphism(a, k, sign):
    if len(a) != 6 or k not in (0, 1, 2) or sign not in (-1, 1):
        raise ValueError("invalid field vector or automorphism")
    one, t, s = basis(0), basis(1), basis(3)
    zeta = scale(add(scale(one, -1), s), Fraction(1, 2))
    zpower = one
    for _ in range(k):
        zpower = mul(zpower, zeta)
    timage = mul(t, zpower)
    simage = scale(s, sign)
    powers = [one, timage, mul(timage, timage)]
    images = powers + [mul(x, simage) for x in powers]
    out = (Fraction(0),) * 6
    for coefficient, image in zip(a, images):
        out = add(out, scale(image, coefficient))
    return out


def format_vector(a):
    return "[" + ",".join(map(str, a)) + "]"


def output(a):
    lines = ["basis=1,t,t^2,s,ts,t^2s; t^3=2; s^2=-3", "input=" + format_vector(a)]
    trace = (Fraction(0),) * 6
    for k in range(3):
        for sign in (1, -1):
            value = automorphism(a, k, sign)
            trace = add(trace, value)
            perm = ",".join(str((k + sign * j) % 3 + 1) for j in range(3))
            lines.append(f"sigma({k},{sign}) roots={perm} value=" + format_vector(value))
    lines.append("trace=" + format_vector(trace))
    lines.append("z*conjugate(z)=" + format_vector(mul(a, automorphism(a, 0, -1))))
    return "\n".join(lines) + "\n"


def main(args):
    if not args:
        a = (Fraction(1),) * 6
    elif len(args) == 6 and all(re.fullmatch(r"-?[0-9]{1,3}", s) for s in args):
        a = tuple(Fraction(int(s)) for s in args)
    else:
        print("usage: galois [a b c d e f], six integers -100..100", file=sys.stderr)
        return 2
    if any(abs(x) > 100 for x in a):
        print("coefficients must be in -100..100", file=sys.stderr)
        return 2
    print(output(a), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
