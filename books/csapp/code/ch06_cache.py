"""Configurable LRU cache trace model; counts transfers, not processor cycles."""
import sys

MASK = (1 << 64) - 1


class Cache:
    def __init__(self, sets, ways, block, write_back=True, allocate=True):
        if (sets < 1 or sets & (sets - 1) or block < 1 or block & (block - 1)
                or ways < 1 or sets * ways > 1048576 or block > 1048576):
            raise ValueError('invalid geometry')
        self.s, self.e, self.b = sets, ways, block
        self.wb, self.wa = bool(write_back), bool(allocate)
        self.rows = [[] for _ in range(sets)]  # LRU first: [tag, dirty]
        self.operations = self.hits = self.misses = self.evictions = 0
        self.writebacks = self.read_bytes = self.write_bytes = 0

    def access(self, op, address, size=1):
        if op not in ('R', 'W') or not 1 <= size <= 4096 or not 0 <= address <= MASK - size + 1:
            raise ValueError('invalid reference')
        self.operations += 1
        result = ''
        while size:
            count = min(size, self.b - address % self.b)
            number = address // self.b
            row, tag = self.rows[number % self.s], number // self.s
            match = next((i for i, item in enumerate(row) if item[0] == tag), None)
            if match is not None:
                self.hits += 1
                result += 'h'
                item = row.pop(match)
                row.append(item)
            else:
                self.misses += 1
                result += 'm'
                if op == 'W' and not self.wa:
                    self.write_bytes += count
                    address += count
                    size -= count
                    continue
                if len(row) == self.e:
                    old = row.pop(0)
                    self.evictions += 1
                    if old[1]:
                        self.writebacks += 1
                        self.write_bytes += self.b
                self.read_bytes += self.b
                item = [tag, False]
                row.append(item)
            if op == 'W':
                if self.wb:
                    item[1] = True
                else:
                    self.write_bytes += count
            address += count
            size -= count
        return result

    def report(self):
        dirty = sum(item[1] for row in self.rows for item in row)
        return (f'operations={self.operations} hits={self.hits} misses={self.misses} '
                f'evictions={self.evictions} writebacks={self.writebacks}\n'
                f'read_bytes={self.read_bytes} write_bytes={self.write_bytes} dirty_lines={dirty}\n')


def main():
    if len(sys.argv) == 1:
        c = Cache(4, 1, 2)
        for address in (0, 1, 13, 8, 0):
            c.access('R', address)
    else:
        if len(sys.argv) != 7:
            raise ValueError('usage: S E B write_back write_allocate trace_file')
        values = [int(x) for x in sys.argv[1:6]]
        if values[3] not in (0, 1) or values[4] not in (0, 1):
            raise ValueError('policy must be 0 or 1')
        c = Cache(*values)
        with open(sys.argv[6], encoding='ascii') as f:
            for line in f:
                fields = line.split()
                if len(fields) != 3 or not fields[1].startswith('0x'):
                    raise ValueError('trace syntax: R|W 0xADDRESS SIZE')
                c.access(fields[0], int(fields[1], 16), int(fields[2]))
    print(c.report(), end='')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, OverflowError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
