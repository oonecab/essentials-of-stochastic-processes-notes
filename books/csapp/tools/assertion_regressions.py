"""Necessary example work and verification must survive -DNDEBUG / Python -O.

Run both modes, retain the same observable output, and require intentionally
wrong algorithms/results to fail in both modes. This is scoped to the examples
that formerly put necessary work in assertions, plus the already explicit C
allocator as a control. It does not claim every optimization is equivalent.
"""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys


PYTHON = ('ch05_loops', 'ch05_polynomial', 'ch05_fill', 'ch08_ecf',
          'ch08_io', 'ch08_shell', 'ch09_allocator', 'ch12_models',
          'ch12_server_checks')
C = ('ch05_loops', 'ch05_polynomial', 'ch09_allocator')


def _run(command, timeout=45):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    timed_out = False
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        out, err = process.communicate()
    finally:
        # A failed socket example may leave its bounded server child behind.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return {'command': list(map(str, command)), 'returncode': process.returncode,
            'stdout': out, 'stderr': err, 'timed_out': timed_out}


def _compile(compiler, source, binary, optimized):
    flags = ['-DNDEBUG'] if optimized else []
    return _run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                 '-pedantic', '-fsanitize=address,undefined', *flags,
                 str(source), '-o', str(binary)])


def _mutations():
    return [
        ('ch05_loops.py', 'combine', 'return r\n', 'return (r + 1) & MASK\n'),
        ('ch05_loops.py', 'dot6x1', 'return sum(r) & MASK', 'return (sum(r) + (mode == "6x1")) & MASK'),
        ('ch05_loops.py', 'dot6x6', 'return sum(r) & MASK', 'return (sum(r) + (mode == "6x6")) & MASK'),
        ('ch05_loops.py', 'dot6x1a', 'return sum(r) & MASK', 'return (sum(r) + (mode == "6x1a")) & MASK'),
        ('ch05_loops.py', 'merge', 'return d+a[i:]+b[j:]', 'return []'),
        ('ch05_loops.py', 'prefix', 'return p\n', 'return [x + 1 for x in p]\n'),
        ('ch05_polynomial.py', 'polynomial', 'return horner(r,x)', 'return horner(r,x) + 1'),
        ('ch05_fill.py', 'fill', 'byte=c & 255', 'byte=(c + 1) & 255'),
        ('ch08_ecf.py', 'orders', 'return sorted(result)', 'return []'),
        ('ch08_io.py', 'read', 'return result or None', 'return None'),
        ('ch08_shell.py', 'transition', 'job.state = "stopped"', 'job.state = "background"'),
        ('ch09_allocator.py', 'zero-allocation',
         'if n <= 0 or n > 65520-(4 if self.elide else 8):',
         'if n == 0:\n            return 16\n        if n < 0 or n > 65520-(4 if self.elide else 8):'),
        ('ch12_models.py', 'interleavings', 'return outcomes', 'return [0, 17, 3]'),
        ('ch05_loops.c', 'combine', 'return r;\n}', 'return r+1;\n}'),
        ('ch05_loops.c', 'dot6x1', 'for (; i < n; ++i) r += u[i]*v[i];\n    return r;',
         'for (; i < n; ++i) r += u[i]*v[i];\n    return r+1;'),
        ('ch05_loops.c', 'dot6x6', 'return ((r0+r1)+(r2+r3))+(r4+r5);',
         'return ((r0+r1)+(r2+r3))+(r4+r5)+1;'),
        ('ch05_loops.c', 'dot6x1a', 'for (; i<n; ++i) r+=u[i]*v[i];\n    return r;',
         'for (; i<n; ++i) r+=u[i]*v[i];\n    return r+1;'),
        ('ch05_loops.c', 'merge', 'while(j<n) d[k++]=b[j++];',
         'while(j<n) d[k++]=b[j++];\n    d[0]=0;'),
        ('ch05_loops.c', 'prefix', 'p[i]=s+b0;', 'p[i]=s+b0+1;'),
        ('ch05_polynomial.c', 'polynomial', 'return result;', 'return result+1;'),
    ]


