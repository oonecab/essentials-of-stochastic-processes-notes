import re
import sys
class Cache:
    def __init__(self, ways=1, block=2):
        self.ways, self.block = ways, block
        self.sets = [[] for _ in range(4)]  # Oldest tag first.
        self.hits = self.misses = 0
    def access(self, address):
        number = address // self.block
        rows, tag = self.sets[number % 4], number // 4
        hit = tag in rows
        if hit:
            self.hits += 1
            rows.remove(tag)
        else:
            self.misses += 1
            if len(rows) == self.ways:
                rows.pop(0)
        rows.append(tag)
        return hit

def parse(s):
    if not re.fullmatch(r"[+]?[0-9]+", s):
        raise ValueError("decimal nonnegative integer required")
    value = int(s)
    if value > (1 << 64) - 1:
        raise ValueError("uint64 range exceeded")
    return value

def main():
    if len(sys.argv) > 1:
        if len(sys.argv) < 3:
            raise ValueError("ways and addresses required")
        ways = parse(sys.argv[1])
        if ways not in (1, 2, 4):
            raise ValueError("ways must be 1, 2 or 4")
        trace = [parse(s) for s in sys.argv[2:]]
    else:
        ways, trace = 1, [0, 1, 13, 8, 0]
    c = Cache(ways)
    for a in trace:
        hit = c.access(a)
        print(f"addr={a} set={(a // 2) % 4} tag={(a // 2) // 4} hit={int(hit)}")
    print(f"hits={c.hits} misses={c.misses}")
    if len(sys.argv) == 1:
        for column in (False, True):
            c = Cache(block=16)
            for i in range(8):
                for j in range(8):
                    c.access((j * 8 + i if column else i * 8 + j) * 4)
            print(f"matrix-{'column' if column else 'row'} hits={c.hits} misses={c.misses}")
if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2)
