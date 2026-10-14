"""Bounded, little-endian Y86-64 ISA model; not a PIPE circuit simulator."""
import sys

MASK = (1 << 64) - 1
SIZE, NONE, RSP = 4096, 15, 4
NAMES = ('rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi',
         'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14')
DEMO = bytes.fromhex(
    '30f2090000000000000030f315000000000000006123'
    '30f4800000000000000040436400000000000000a02fb00f'
    '7340000000000000008041000000000000000090')


def cond(fn, z, s, o):
    return (True, (s != o) or z, s != o, z, not z,
            s == o, (s == o) and not z)[fn]


def alu(fn, a, b):
    r = ((b + a) if fn == 0 else (b - a) if fn == 1 else
         (b & a) if fn == 2 else (b ^ a)) & MASK
    sa, sb, sr = a >> 63, b >> 63, r >> 63
    overflow = (sa == sb and sr != sb) if fn == 0 else (
        (sa != sb and sr != sb) if fn == 1 else False)
    return r, (r == 0, bool(sr), overflow)


def control(load_use, mispredict, returning, memory_bad, writeback_bad):
    return (load_use or returning, load_use,
            mispredict or (returning and not load_use),
            load_use or mispredict, memory_bad or writeback_bad, writeback_bad)


def forward(src, raw, sources):
    # sources are ordered: e_valE, m_valM, M_valE, W_valM, W_valE.
    for dst, value in sources:
        if src != NONE and src == dst:
            return value
    return raw


def check_logic():
    checks = 0
    for l in (False, True):
        for b in (False, True):
            if l and b:  # E cannot be both a load and a branch.
                continue
            for r in (False, True):
                for m in (False, True):
                    for w in (False, True):
                        f, ds, db, eb, mb, ws = control(l, b, r, m, w)
                        if ds and db or (l and not (f and ds and eb)):
                            raise RuntimeError('pipeline control conflict')
                        if mb != (m or w) or ws != w:
                            raise RuntimeError('exception ordering')
                        checks += 1
    if forward(4, 0, [(15, 0), (4, 5), (4, 264), (15, 0), (15, 0)]) != 5:
        raise RuntimeError('pop forwarding priority')
    if forward(2, 0, [(2, 3), (15, 0), (2, 10), (15, 0), (15, 0)]) != 3:
        raise RuntimeError('latest producer priority')
    return checks


class Machine:
    def __init__(self, image):
        if len(image) > SIZE:
            raise ValueError('image exceeds 4096 bytes')
        self.mem = bytearray(SIZE)
        self.mem[:len(image)] = image
        self.reg = [0] * 15
        self.pc, self.cc, self.stat = 0, (True, False, False), 'AOK'
        self.steps = self.loads = self.misses = self.rets = 0
        self.previous_load = NONE
        self.trace = []

    def word(self, addr):
        if addr > SIZE - 8:
            raise IndexError('word address')
        return int.from_bytes(self.mem[addr:addr + 8], 'little')

    def step(self):
        p = self.pc
        if p >= SIZE:
            self.stat = 'ADR'
            return
        op, fn = self.mem[p] >> 4, self.mem[p] & 15
        if op > 12 or fn > (6 if op in (2, 7) else 3 if op == 6 else 0):
            self.stat = 'INS'
            return
        nr, nc = op in (2, 3, 4, 5, 6, 10, 11, 12), op in (3, 4, 5, 7, 8, 12)
        length = 1 + nr + 8 * nc
        if p > SIZE - length:
            self.stat = 'ADR'
            return
        a, b = (self.mem[p + 1] >> 4, self.mem[p + 1] & 15) if nr else (NONE, NONE)
        good = (a < NONE and b < NONE) if op in (2, 4, 5, 6) else (
            a == NONE and b < NONE) if op in (3, 12) else (
            a < NONE and b == NONE) if op in (10, 11) else True
        if not good:
            self.stat = 'INS'
            return
        c = self.word(p + 1 + nr) if nc else 0
        sa = a if op in (2, 4, 6, 10) else RSP if op in (9, 11) else NONE
        sb = b if op in (4, 5, 6, 12) else RSP if op in (8, 9, 10, 11) else NONE
        va, vb = (self.reg[sa] if sa != NONE else 0), (self.reg[sb] if sb != NONE else 0)
        de = b if op in (2, 3, 6, 12) else RSP if op in (8, 9, 10, 11) else NONE
        dm = a if op in (5, 11) else NONE
        aa = va if op in (2, 6) else c if op in (3, 4, 5, 12) else (
            MASK - 7 if op in (8, 10) else 8 if op in (9, 11) else 0)
        ve, cc = alu(fn if op == 6 else 0, aa, vb)
        taken = cond(fn, *self.cc) if op in (2, 7) else True
        if op == 2 and not taken:
            de = NONE
        read, write = op in (5, 9, 11), op in (4, 8, 10)
        addr = va if op in (9, 11) else ve
        if (read or write) and addr > SIZE - 8:
            self.stat = 'ADR'
            return  # Failed memory operation has no architectural writes.
        vm = self.word(addr) if read else 0
        nextpc = c if op == 8 or op == 7 and taken else vm if op == 9 else p + length
        if self.previous_load != NONE and self.previous_load in (sa, sb):
            self.loads += 1
        self.previous_load = dm
        self.steps += 1
        self.misses += op == 7 and not taken
        self.rets += op == 9
        self.trace.append((p, op, fn, taken, sa, sb, dm))
        if op == 0:
            self.stat = 'HLT'
            return
        if write:
            data = p + length if op == 8 else va
            self.mem[addr:addr + 8] = data.to_bytes(8, 'little')
        if de != NONE:
            self.reg[de] = ve
        if dm != NONE:
            self.reg[dm] = vm  # M write wins for popq %rsp.
        if op in (6, 12):
            self.cc = cc
        self.pc = nextpc

    def run(self):
        while self.stat == 'AOK' and self.steps < 1000000:
            self.step()
        if self.stat == 'AOK':
            raise RuntimeError('instruction limit exceeded')

    def report(self):
        print(f'steps={self.steps} status={self.stat} pc=0x{self.pc:03x} cc=' +
              ''.join(str(int(x)) for x in self.cc))
        print(f'load-use={self.loads} mispredict={self.misses} ret={self.rets}')
        for i, name in enumerate(NAMES):
            print(f'{name}=0x{self.reg[i]:016x}')
        digest = 14695981039346656037
        for value in self.mem:
            digest = ((digest ^ value) * 1099511628211) & MASK
        print(f'memory-fnv64={digest:016x}')


def main():
    try:
        if len(sys.argv) > 2:
            raise ValueError('usage: ch04_machine.py [image.bin]')
        image = open(sys.argv[1], 'rb').read(SIZE + 1) if len(sys.argv) == 2 else DEMO
        print(f'control-cases={check_logic()} forwarding-cases=2')
        machine = Machine(image)
        machine.run()
        machine.report()
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
