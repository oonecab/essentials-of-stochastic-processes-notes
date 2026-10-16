"""Execute the alias and side-effect examples extracted from the reading page."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import subprocess


def check_explanations(base: Path, run: Path, compiler: str):
    run.mkdir(parents=True, exist_ok=True)
    page = (base / 'notes/chapter05_optimization.html').read_text()
    match = re.search(r'<code\b[^>]*\bid="alias-functions"[^>]*>(.*?)</code>', page, re.S)
    if match is None:
        raise ValueError('The alias example is missing from the reading page')
    functions = html.unescape(match[1])
    bodies = [html.unescape(s) for s in re.findall(r'<code>(.*?)</code>', page, re.S)]
    body = next((s for s in bodies if s.startswith('++calls;')), None)
    if body is None:
        raise ValueError('The side-effect example is missing from the reading page')
    # Reference results count the original object values algebraically. Every
    # intermediate result in this small domain is representable even by C's
    # minimum required long range, including the negative cases.
    driver = r'''
#include <stdio.h>
static int calls;
static int f(void) { FUNCTION_BODY }
int main(void) {
    for (long a = -16; a <= 16; ++a) {
        long t = a, o = a;
        twice(&t, &t);
        once(&o, &o);
        if (t != 4*a || o != 3*a) {
            fprintf(stderr, "alias mismatch at %ld: %ld %ld\n", a, t, o);
            return 1;
        }
        for (long b = -16; b <= 16; ++b) {
            t = a; o = a;
            const long y = b;
            twice(&t, &y);
            once(&o, &y);
            if (t != a+2*b || o != a+2*b || y != b) return 2;
        }
    }
    long n = 2;
    twice(&n, &n);
    long t = n;
    n = 2;
    once(&n, &n);
    printf("initial=2 twice=%ld once=%ld alias-cases=33 distinct-cases=1089\n", t, n);
    calls = 0;
    int sum = 0;
    for (int i = 0; i < 4; ++i) sum += f();
    if (sum != 28 || calls != 4) return 3;
    calls = 0;
    sum = 4*f();
    if (sum != 28 || calls != 1) return 4;
    puts("side-effects: sums=28,28 calls=4,1");
    return 0;
}
'''.replace('FUNCTION_BODY', body)
    commands = []

    def command(args, expected=0):
        result = subprocess.run(list(map(str, args)), text=True, capture_output=True, timeout=60)
        commands.append({'command': [str(a).replace(str(run), 'RUN').replace(str(base), 'BOOK') for a in args],
                         'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        if expected is not None and result.returncode != expected:
            (run / 'failure.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
            raise ValueError('Explanation regression failed: ' + result.stderr)
        return result

    source = run / 'alias.c'
    source.write_text(functions + '\n' + driver)
    flags = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic', '-DNDEBUG']
    expected = ('initial=2 twice=8 once=6 alias-cases=33 distinct-cases=1089\n'
                'side-effects: sums=28,28 calls=4,1\n')
    configurations = [('O0', ['-O0']), ('O3', ['-O3']),
                      ('sanitized', ['-O2', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]
    for name, extra in configurations:
        binary = run / name
        command([*flags, *extra, source, '-o', binary])
        if command([binary]).stdout != expected:
            raise ValueError('Reading example output differs: ' + name)

    # The specific unsafe optimization discussed in the text must be detected.
    mutant_text, count = re.subn(r'(void twice\([^)]*\)\s*\{).*?(\})',
                                r'\1\n    *xp += 2 * (*yp);\n\2', functions, count=1, flags=re.S)
    if count != 1 or mutant_text == functions:
        raise ValueError('Alias mutation target is missing or already incorrect')
    mutant = run / 'merged.c'
    mutant.write_text(mutant_text + '\n' + driver)
    command([*flags, '-O3', mutant, '-o', run / 'merged'])
    rejected = command([run / 'merged'], expected=1)
    if 'alias mismatch' not in rejected.stderr:
        raise ValueError('Mutation failed for an unrelated reason')

    invalid = run / 'const-write.c'
    invalid.write_text('void invalid(const long *yp) { *yp = 4; }\n')
    result = command([*flags, '-fsyntax-only', invalid], expected=None)
    if result.returncode == 0 or not any(s in result.stderr for s in ('const-qualified', 'read-only')):
        raise ValueError('The compiler did not diagnose writing through const long *')
    report = {'status': 'passed', 'source': 'notes/chapter05_optimization.html#alias-functions',
              'extracted_code_sha256': hashlib.sha256(functions.encode()).hexdigest(),
              'configurations': [name for name, _ in configurations], 'ndebug': True,
              'alias_cases_per_run': 33, 'distinct_cases_per_run': 1089,
              'initial_two': {'twice': 8, 'once': 6}, 'side_effect_calls': [4, 1],
              'unsafe_merge_rejected': True, 'const_write_rejected': True,
              'scope': 'Small representable long values; no signed-overflow or performance claim.',
              'commands': commands}
    (run / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report
