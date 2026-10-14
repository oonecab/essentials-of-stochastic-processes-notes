"""Finite interleaving model; no Python threading/GIL conclusions are inferred."""
from functools import lru_cache


def count_updates():
    outcomes = [0, 0, 0]
    def step(pc, registers, value):
        if pc == (3, 3):
            outcomes[value] += 1
            return
        for t in range(2):
            if pc[t] == 3:
                continue
            p, r = list(pc), list(registers)
            new = value
            if p[t] == 0:
                r[t] = value
            elif p[t] == 1:
                r[t] += 1
            else:
                new = r[t]
            p[t] += 1
            step(tuple(p), tuple(r), new)
    step((0, 0), (0, 0), 0)
    return outcomes


def lock_states(programs, tokens):
    """lowercase acquires, uppercase releases; return distinct terminal states."""
    dead, done = set(), set()
    @lru_cache(None)
    def visit(pc, free):
        enabled = False
        if all(i == len(p) for i, p in zip(pc, programs)):
            done.add((pc, free))
            return
        for t, p in enumerate(programs):
            if pc[t] == len(p):
                continue
            op = p[pc[t]]
            bit = 1 << (ord(op.lower()) - ord('a'))
            if op.islower() and not free & bit:
                continue
            if op.isupper() and free & bit:
                raise ValueError('release without ownership')
            nxt = list(pc)
            nxt[t] += 1
            enabled = True
            visit(tuple(nxt), free ^ bit)
        if not enabled:
            dead.add((pc, free))
    visit((0,) * len(programs), tokens)
    return dead, done


def main():
    outcomes = count_updates()
    if outcomes != [0, 18, 2]:
        raise RuntimeError(f'counter outcome mismatch: {outcomes}')
    print(f'counter schedules={sum(outcomes)} final1={outcomes[1]} final2={outcomes[2]}')
    cases = [
        ('12.15-original', ('aAbB', 'aAbB'), 1, True),
        ('12.15-fixed', ('aAbB', 'aAbB'), 3, False),
        ('12.28-case1', ('abAB', 'abAB'), 3, False),
        ('12.28-case2', ('abAB', 'abBA'), 3, False),
        ('12.28-case3', ('abBA', 'abAB'), 3, False),
        ('12.28-case4', ('abBA', 'abBA'), 3, False),
        ('12.29', ('abBcCA', 'cbBC'), 7, False),
        ('12.30', ('abBcCA', 'cbBCaA', 'cCbaAB'), 7, True),
    ]
    for name, programs, initial, expected in cases:
        dead, done = lock_states(programs, initial)
        if bool(dead) != expected:
            raise RuntimeError(f'lock outcome mismatch: {name}')
        print(f'{name} deadlocks={len(dead)} completed={len(done)}')


if __name__ == '__main__':
    main()
