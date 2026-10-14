"""Independent allocation, cache-policy and fill regressions for the reading examples."""
from __future__ import annotations

import ctypes
import importlib.util
from pathlib import Path
import random
import subprocess
import sys
from unittest.mock import patch


def execute(args):
    return subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=90)


def output(args):
    result = execute(args)
    if result.returncode:
        raise ValueError(f'Command failed: {args[0]}\n{result.stderr[:1200]}')
    return result.stdout


def compile_c(source, binary, compiler='clang', extra=()):
    output([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic', '-O2',
            '-fsanitize=address,undefined', '-fno-omit-frame-pointer', *extra,
            source, '-o', binary])


def check_allocations(base):
    spec = importlib.util.spec_from_file_location('csapp_integer_regression', base / 'code/ch02_integer.py')
    integer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(integer)
    size_max = (1 << (8 * ctypes.sizeof(ctypes.c_size_t))) - 1
    cases = 0

    if integer.checked_calloc(17, 3) != bytes(51):
        raise ValueError('checked_calloc must return zeroed bytes')
    if integer.copy_elements([b'abcd', b'efgh'], 2, 4) != b'abcdefgh':
        raise ValueError('copy_elements must preserve each complete source element')
    cases += 2

    # The replacement allocator records calls and never reserves a large buffer.
    refused = [(0, 4), (3, 0), (-1, 4), (3, -1), (size_max, 2),
               (sys.maxsize + 1, 1), (1, sys.maxsize + 1),
               (sys.maxsize // 2 + 1, 2)]
    for function in (integer.checked_calloc, lambda n, size: integer.copy_elements([], n, size)):
        with patch.object(integer, 'bytearray', side_effect=RuntimeError('allocator reached'), create=True) as allocation:
            for count, size in refused:
                if function(count, size) is not None:
                    raise ValueError(f'Allocation boundary accepted: {count}, {size}')
                cases += 1
            if allocation.called:
                raise ValueError('Invalid allocation length reached the allocator')

        for error in (MemoryError, OverflowError):
            with patch.object(integer, 'bytearray', side_effect=error, create=True) as allocation:
                if function(1, 8) is not None or allocation.call_args.args != (8,):
                    raise ValueError(f'Allocation failure contract differs: {error.__name__}')
                cases += 1

        # The largest representable length is permitted to reach an allocator;
        # actual allocation failure still returns None.
        limit = min(size_max, sys.maxsize)
        with patch.object(integer, 'bytearray', side_effect=MemoryError, create=True) as allocation:
            if function(1, limit) is not None or allocation.call_args.args != (limit,):
                raise ValueError('Representable allocation boundary was rejected before allocation')
            cases += 1
    return {'cases': cases, 'size_t_max': size_max, 'python_length_max': sys.maxsize,
            'large_allocations': 0, 'injected_failures': ['MemoryError', 'OverflowError']}


def cache_oracle(config, trace):
    """Use block-ID maps, interval intersections and last-reference positions."""
    sets, ways, width, write_back, allocate = config
    residents = [{} for _ in range(sets)]
    counters = dict(operations=len(trace), hits=0, misses=0, evictions=0,
                    writebacks=0, read_bytes=0, write_bytes=0, dirty_lines=0)
    for operation_index, (operation, start, length) in enumerate(trace):
        end = start + length
        for block in range(start // width, (end - 1) // width + 1):
            transferred = min(end, (block + 1) * width) - max(start, block * width)
            row = residents[block % sets]
            if block in row:
                counters['hits'] += 1
            else:
                counters['misses'] += 1
                if operation == 'W' and not allocate:
                    counters['write_bytes'] += transferred
                    continue
                if len(row) == ways:
                    victim = min(row, key=lambda resident: row[resident][0])
                    _, dirty = row.pop(victim)
                    counters['evictions'] += 1
                    if dirty:
                        counters['writebacks'] += 1
                        counters['write_bytes'] += width
                row[block] = [(operation_index, block), False]
                counters['read_bytes'] += width
            row[block][0] = (operation_index, block)
            if operation == 'W':
                if write_back:
                    row[block][1] = True
                else:
                    counters['write_bytes'] += transferred
    counters['dirty_lines'] = sum(dirty for row in residents for _, dirty in row.values())
    return counters


def cache_report(counters):
    first = ('operations', 'hits', 'misses', 'evictions', 'writebacks')
    second = ('read_bytes', 'write_bytes', 'dirty_lines')
    return ''.join(' '.join(f'{key}={counters[key]}' for key in keys) + '\n'
                   for keys in (first, second))


def cache_cases():
    # These totals are derived by hand. They also validate the independent oracle.
    keys = ('operations', 'hits', 'misses', 'evictions', 'writebacks',
            'read_bytes', 'write_bytes', 'dirty_lines')
    cases = [
        ('write-back-allocate', (1, 1, 2, 1, 1), [('W', 0, 1), ('R', 2, 1)],
         (2, 0, 2, 1, 1, 4, 2, 0)),
        ('write-through-allocate', (1, 1, 2, 0, 1), [('W', 0, 1), ('R', 2, 1)],
         (2, 0, 2, 1, 0, 4, 1, 0)),
        ('write-back-no-allocate', (1, 1, 2, 1, 0),
         [('W', 0, 1), ('R', 0, 1), ('W', 0, 1), ('R', 2, 1)],
         (4, 1, 3, 1, 1, 4, 3, 0)),
        ('write-through-no-allocate', (1, 1, 2, 0, 0),
         [('W', 0, 1), ('R', 0, 1), ('W', 0, 1), ('R', 2, 1)],
         (4, 1, 3, 1, 0, 4, 2, 0)),
        ('per-set-lru-writeback', (2, 2, 4, 1, 1),
         [('W', 0, 1), ('R', 4, 1), ('W', 8, 1), ('R', 12, 1),
          ('R', 0, 1), ('W', 16, 1), ('R', 4, 1), ('R', 8, 1)],
         (8, 2, 6, 2, 2, 24, 8, 1)),
    ]
    for write_back, allocate, totals in (
            (1, 1, (2, 1, 5, 3, 2, 20, 8, 1)),
            (0, 1, (2, 1, 5, 3, 0, 20, 6, 0)),
            (1, 0, (2, 0, 6, 1, 0, 12, 6, 0)),
            (0, 0, (2, 0, 6, 1, 0, 12, 6, 0))):
        cases.append((f'cross-block-wb{write_back}-wa{allocate}', (2, 1, 4, write_back, allocate),
                      [('W', 3, 6), ('R', 0, 9)], totals))
    result = []
    for name, config, trace, values in cases:
        expected = dict(zip(keys, values))
        if cache_oracle(config, trace) != expected:
            raise ValueError('Cache oracle differs from hand calculation: ' + name)
        result.append((name, config, trace, cache_report(expected)))
    generator = random.Random(20261014)
    for sets in (1, 2, 8):
        for ways in (1, 3):
            for width in (1, 16):
                for write_back in (0, 1):
                    for allocate in (0, 1):
                        config = (sets, ways, width, write_back, allocate)
                        trace = [(generator.choice(('R', 'W')), generator.randrange(1024),
                                  generator.randrange(1, 81)) for _ in range(80)]
                        trace += [('W', (1 << 64) - 16, 16), ('R', (1 << 64) - 1, 1)]
                        name = 'sample-' + '-'.join(map(str, config))
                        result.append((name, config, trace, cache_report(cache_oracle(config, trace))))
    return result


def check_cache(base, run, binary, compiler):
    cases = cache_cases()
    for name, config, trace, expected in cases:
        path = run / (name + '.trace')
        path.write_text(''.join(f'{op} 0x{address:x} {length}\n' for op, address, length in trace))
        for implementation in ([binary], [sys.executable, base / 'code/ch06_cache.py']):
            actual = output([*implementation, *config, path])
            if actual != expected:
                raise ValueError(f'Cache independent reference differs: {name}, {implementation[0]}\n{actual}')

    source = (base / 'code/ch06_cache.c').read_text()
    target = 'item->dirty=true'
    if source.count(target) != 1:
        raise ValueError('Cache mutation anchor differs')
    mutant_source, mutant_binary = run / 'cache-dirty-mutant.c', run / 'cache-dirty-mutant'
    mutant_source.write_text(source.replace(target, 'item->dirty=false'))
    compile_c(mutant_source, mutant_binary, compiler)
    name, config, _, expected = cases[0]
    actual = output([mutant_binary, *config, run / (name + '.trace')])
    if actual == expected:
        raise ValueError('Cache dirty-state mutation survived the writeback regression')
    return {'hand_calculated_cases': 9, 'sampled_configurations': 48,
            'cases_per_language': len(cases), 'operations_per_language': sum(len(c[2]) for c in cases),
            'oracle': 'block-ID maps, interval intersections and last-reference positions',
            'write_policies': 'all four write-back/write-through and allocation combinations',
            'dirty_mutation': {'detected_by': name, 'expected': expected, 'observed': actual}}


def check_fill(base, run, compiler):
    expected = 'fill-cases=3120 word-bytes=8 guards=ok\n'
    binary = run / 'ch05-fill-ndebug'
    compile_c(base / 'code/ch05_fill.c', binary, compiler, ('-DNDEBUG',))
    if output([binary]) != expected:
        raise ValueError('Fill NDEBUG result differs')
    source = (base / 'code/ch05_fill.c').read_text()
    target = 'const unsigned char byte=(unsigned char)c;'
    if source.count(target) != 1:
        raise ValueError('Fill mutation anchor differs')
    mutant_source, mutant_binary = run / 'fill-byte-mutant.c', run / 'fill-byte-mutant'
    mutant_source.write_text(source.replace(target, 'const unsigned char byte=(unsigned char)(c+1);'))
    compile_c(mutant_source, mutant_binary, compiler, ('-DNDEBUG',))
    mutant = execute([mutant_binary])
    if mutant.returncode != 1 or 'fill byte differs' not in mutant.stderr or 'guards=ok' in mutant.stdout:
        raise ValueError('Fill byte mutation survived the NDEBUG validation')
    return {'ndebug_cases': 3120, 'ndebug_sanitizers': 'ASan/UBSan',
            'byte_mutation': {'exit_code': mutant.returncode, 'diagnostic': mutant.stderr.strip()}}


def check_regressions(base, run, binaries, compiler='clang'):
    run.mkdir(parents=True, exist_ok=True)
    return {'allocations': check_allocations(base),
            'cache_policies': check_cache(base, run, binaries['ch06_cache'], compiler),
            'fill_ndebug': check_fill(base, run, compiler)}