def inspect_assertions(base, run, compiler='clang'):
    base, run = Path(base), Path(run)
    run.mkdir(parents=True, exist_ok=True)
    code = base / 'code'
    normal, mutations = [], []
    for name in C:
        outputs = []
        for optimized in (False, True):
            binary = run / (name + ('-ndebug' if optimized else '-normal'))
            compiled = _compile(compiler, code / (name + '.c'), binary, optimized)
            executed = _run([str(binary)]) if compiled['returncode'] == 0 else None
            item = {'source': name + '.c', 'disabled_assertions': optimized,
                    'compile': compiled, 'execution': executed}
            item['passed'] = bool(executed and executed['returncode'] == 0 and
                                  not executed['timed_out'] and not executed['stderr'])
            outputs.append(executed['stdout'] if executed else None)
            normal.append(item)
        if outputs[0] != outputs[1]:
            normal[-1]['passed'] = False
    for name in PYTHON:
        outputs = []
        for optimized in (False, True):
            command = [sys.executable, *(['-O'] if optimized else []), str(code / (name + '.py'))]
            executed = _run(command)
            outputs.append(executed['stdout'])
            normal.append({'source': name + '.py', 'disabled_assertions': optimized,
                           'execution': executed,
                           'passed': executed['returncode'] == 0 and not executed['timed_out']
                                     and not executed['stderr']})
        if outputs[0] != outputs[1]:
            normal[-1]['passed'] = False
    for filename, name, old, new in _mutations():
        original = (code / filename).read_text()
        # The first occurrence is intentional for the two C reduction returns.
        if old not in original:
            raise ValueError(f'mutation site missing: {filename} {name}')
        mutant = run / (name + '-' + filename)
        mutant.write_text(original.replace(old, new, 1))
        for optimized in (False, True):
            if filename.endswith('.c'):
                binary = run / (mutant.stem + ('-ndebug' if optimized else '-normal'))
                compiled = _compile(compiler, mutant, binary, optimized)
                executed = _run([str(binary)]) if compiled['returncode'] == 0 else None
            else:
                compiled = None
                executed = _run([sys.executable, *(['-O'] if optimized else []), str(mutant)])
            mutations.append({'source': filename, 'mutation': name,
                              'disabled_assertions': optimized, 'compile': compiled,
                              'execution': executed,
                              'passed': bool(executed and executed['returncode'] != 0
                                             and not executed['timed_out'] and executed['stderr'])})
    # A parser acceptance failure can be isolated without starting sockets.
    driver = run / 'bad_http_response.py'
    driver.write_text('import runpy\nmodule = runpy.run_path(' +
                      repr(str(code / 'ch12_server_checks.py')) + ')\n' +
                      "module['check_complete_home_response'](b'HTTP/1.0 200 OK\\r\\nContent-Length: 3\\r\\n\\r\\nbad')\n")
    for optimized in (False, True):
        executed = _run([sys.executable, *(['-O'] if optimized else []), str(driver)])
        mutations.append({'source': 'ch12_server_checks.py', 'mutation': 'wrong-body',
                          'disabled_assertions': optimized, 'execution': executed,
                          'passed': executed['returncode'] != 0 and not executed['timed_out']
                                    and bool(executed['stderr'])})
    report = {'scope': 'necessary self-checks under assertion removal; finite examples and wrong variants',
              'source_sha256': {f: hashlib.sha256((code / f).read_bytes()).hexdigest()
                                for f in [*(n + '.c' for n in C), *(n + '.py' for n in PYTHON)]},
              'normal_runs': normal, 'mutations': mutations,
              'passed': all(row['passed'] for row in normal + mutations)}
    (run / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def check_assertions(base, run, compiler='clang'):
    report = inspect_assertions(base, run, compiler)
    if not report['passed']:
        raise AssertionError('assertion-removal regression failed; inspect ' + str(Path(run) / 'report.json'))
    return report
