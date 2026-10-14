"""Independent arithmetic and live-interval references for CS:APP Part II."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import pty
import random
import re
import select
import signal
import subprocess
import sys
import time


def module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def check_part_two(base: Path, run: Path, compiler: str):
    run.mkdir(parents=True, exist_ok=True)
    commands = []

    def command(args, expected=0):
        proc = subprocess.run(list(map(str, args)), capture_output=True, text=True, timeout=90)
        commands.append({'command': [str(x).replace(str(base), 'BOOK').replace(str(run), 'RUN') for x in args],
                         'exit_code': proc.returncode, 'stdout': proc.stdout[:3000], 'stderr': proc.stderr[:2000]})
        if expected is not None and proc.returncode != expected:
            (run / 'failure.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
            raise ValueError('Part II regression failed: ' + repr(list(map(str, args))) + '\n' + proc.stderr[:1500])
        return proc

    flags = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic', '-O1',
             '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-DNDEBUG']

    def harness(name, source, body):
        path = run / (name + '.c')
        path.write_text('#define main original_example_main\n#include ' + json.dumps(str(source)) +
                        '\n#undef main\nint main(void) {\n' + body + '\nreturn 0;\n}\n')
        binary = run / name
        command([*flags, path, '-o', binary])
        return binary

    relocation = module(base / 'code/ch07_relocation.py')
    randoms = random.Random(20261014)
    cases = [(0, 0, 0, False), (0, -1, 0, False), (0xFFFFFFFF, 1, 0, False),
             (0x80000000, 0, 0, True), (0, 0, 0x80000000, True),
             (0x4004F8, -4, 0x4004EA, True)]
    cases += [(randoms.randrange(1 << 32), randoms.randrange(-(1 << 31), 1 << 31),
               randoms.randrange(1 << 32), bool(randoms.randrange(2))) for _ in range(256)]
    lines = []
    for i, (symbol, addend, place, relative) in enumerate(cases):
        number = symbol + addend - (place if relative else 0)
        low, high = (-(1 << 31), (1 << 31) - 1) if relative else (0, (1 << 32) - 1)
        good = low <= number <= high
        expected = (number % (1 << 32)).to_bytes(4, 'little') if good else None
        if relocation.relocate(symbol, addend, place, relative) != expected:
            raise ValueError('Python relocation differs from integer reference')
        octets = expected if good else bytes([165] * 4)
        lines.append('{ unsigned char out[4]={165,165,165,165}; '
                     f'bool ok=relocate(UINT32_C({symbol}), (int32_t)INT64_C({addend}), '
                     f'UINT32_C({place}), {str(relative).lower()}, out); '
                     f'if(ok!={str(good).lower()} || ' + ' || '.join(
                         f'out[{j}]!={b}' for j, b in enumerate(octets)) + f')return 1; }} /* {i} */')
    relbody = '\n'.join(lines)
    command([harness('relocation-reference', base / 'code/ch07_relocation.c', relbody)])
    mutated = (base / 'code/ch07_relocation.c').read_text().replace('value -= place;', 'value += place;', 1)
    mutant = run / 'relocation-wrong-place.c'; mutant.write_text(mutated)
    if command([harness('relocation-mutant', mutant, relbody)], expected=None).returncode == 0:
        raise ValueError('Wrong relocation place mutation escaped')

    # The oracle stores live intervals, not headers, footers, or the example's
    # block list. Holes are their complement; next-fit ranks hole starts by
    # cyclic distance from a separately maintained allocation cursor.
    allocator = module(base / 'code/ch09_allocator.py')
    allocator_trace, allocator_stats, operations = [], [], 0
    first, end, capacity, slots_count = 12, 65532, 65520, 64
    for mode in range(4):
        nf, elide = bool(mode & 1), bool(mode & 2)
        overhead = 4 if elide else 8
        stats = {'policy': 'next-fit' if nf else 'first-fit',
                 'footers': 'free-only' if elide else 'full', 'seed': 937713 + mode,
                 'random_operations': 6000, 'operations': 0, 'allocation_attempts': 0,
                 'successful_allocations': 0, 'frees': 0, 'null_frees': 0,
                 'failed_allocations': {'zero': 0, 'overlarge': 0, 'exhaustion': 0},
                 'next_fit_wraps': 0, 'different_from_first_fit': 0,
                 'cursor_repairs': 0, 'coalescing_cases': [0] * 4,
                 'directed_scenarios': []}
        rng = random.Random(stats['seed'])
        live, cursor, counters, pyheap, scenario = {}, first, [0] * 4, None, ''

        def holes():
            free, prior = [], first
            for start, length, _ in sorted(live.values()):
                if start > prior:
                    free.append((prior, start - prior))
                prior = start + length
            if prior < end:
                free.append((prior, end - prior))
            return free

        def snapshot():
            return (tuple(tuple(block) for block in pyheap.blocks), pyheap.rover,
                    tuple(pyheap.cases), pyheap.nf, pyheap.elide)

        def record(op, slot=0, requested=0, pointer=0):
            nonlocal operations
            # Exact geometry and cursor checks do not depend on Heap.check's
            # asserts; these remain active even under Python -O.
            expected = sorted([[h, n, True] for h, n, _ in live.values()] +
                              [[h, n, False] for h, n in holes()])
            if (pyheap.blocks != expected or pyheap.rover != cursor or
                    pyheap.cases != counters or pyheap.nf != nf or pyheap.elide != elide):
                raise ValueError(f'Python allocator reference mismatch: mode={mode} scenario={scenario} '
                                 f'op={op} cursor={pyheap.rover}/{cursor}')
            pyheap.check()
            allocator_trace.append({'op': op, 'mode': mode, 'scenario': scenario, 'slot': slot,
                                    'request': requested, 'pointer': pointer, 'cursor': cursor,
                                    'coalescing_cases': counters.copy()})
            if op not in ('I', 'E'):
                operations += 1
                stats['operations'] += 1

        def reset(label):
            nonlocal live, cursor, counters, pyheap, scenario
            if live:
                raise ValueError('Reference reset would discard live allocations')
            live, cursor, counters, scenario = {}, first, [0] * 4, label
            pyheap = allocator.Heap(nf, elide)
            record('I')

        def allocate(slot, requested):
            nonlocal cursor
            if slot in live:
                raise ValueError('Reference overwrote an outstanding allocation')
            before = snapshot()
            free = holes()
            needed = max(16, ((requested + overhead + 7) // 8) * 8)
            candidates = sorted(free, key=lambda hole: (hole[0] - cursor) % capacity) if nf else free
            eligible = [hole for hole in candidates if hole[1] >= needed]
            chosen = eligible[0] if 0 < requested <= capacity - overhead and eligible else None
            pointer = None
            stats['allocation_attempts'] += 1
            if chosen is not None:
                start, length = chosen
                if nf:
                    stats['next_fit_wraps'] += start < cursor
                    stats['different_from_first_fit'] += start != min(h for h, n in free if n >= needed)
                consumed = needed if length - needed >= 16 else length
                live[slot] = (start, consumed, requested)
                pointer, cursor = start + 4, first + ((start + consumed - first) % capacity)
                stats['successful_allocations'] += 1
            else:
                failure = 'zero' if requested == 0 else 'overlarge' if requested > capacity - overhead else 'exhaustion'
                stats['failed_allocations'][failure] += 1
            if pyheap.alloc(requested) != pointer:
                raise ValueError(f'Python allocation address differs: mode={mode} scenario={scenario}')
            if pointer is None and snapshot() != before:
                raise ValueError(f'Python failed allocation changed state: mode={mode} scenario={scenario}')
            record('A', slot, requested, pointer or 0)
            return pointer

        def release(slot):
            nonlocal cursor
            start, length, _ = live[slot]
            free = holes()
            # Adjacent complementary intervals identify coalescing cases without
            # inspecting the implementation's previous-allocation bit/footer.
            left = any(h + n == start for h, n in free)
            right = any(h == start + length for h, _ in free)
            case = 2 * left + right
            counters[case] += 1
            stats['coalescing_cases'][case] += 1
            del live[slot]
            containing = next((h for h, n in holes() if h <= cursor < h + n), cursor)
            stats['cursor_repairs'] += containing != cursor
            cursor = containing
            pyheap.free(start + 4)
            stats['frees'] += 1
            record('F', slot)

        def null_free():
            before = snapshot()
            pyheap.free(None)
            if snapshot() != before:
                raise ValueError('Python free(None) changed state')
            stats['null_frees'] += 1
            record('N')

        def finish():
            for slot in list(live):
                release(slot)
            if holes() != [(first, capacity)] or cursor != first:
                raise ValueError('Reference did not restore the complete arena')
            record('E')

        for case in range(4):
            label = f'coalescing-{case}'
            stats['directed_scenarios'].append(label)
            reset(label)
            for slot in range(5):
                allocate(slot, 16)
            if case & 2:
                release(1)
            if case & 1:
                release(3)
            release(2)
            finish()

        # A low-address hole and a later cursor distinguish the two policies.
        stats['directed_scenarios'].append('policy-selection')
        reset('policy-selection')
        for slot in range(3):
            allocate(slot, 16)
        release(0)
        if allocate(3, 16) != (88 if nf else 16):
            raise ValueError('Directed policy reference changed')
        finish()

        # The tail hole is 16 bytes, below a 24-byte request. A search starting
        # there must cross the arena end to select the 24-byte hole at FIRST.
        stats['directed_scenarios'].append('wrap-to-low-hole')
        reset('wrap-to-low-hole')
        allocate(0, 24 - overhead)
        allocate(1, 24 - overhead)
        allocate(2, capacity - 64 - overhead)
        release(0)
        if cursor != end - 16 or allocate(3, 24 - overhead) != first + 4:
            raise ValueError('Directed wrap reference changed')
        finish()

        # The cursor first lies inside a right-merged hole, then inside the
        # larger hole produced when the remaining middle allocation is freed.
        stats['directed_scenarios'].append('cursor-right-then-both-merge')
        reset('cursor-right-then-both-merge')
        for slot in range(3):
            allocate(slot, 16)
        release(0)
        release(2)
        if cursor != 60:
            raise ValueError('Directed right-merge cursor changed')
        release(1)
        if cursor != first:
            raise ValueError('Directed both-merge cursor changed')
        finish()

        stats['directed_scenarios'].append('failure-state-preservation')
        reset('failure-state-preservation')
        allocate(0, 16)
        for requested in (0, capacity - overhead + 1, (1 << 64) - 1):
            allocate(1, requested)
        null_free()
        release(0)
        allocate(0, capacity - overhead)
        allocate(1, 1)
        allocate(1, 0)
        allocate(1, capacity + 1)
        null_free()
        finish()

        reset('fixed-seed-mixed')
        for step in range(stats['random_operations']):
            vacant = [slot for slot in range(slots_count) if slot not in live]
            if live and (not vacant or rng.random() < .46):
                release(rng.choice(list(live)))
            else:
                allocate(rng.choice(vacant), rng.choice([0, 1, 7, 8, 9, 15, 16, 17,
                         65512, 65513, 65516, 65517, 65520, 65521, (1 << 64) - 1,
                         rng.randrange(1, 4000)]))
            if step % 127 == 0:
                null_free()
        finish()
        if (not all(stats['coalescing_cases']) or not all(stats['failed_allocations'].values()) or
                (nf and (not stats['next_fit_wraps'] or not stats['different_from_first_fit']))):
            raise ValueError('Allocator reference did not exercise its declared coverage')
        allocator_stats.append(stats)

    # Use one compact trace interpreter so all mutations receive exactly the
    # same operations and independent expected addresses/cursors/case counts.
    (run / 'allocator-trace.json').write_text(json.dumps(allocator_trace, indent=2) + '\n')
    rows = []
    for item in allocator_trace:
        rows.append("{'%s',%d,%d,UINT64_C(%d),%d,%d,{%s}}" %
                    (item['op'], item['mode'], item['slot'], item['request'], item['pointer'],
                     item['cursor'], ','.join(map(str, item['coalescing_cases']))))
    body = r'''
struct operation { char op; unsigned mode, slot; uint64_t request; size_t pointer, cursor; unsigned counts[4]; };
static const struct operation trace[] = {
''' + ',\n'.join(rows) + r'''
};
void *slots[64]={0}; size_t lengths[64]={0}; unsigned char saved[CAP];
#define FAIL(reason) do { fprintf(stderr,"step=%zu mode=%u op=%c %s\n",step,t->mode,t->op,reason); return 1; } while(0)
for(size_t step=0;step<sizeof trace/sizeof trace[0];step++) {
    const struct operation *t=&trace[step];
    bool nf=(t->mode&1u)!=0, nofooter=(t->mode&2u)!=0;
    if(t->op=='I') {init(nf,nofooter);memset(slots,0,sizeof slots);memset(lengths,0,sizeof lengths);}
    else if(t->op=='A'||t->op=='N') {
        if(t->op=='A'&&slots[t->slot])FAIL("test reused a live slot");
        memcpy(saved,heap.b,CAP);size_t old_rover=rover;unsigned old_cases[4];
        memcpy(old_cases,cases,sizeof cases);bool old_nf=next_fit,old_elide=elide;
        void *p=NULL;
        if(t->op=='N')toy_free(NULL);else p=toy_malloc((size_t)t->request);
        if(p!=(t->pointer?heap.b+t->pointer:NULL))FAIL("address differs from live-interval reference");
        if(!p&&(memcmp(saved,heap.b,CAP)||old_rover!=rover||memcmp(old_cases,cases,sizeof cases)||
                old_nf!=next_fit||old_elide!=elide))FAIL("failure or NULL free changed arena/control state");
        if(p) {if((uintptr_t)p%8)FAIL("payload alignment");slots[t->slot]=p;
            lengths[t->slot]=(size_t)t->request;memset(p,(int)t->slot+1,lengths[t->slot]);}
    } else if(t->op=='F') {
        if(!slots[t->slot])FAIL("test freed an empty slot");
        toy_free(slots[t->slot]);slots[t->slot]=NULL;lengths[t->slot]=0;
    } else if(t->op=='E') {
        if(size(FIRST)!=END-FIRST||allocated(FIRST))FAIL("arena not fully restored");
    } else FAIL("unknown test operation");
    if(rover!=t->cursor)FAIL("cursor differs from independent reference");
    if(memcmp(cases,t->counts,sizeof cases)||next_fit!=nf||elide!=nofooter)FAIL("control state differs");
    if(!check())FAIL("allocator invariant");
    for(unsigned k=0;k<64;k++)if(slots[k])for(size_t j=0;j<lengths[k];j++)
        if(((unsigned char *)slots[k])[j]!=k+1)FAIL("live payload changed");
}
printf("allocator trace steps=%zu addresses/cursors/control/payloads/failure snapshots=PASS\n",sizeof trace/sizeof trace[0]);
#undef FAIL
'''
    source = (base / 'code/ch09_allocator.c').read_text()
    mutations = [
        ('missing backward coalescing', 'allocator-no-left-merge', 'if(!pa){', 'if(false){'),
        ('next-fit replaced by first-fit', 'allocator-next-as-first',
         'size_t start=next_fit?rover:FIRST,h=start;', 'size_t start=FIRST,h=start;'),
        ('next-fit cursor not repaired after free', 'allocator-stale-cursor',
         'if(rover>=h&&rover<h+n)rover=h;', 'if(!next_fit&&rover>=h&&rover<h+n)rover=h;'),
    ]
    mutation_results = []
    # Run deliberately wrong implementations before accepting the real C source.
    for description, name, old, new in mutations:
        if source.count(old) != 1:
            raise ValueError('Allocator mutation site changed; review the test: ' + description)
        mutant = run / (name + '.c')
        mutant.write_text(source.replace(old, new, 1))
        observed = command([harness(name + '-test', mutant, body)], expected=None)
        if observed.returncode == 0 or 'step=' not in observed.stderr:
            raise ValueError('Allocator mutation was not rejected by an explicit regression: ' + description)
        mutation_results.append({'mutation': description, 'exit_code': observed.returncode,
                                 'stderr': observed.stderr.strip()})
        (run / 'allocator-mutation-results.json').write_text(json.dumps(mutation_results, indent=2) + '\n')
    command([harness('allocator-reference', base / 'code/ch09_allocator.c', body)])
    (run / 'allocator-reference-summary.json').write_text(json.dumps(
        {'operations': operations, 'trace_steps': len(allocator_trace), 'modes': allocator_stats,
         'mutations': mutation_results}, indent=2) + '\n')

    # Figure 9.20: hand-derived field results, including TLB hit beyond printed PTEs.
    vm = module(base / 'code/ch09_vm.py')
    reference = {
        0x3D7: 'va=03d7 vpn=0f vpo=17 tlbi=3 tlbt=03 tlb=Y fault=N pa=357 co=3 ci=5 ct=0d cache=Y byte=1d',
        0x27C: 'va=027c vpn=09 vpo=3c tlbi=1 tlbt=02 tlb=N fault=N pa=5fc co=0 ci=f ct=17 cache=N',
        0x3A9: 'va=03a9 vpn=0e vpo=29 tlbi=2 tlbt=03 tlb=N fault=N pa=469 co=1 ci=a ct=11 cache=N',
        0x40: 'va=0040 vpn=01 vpo=00 tlbi=1 tlbt=00 tlb=N fault=Y',
        0x900: 'va=0900 vpn=24 vpo=00 tlbi=0 tlbt=09 tlb=Y fault=N pa=340 co=0 ci=0 ct=0d cache=N',
    }
    binary = run / 'vm'; command([*flags, base / 'code/ch09_vm.c', '-o', binary])
    for address, expected in reference.items():
        if vm.translate(address) != expected or command([binary, f'{address:x}']).stdout != expected + '\n':
            raise ValueError('Address translation differs from hand-derived values')
    invalid = ['', ' 1', '\t1', '-1', '+1', '0x', 'g', '4000', '10000000000000000', '400']
    for value in invalid:
        command([binary, value], expected=2)
        command([sys.executable, base / 'code/ch09_vm.py', value], expected=2)

    command([sys.executable, base / 'code/ch07_probe.py', run / 'linker-probe'])
    mapped = run / 'mmap-example'
    command([*flags, base / 'code/ch09_mmap.c', '-o', mapped])
    empty = run / 'empty.txt'; empty.write_bytes(b'')
    sample = run / 'hello.txt'; sample.write_bytes(b'Hello, world!\n')
    if command([mapped, 'copy', empty]).stdout != '':
        raise ValueError('Empty file copy produced bytes')
    if command([mapped, 'copy', sample]).stdout != 'Hello, world!\n':
        raise ValueError('Mapped copy differs')
    command([mapped, 'change', sample])
    if sample.read_bytes() != b'Jello, world!\n':
        raise ValueError('Shared mapped update did not persist')
    command([mapped, 'change', empty], expected=1)
    command([mapped, 'change', sample], expected=1)
    command([mapped, 'copy', run / 'missing-file'], expected=1)

    # Exercise actual job-control paths with only a task-owned sleep child.
    shell = run / 'shell-example'
    command([*flags, base / 'code/ch08_shell.c', '-o', shell])
    helper_source = run / 'shell-job.c'
    helper_source.write_text('''#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <unistd.h>
static void continued(int sig){(void)sig; const char s[]="CHILD_RESUMED\\n";
ssize_t n=write(STDOUT_FILENO,s,sizeof s-1);(void)n;}
int main(void){struct sigaction sa={0};sa.sa_handler=continued;
if(sigemptyset(&sa.sa_mask)||sigaction(SIGCONT,&sa,0))return 1;
alarm(30);const char s[]="CHILD_READY\\n";
if(write(STDOUT_FILENO,s,sizeof s-1)<0)return 1;
for(;;)pause();}
''')
    helper = run / 'shell-job'; command([*flags, helper_source, '-o', helper])
    master, slave = pty.openpty()
    proc = subprocess.Popen([str(shell), '--interactive'], stdin=slave, stdout=slave, stderr=slave,
                            start_new_session=True)
    os.close(slave)
    transcript, child, cursor = '', None, 0

    def receive(pattern, timeout=7):
        nonlocal transcript, cursor
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            matched = re.search(pattern, transcript[cursor:])
            if matched:
                cursor += matched.end()
                return matched
            ready, _, _ = select.select([master], [], [], max(0, until - time.monotonic()))
            if ready:
                transcript += os.read(master, 65536).decode(errors='replace')
        raise ValueError('Shell observation timed out: ' + pattern + '\n' + transcript[-1500:])

    def send(line):
        os.write(master, (line + '\n').encode())

    try:
        receive(r'> ')
        send(str(helper) + ' &')
        job = receive(r'\[(\d+)\] (\d+) ' + re.escape(str(helper)))
        jid, child = int(job[1]), int(job[2])
        if 'CHILD_READY' not in transcript:
            receive('CHILD_READY')
        os.kill(child, signal.SIGSTOP)
        receive(r'stopped by signal')
        send('jobs'); receive(r'Stopped')
        resumed_from = len(transcript)
        send(f'bg %{jid}'); receive(r'\[' + str(jid) + r'\] ' + str(child))
        if 'CHILD_RESUMED' not in transcript[resumed_from:]:
            receive('CHILD_RESUMED')
        send('jobs'); receive(r'Running')
        send(f'fg %{jid}')
        # The child confirms SIGCONT was sent by fg; the parent blocks SIGINT
        # throughout this state transition, then unmasks it in sigsuspend.
        receive('CHILD_RESUMED')
        os.kill(proc.pid, signal.SIGINT)
        receive(r'Job ' + str(child) + r' terminated by signal 2')
        send(f'fg %{jid}'); receive(r'No such process')
        send('quit'); proc.wait(timeout=7)
        if proc.returncode:
            raise ValueError('Shell exited with failure')
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            child = None
        else:
            raise ValueError('Shell failed to reap owned sleep child')
    finally:
        if proc.poll() is None:
            proc.kill(); proc.wait(timeout=7)
        if child is not None:
            try:
                os.kill(child, signal.SIGKILL)
            except ProcessLookupError:
                pass
        os.close(master)
        (run / 'shell-pty.txt').write_text(transcript)
    result = {'relocation_integer_reference_cases': len(cases),
              'allocator_live_interval_operations': operations,
              'allocator_conditions': 'first/next fit x full/free-only footers; live-interval complement and cursor reference; C payload and failure arena/control preservation; -DNDEBUG ASan/UBSan',
              'allocator_modes': allocator_stats, 'allocator_trace_steps': len(allocator_trace),
              'allocator_mutation_results': mutation_results,
              'vm_hand_derived_cases': len(reference), 'vm_invalid_inputs_per_language': len(invalid),
              'detected_mutations': ['wrong PC-relative place sign', *[entry['mutation'] for entry in mutation_results]],
              'native_linker_probe': 'separate compile, archive, rejected unresolved symbol, dynamic loading and failures',
              'native_mmap_cases': 6,
              'native_shell_pty': 'background, stop, jobs, bg, fg, SIGINT forwarding, reap, invalid job, quit'}
    (run / 'report.json').write_text(json.dumps({'summary': result, 'commands': commands}, ensure_ascii=False, indent=2) + '\n')
    return result
