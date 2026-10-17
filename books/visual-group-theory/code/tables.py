"""Check all group axioms for a finite operation table (1..16 elements)."""
import re
import sys


def check(table):
    n = len(table)
    if not 1 <= n <= 16 or any(len(row) != n for row in table):
        raise ValueError("expected a square table of size 1..16")
    if any(type(x) is not int for row in table for x in row):
        raise ValueError("table entries must be integers")
    for i in range(n):
        for j in range(n):
            if not 0 <= table[i][j] < n:
                return [f"CLOSURE FAIL {i} {j} {table[i][j]}", "GROUP NO"], False
    lines = ["CLOSURE OK"]
    witness = next(((a, b, c, table[table[a][b]][c], table[a][table[b][c]])
                    for a in range(n) for b in range(n) for c in range(n)
                    if table[table[a][b]][c] != table[a][table[b][c]]), None)
    lines.append("ASSOCIATIVE OK" if witness is None else
                 "ASSOCIATIVE FAIL " + " ".join(map(str, witness)))
    identity = next((e for e in range(n)
                     if all(table[e][a] == a and table[a][e] == a for a in range(n))), None)
    lines.append("IDENTITY NONE" if identity is None else f"IDENTITY {identity}")
    missing = None
    if identity is None:
        lines.append("INVERSES UNDEFINED")
    else:
        missing = next((a for a in range(n)
                        if not any(table[a][b] == identity and table[b][a] == identity
                                   for b in range(n))), None)
        lines.append("INVERSES OK" if missing is None else f"INVERSES FAIL {missing}")
    group = witness is None and identity is not None and missing is None
    lines.append("GROUP YES" if group else "GROUP NO")
    return lines, group


def read_table(text):
    if not text.isascii():
        raise ValueError("input must be ASCII text")
    tokens = re.split(r"[ \t\n\r\v\f]+", text.strip(" \t\n\r\v\f"))
    if not tokens or any(re.fullmatch(r"-?[0-9]{1,4}", t) is None for t in tokens):
        raise ValueError("expected integer tokens with at most four digits")
    numbers = list(map(int, tokens))
    n = numbers[0]
    if not 1 <= n <= 16 or len(numbers) != 1 + n * n:
        raise ValueError("expected n in 1..16 followed by exactly n*n entries")
    return [numbers[1 + i*n:1 + (i+1)*n] for i in range(n)]


def main(args):
    if args not in ([], ["--stdin"]):
        raise ValueError("usage: tables.py [--stdin]")
    table = read_table(sys.stdin.read()) if args else [[i ^ j for j in range(4)] for i in range(4)]
    lines, group = check(table)
    print("\n".join(lines))
    return 0 if group else 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
