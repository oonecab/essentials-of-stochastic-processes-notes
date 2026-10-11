# Code audit - 7 C11 / Python 3 program pairs

Auditor: teammate `code-audit` (shared task `task-3`). Date: 2026-10-11.
Project: Durrett, Essentials of Stochastic Processes (3rd ed.) reading-notes repo.
Scope: `code/` only (14 programs + Makefile/README/programs.json/per-chapter READMEs);
`tools/check_notes.py` and `tools/notes_cases.json` were treated as claims and independently
falsified where possible. All findings were reproduced by the auditor; no file under `code/`
or `tools/` was modified (the only file written is this report).

## Environment and method

- macOS/arm64 (Apple Silicon), `cc` = Apple clang 17.0.0, bundled Python 3.13.2, numpy 2.3.5.
- `make -C code`, `make -B -C code` (clean, `-Wall -Wextra -Werror -pedantic`); pre-built
  binaries in `code/build/` were hashed before/after a forced rebuild and are byte-identical
  to the sources.
- `clang -std=c11 -O1 -g -fsanitize=address,undefined` on all 7 C programs, run on documented
  and adversarial inputs: no ASan/UBSan diagnostics. `clang --analyze`: no findings.
  GNU gcc/`-fanalyzer` is not present on this host (`gcc` is an Apple-clang shim).
- `python3 tools/sync_code.py` (read-only): program_pairs=7, source_files=14, differences=[],
  i.e. the 14 HTML reading copies are byte-identical to the standalone sources.
- Independent references written in `/tmp`: exact `fractions` solvers, numpy, an independent
  xorshift32, independent Black-Scholes/CRR, and an independent replay of each simulation.
- Random sweeps: 60 `linear` cases (all 7 modes, n up to 5) vs numpy; 425 `finance` cases
  (all 8 payoffs, American/European, N up to 5) vs exact Fraction trees; 14 `bs` cases vs the
  closed-form formula; 4 CRR convergence cases vs an independent iterative tree; 150
  bash-driven C/Python parity probes.

## Per-program verdicts

| Program | Verdict | One-line justification |
|---|---|---|
| `linear.c/.py` | **7/10** | Math is correct for all 7 modes (60/60 random cases match numpy; textbook values match), but over-long tokens are silently split by C (F2), error exit codes differ (F3), the 1e-12 pivot threshold rejects valid ill-conditioned generators (F7), and near-unit diagonals lose ~1e-5 (F8). |
| `poisson.c/.py` | **9/10** | Exponential-interval Poisson count is correct; RNG bit-exact with independent xorshift32; counts/theory independently reproduced. Only cosmetic nits. |
| `renewal.c/.py` | **9/10** | Length-bias frequencies correct (0.1/0.9); independent replay matches exactly. |
| `ctmc.c/.py` | **9/10** | Two-state CTMC jump/time statistics correct (time proportions 1/3, 2/3; sample sojourn means 0.502/0.993 vs theory 0.5/1.0); independent replay matches. |
| `stopping.c/.py` | **9/10** | Gambler's-ruin stopping time and exit side correct (E=25, P(up)=0.5); independent replay matches. |
| `finance.c/.py` | **6/10** | All 8 payoff trees, discounting and delta independently verified (240 nodes + exercise 6.8 exact), but C/Python outputs can differ through FMA contraction (F1) and Python's compensated `sum` (F6), the documented tie rule is violated by rounding (F4), and over-long tokens are accepted by C only (F2). |
| `bs.c/.py` | **8/10** | Black-Scholes, put/call parity, CRR convergence and the t=0/vol=0 limits are correct; C prints `0` where Python prints `-0` for the exact-ATM deterministic limit (F5), exit codes differ (F3), and over-long tokens are accepted by C only (F2). |

## Findings

### F1 (Major, portability/parity) - FMA contraction makes C and Python disagree on `finance` action flags and last digits

- **Files:** `code/Makefile:1-2` (no `-ffp-contract` setting), `code/chapter06_mathematical_finance/finance.c:41,44`.
- **Description:** `cc -O2` on arm64 contracts `p*vh + (1-p)*vt` into a fused multiply-add
  (clang default is `-ffp-contract=on`; FMA is baseline on Apple Silicon). Python evaluates the
  multiply and add separately, so `cv` can differ by 1 ulp and the `iv >= cv` action test flips.
  At N=12 the accumulated difference also reaches the 12th printed digit.
- **Reproducer:**
```sh
printf '5 4 3 0.6666666666666666 0.0 10 0 1 10\n' | ./code/build/finance > /tmp/c.txt
printf '5 4 3 0.6666666666666666 0.0 10 0 1 10\n' | python3 code/chapter06_mathematical_finance/finance.py > /tmp/p.txt
diff /tmp/c.txt /tmp/p.txt
# 8 lines differ only in column 5, e.g.
# < HH 36 26 1 0        (C)
# > HH 36 26 1 1        (Python)
clang -std=c11 -O2 -Wall -Wextra -Werror -pedantic -ffp-contract=off \
  code/chapter06_mathematical_finance/finance.c -lm -o /tmp/fin_off   # diff with Python is now empty
```
- **Observed:** same input, same exit code 0, C emits action `0` and Python `1` at 8 internal nodes
  (`--ffp-contract=off` reproduces Python exactly). At `12 100 1.2 0.9 0.05 100 3 1 150` the two
  outputs even differ in value columns by ~1e-15 relative.
- **Expected:** identical output for identical input (or a documented tolerance).
- **Fix:** add `-ffp-contract=off` to `CFLAGS` (portable to clang and gcc), or make both
  implementations use the same explicit fused/unfused form; long term, make exercise decisions
  tolerance-based (see F4).

### F2 (Major, input validation/parity) - C `%127s` silently splits over-long tokens; Python rejects them

- **Files:** `code/chapter01_markov_chains/linear.c:9,17`, `code/chapter06_mathematical_finance/finance.c:10,18`,
  `code/chapter06_mathematical_finance/bs.c:6`; Python counterparts check `len(s)>127`
  (`linear.py:10,14`, `finance.py:6,9`, `bs.py:7`).
- **Description:** `scanf("%127s", s)` reads at most 127 characters and leaves the rest of the
  token in the stream, where it is consumed as the *next* field. Python has no such truncation
  and rejects any token longer than 127 characters. A crafted 128-character token therefore makes
  C accept input that Python rejects (the trailing character can fill the otherwise-missing field).
- **Reproducer:**
```sh
TOK=$(python3 -c "print('0'*127+'1',end='')")      # 128 chars
printf '2\n%s 1 0\n' "$TOK" | ./code/build/linear pstation
# C: prints "0.5 0.5", exit 0   (token split into "0"*127 and "1")

printf '2\n%s 1 0\n' "$TOK" | python3 code/chapter01_markov_chains/linear.py pstation
# Python: exit 2 (token length 128 > 127)

# Same defect in finance and bs:
TOK2=$(python3 -c "print('0'*127+'1',end='')")
printf '%s 4 1 .5 .25 4 0 0\n' "$TOK2"  | ./code/build/finance    # exit 0
printf '%s 4 1 .5 .25 4 0 0\n' "$TOK2"  | python3 code/chapter06_mathematical_finance/finance.py  # exit 2
TOKB=$(python3 -c "print('1'*127+'1',end='')")
printf '%s 1 .05 .2\n' "$TOKB" | ./code/build/bs                    # exit 0 (S=1.11e126)
printf '%s 1 .05 .2\n' "$TOKB" | python3 code/chapter06_mathematical_finance/bs.py  # exit 2
```
- **Observed:** C accepts and computes a result; Python exits 2. The documented limit is "at most
  127 characters" (Python) but C silently truncates.
- **Expected:** both reject tokens >127 chars with a nonzero exit.
- **Fix:** after each `%127s`, detect truncation (e.g. peek the next byte with `getc(stdin)` and
  reject if it is not whitespace/EOF), or read with a larger buffer/`fgets` and enforce the length
  explicitly.

### F3 (Minor, parity) - C returns 3/4 where Python always returns 2 on failure

- **Files:** `linear.c:73,86,91,94` returns 3, `linear.c:47,52,58,64,70,81` returns 2,
  `linear.py:71` maps every error to 2; `finance.c:52,54` returns 4/3, `finance.py:41` maps all
  to 2; `bs.c:24,26,27` returns 2 and `bs.c:29,32,34,37,41` returns 3, `bs.py:36` maps all to 2.
- **Description:** the C programs distinguish input errors (2), numerical/solve failure (3) and
  allocation failure (4, `finance` only). The Python programs catch all exceptions and call
  `sys.exit(2)`. Same input can therefore produce different exit codes even though the README only
  promises "nonzero".
- **Reproducer:**
```sh
printf '2\n1 0\n0 1\n' | ./code/build/linear pstation ; echo "C=$?"      # C=3 (singular)
printf '2\n1 0\n0 1\n' | python3 code/chapter01_markov_chains/linear.py pstation ; echo "Py=$?"  # Py=2
printf '100 100 1 1000 .2\n' | ./code/build/bs ; echo "C=$?"              # C=3 (disc underflow)
printf '100 100 1 1000 .2\n' | python3 code/chapter06_mathematical_finance/bs.py ; echo "Py=$?"  # Py=2
```
- **Observed:** C=3 / Python=2 (and the same 2-vs-3 split for every solve/numerical failure; only
  `finance` can return 4, and only on `calloc` failure, which is not reachable with the N<=12 cap).
- **Expected:** parity of exit codes if the task's "edge behavior equal" criterion is applied.
- **Fix:** if exact code parity is desired, define a shared error taxonomy and map Python
  exceptions to 2/3/4; otherwise document the divergence explicitly in `code/README.md`.

### F4 (Minor, correctness vs docs) - exact exercise/continuation ties are resolved differently from the documented rule

- **Files:** `code/chapter06_mathematical_finance/finance.c:44` (`iv>=cv`), `finance.py:33`.
- **Description:** the notes say a node is exercised when the immediate payoff is positive and
  "not less than" the continuation value (`iv >= cv`). In floating point, `cv` can round 1 ulp above
  an exactly equal `iv`, so the program continues instead of exercising even when the exact values
  tie. Values are unaffected at a tie (`max(iv,cv)`), but the printed action flag is wrong and a
  1-ulp sign flip in either direction can select the wrong branch.
- **Reproducer:**
```sh
printf '3 100 2 0.6666666666666666 0.0 100 1 1 50\n' | ./code/build/finance | grep '^TT '
# TT 44.4444444444 55.5555555556 -1 0
python3 - <<'PY'
from fractions import Fraction as F
d=F('0.6666666666666666'); p=(1-d)/(2-d); S=100*d*d
iv=max(100-S,F(0)); cv=(p*max(100-2*S,F(0))+(1-p)*max(100-S*d,F(0)))
print('iv==cv:', iv==cv, '=> documented action', int(iv>0 and iv>=cv))
PY
```
- **Observed:** node `TT` prints action 0; exact arithmetic gives `iv == cv == 500/9`, so the
  documented rule requires action 1. The bundled "near exercise tie" fixtures only cover strict
  inequalities, not exact ties.
- **Expected:** exercise at an exact tie (or an explicitly documented tie convention).
- **Fix:** compare with a relative tolerance, e.g. `iv >= cv - 1e-12*max(1,abs(iv),abs(cv))`, in
  both languages, and add a tie fixture.

### F5 (Minor, output parity) - Python prints `-0` where C prints `0` for the deterministic exact-ATM limit of `bs`

- **Files:** `code/chapter06_mathematical_finance/bs.c:30` (`fmax(-gap,0)`), `bs.py:13` (`max(-gap,0)`).
- **Description:** at `gap == 0`, C's `fmax(-0.0, 0.0)` returns `+0.0`, while Python's
  `max(-0.0, 0)` returns its first argument `-0.0`. The two values compare equal, so the bundled
  `math.isclose` checks pass, but the printed text differs.
- **Reproducer:**
```sh
printf '100 100 0 .05 .2\n' | ./code/build/bs   # 0 0 0.5
printf '100 100 0 .05 .2\n' | python3 code/chapter06_mathematical_finance/bs.py   # 0 -0 0.5
printf '100 100 1 0 0\n'   | ./code/build/bs   # bundled fixture "discounted strike": 0 0 0.5
printf '100 100 1 0 0\n'   | python3 code/chapter06_mathematical_finance/bs.py   # 0 -0 0.5
```
- **Observed:** Python emits the token `-0`, C emits `0`; `od -c` confirms the extra `-` byte.
- **Expected:** identical text (or a normalized zero).
- **Fix:** in `bs.py`, write `put = 0.0 if put == 0 else put` (and likewise for `c`/`delta`), or use
  a `fmax`-equivalent; alternatively print with a formatter that normalizes negative zero.

### F6 (Minor, parity) - Python 3.12+ compensated `sum()` makes the Asian payoff differ from C in the last digits

- **Files:** `code/chapter06_mathematical_finance/finance.py:20`
  (`sum(x/len(ss) for x in ss)`) vs `finance.c:24` (`mean += ss[i]/(n+1)`).
- **Description:** since Python 3.12, the builtin `sum()` uses Neumaier compensated summation for
  floats, while C accumulates the same divided terms naively in path order. For N=12 there are
  1963/4096 paths whose mean differs, up to 5.7e-14 absolute; this propagates to value columns.
  This is *not* FMA - it still reproduces with `-ffp-contract=off`.
- **Reproducer:**
```sh
printf '9 100 1.2 0.9 0.05 100 2 1 150\n' | ./code/build/finance > /tmp/c.txt
printf '9 100 1.2 0.9 0.05 100 2 1 150\n' | python3 code/chapter06_mathematical_finance/finance.py > /tmp/p.txt
diff /tmp/c.txt /tmp/p.txt
# 483c483
# < TTTHHHTT 102.036672 0.00866468571428 0.000594421582076 0
# > TTTHHHTT 102.036672 0.00866468571429 0.000594421582076 0
```
- **Observed:** values differ in the 12th significant digit (relative ~1e-12); the bundled
  comparison tolerance (1e-8) hides it. `check_notes.py`'s only Asian overflow fixture uses N=2.
- **Expected:** identical output for identical input (or a documented tolerance).
- **Fix:** use the same explicit accumulation loop in Python (or enable/implement the same
  compensation in C) if byte-identical parity is desired.

### F7 (Minor, numerical robustness) - the 1e-12 pivot threshold rejects valid, uniquely-solvable ill-conditioned generators

- **Files:** `code/chapter01_markov_chains/linear.c:31`, `linear.py:39`.
- **Description:** after per-row scaling, any pivot with magnitude < 1e-12 is treated as singular.
  This is documented in the notes, but it is a false negative for legitimate CTMCs whose generator
  has a tiny (but exactly representable) transition rate, even when the stationary distribution is
  simple and numpy solves the system without difficulty.
- **Reproducer:**
```sh
printf '3\n-1 1 0\n1 -1.0000000000000009 8.881784197001252e-16\n0 8.881784197001252e-16 -8.881784197001252e-16\n' \
  | ./code/build/linear qstation ; echo "C=$?"      # C=3
printf '3\n-1 1 0\n1 -1.0000000000000009 8.881784197001252e-16\n0 8.881784197001252e-16 -8.881784197001252e-16\n' \
  | python3 code/chapter01_markov_chains/linear.py qstation ; echo "Py=$?"   # Py=2
python3 - <<'PY'
import numpy as np
e=2.0**-50; Q=np.array([[-1,1,0],[1,-(1+e),e],[0,e,-e]])
A=Q.T.copy(); A[-1]=1; print(np.linalg.solve(A,[0,0,1.0]))   # [1/3 1/3 1/3]
PY
```
- **Observed:** both programs reject (C=3, Python=2); the matrix has exactly zero row sums in
  double and the unique stationary distribution `(1/3,1/3,1/3)` (condition number ~3e15).
- **Expected:** either solve it (iterative refinement / relative threshold) or document the
  rejection more prominently; the current note wording ("singular or severely ill-conditioned")
  is defensible but this is a practical false rejection.
- **Fix:** use a condition-aware threshold relative to the row/scaled norm, or add one step of
  iterative refinement / a fallback (e.g. solve the detailed-balance system when it exists).

### F8 (Minor, numerical quality) - near-unit diagonals lose absolute accuracy because `I-P` is formed explicitly

- **Files:** `code/chapter01_markov_chains/linear.c:71` (`p[j][i]-(i==j)`), `linear.py:52`;
  loose acceptance in `linear.c:58` / `linear.py:31` (`1e-8`).
- **Description:** for a chain with diagonal near 1, `p - 1` loses ~16 digits; the cancellation is
  amplified by the condition number (~1e12 here). The program returns the exact stationary
  distribution *of the parsed doubles* (numpy agrees), but that differs from the mathematically
  intended statement of the input by ~1e-5, and the 1e-8 row-sum tolerance admits the input without
  warning.
- **Reproducer:**
```sh
printf '2\n0.999999999999 1e-12\n1e-12 0.999999999999\n' | ./code/build/linear pstation
# 0.500005530491 0.499994469509   (C and Python identical; numpy.linalg.solve gives the same)
# mathematically intended stationary distribution: 0.5 0.5
```
- **Observed:** `0.500005530491 0.499994469509` (error ~1.1e-5) for a row-stochastic input whose
  rows sum to exactly 1.0 in double.
- **Expected:** ideally `0.5 0.5`, or an explicit conditioning warning/rejection.
- **Fix:** tighten the row-sum tolerance (e.g. 1e-12 relative) and/or solve for the stationary
  distribution without forming `I-P` explicitly (e.g. power iteration on `P` with normalization, or
  compensated arithmetic), and report a conditioning estimate.

### F9 (Nit, maintainability) - `finance.c` path strings rely on `calloc` zeroing for NUL termination

- **File:** `code/chapter06_mathematical_finance/finance.c:35-37`.
- **Description:** only `nodes[h].path[len]='H'` / `'T'` is written; the terminating `'\0'` at
  `path[len+1]` is never stored explicitly. It happens to be zero because `nodes` was `calloc`ed and
  children are only written once, and the `char path[14]` size is sufficient for N<=12. The code is
  correct as-is but fragile (a later change to `malloc`, node reuse, or a path short-circuit would
  break it).
- **Fix:** write `nodes[h].path[len+1]='\0';` explicitly (same for `t`).

### F10 (Nit, maintainability/documentation) - xorshift32 RNG is duplicated eight times and the seed is an undocumented literal

- **Files:** `poisson.c/.py:4-7`, `renewal.c/.py:3-6`, `ctmc.c/.py:4-7`, `stopping.c/.py:3-6`
  (all `state=UINT32_C(20261010)` / `state=20261010`).
- **Description:** the same six-line generator is copied into four C and four Python files. That is
  a reasonable self-containment choice for standalone examples, but the seed value itself
  (20261010) is never named or explained in the code or the per-chapter READMEs, so reproducing a
  figure requires reading the source. The generator itself was independently verified (see below).
- **Fix:** add a one-line comment naming the algorithm (Marsaglia xorshift32, shifts 13/17/5) and
  the seed, and mention both in `code/README.md`.

### F11 (Nit, usability) - no error message is emitted on any failure path

- **Files:** every C `main` returns silently; `linear.py:71`, `finance.py:41`, `bs.py:36` catch the
  exception and discard it, and `main()` never raises a caught exception's text.
- **Description:** a user supplying bad input gets only a nonzero exit status. The README says
  only "nonzero exit code", so this is not a contract violation, but it makes debugging harder.
- **Fix:** print a short diagnostic to `stderr` (and keep the exit codes) in both languages.

### F12 (Nit, build hygiene) - Makefile has no `clean` target and no explicit floating-point contract setting

- **File:** `code/Makefile:1-24`.
- **Description:** `make -B -C code` works and is warning-free, but there is no `clean`, and
  `-ffp-contract` is left at the compiler default (the root of F1). The `1e-6` normalization check
  in `linear.c:94` / `linear.py:66` is the only threshold not discussed in the notes.
- **Fix:** add `clean` and `-ffp-contract=off`; document the `1e-6` check next to the `1e-8`/`1e-12`
  thresholds.

## Parity / edge-case results

| # | Program | Input tried | C result | Python result | Verdict |
|---|---|---|---|---|---|
| 1 | poisson/renewal/ctmc/stopping | documented no-arg run | rc 0 | rc 0 | byte-identical; independently replayed; theory within MC error |
| 2 | RNG (all sims) | first 20 raw states/uniforms | - | - | 3-way identical (C, source Python, independent numpy uint32 xorshift32) |
| 3 | linear (all 7 modes) | 60 random n<=5 cases | rc 0 | rc 0 | byte-identical; matches numpy to <1e-8 |
| 4 | linear pstation/qstation | random n=64 chain / birth-death Q | rc 0 | rc 0 | byte-identical, sum=1 |
| 5 | linear psteps | n=64, k=100000, 4 random chains | rc 0 | rc 0 | byte-identical (Python ~11 s, C ~0.2 s) |
| 6 | linear | tokens `1`, `1.`, `.5`, `+1`, `1e0`, `1E0`, `1e+0`, `01.0`, `1e-400` | rc 0/2 as expected | same | same acceptance |
| 7 | linear | `nan`, `NaN`, `inf`, `-inf`, `0x1p0`, `1_0`, `1,0`, `1e`, `.`, `+`, `-.`, `1.2.3`, `1e309` | rc 2 | rc 2 | both reject |
| 8 | linear | integer tokens `+2`, `02`, `-2`, `2.0`, `0x2`, >2^31, 26-digit | - | - | same exit (0/2) |
| 9 | linear | trailing whitespace | rc 0 | rc 0 | both accept |
| 10 | linear | extra token, too few tokens, empty stdin | rc 2 | rc 2 | both reject |
| 11 | linear | n=65 (>MAX 64), 200-digit n token | rc 2 | rc 2 | both reject |
| 12 | linear | 128-char `0`*127+`1` token | **rc 0**, prints `0.5 0.5` | **rc 2** | **F2 parity/validation bug** |
| 13 | linear | identity 2x2 (non-unique stationary) | rc 3 | rc 2 | F3 exit-code divergence; both fail |
| 14 | linear | exact 2^-50 CTMC generator (F7) | rc 3 | rc 2 | F7 + F3 exit codes; numpy solves uniquely |
| 15 | linear | near-unit-diagonal P (F8) | `0.500005530491 ...` | same | F8; numpy agrees with program, not with intended 0.5 |
| 16 | finance (all 8 payoffs, N=3) | 16 runs, 240 nodes reconstructed | rc 0 | rc 0 | byte-identical; every value/delta/action matches independent payoff + recurrence |
| 17 | finance | 425 random valid cases vs exact Fraction trees | - | - | 3 action-only C/Python diffs (F1), 5 exact-tie action diffs (F4), values within 2e-9 |
| 18 | finance N=12 kind 2 | `12 ... 2 1 ...` | last digit `...428` | `...429` | F6 (compensated sum); persists with `-ffp-contract=off` |
| 19 | finance N=12 kind 3 | `12 ... 3 1 ...` | last digit | last digit | F1 (FMA); disappears with `-ffp-contract=off` |
| 20 | finance | 128-char token crafted as N=0/s0=1 | **rc 0** | **rc 2** | F2 |
| 21 | finance | N=13, kind=8, american=2, d>=1+r, missing/extra field, `inf` | rc 2 | rc 2 | both reject |
| 22 | finance | exercise vs continue near tie (bundled N=1 fixtures) | rc 0 | rc 0 | both follow `iv>=cv`; exact ties untested (F4) |
| 23 | bs | 14 varied normal-mode cases | rc 0 | rc 0 | byte-identical; matches closed form to <1e-9 |
| 24 | bs convergence | 4 cases, n=16..512 | rc 0 | rc 0 | byte-identical; matches independent CRR to <5e-12; converges to BS |
| 25 | bs | t=0 ATM / `100 100 1 0 0` | `0 0 0.5` | `0 -0 0.5` | **F5 output parity bug** |
| 26 | bs | r=+-1000, r=1e308 (exp over/underflow) | rc 3 | rc 2 | F3 exit-code divergence; both fail |
| 27 | bs | t<0, vol<0, s<=0, k<=0, extra token, unknown/extra mode | rc 2 | rc 2 | both reject |
| 28 | bs | 128-char `1`*127+`1` token | **rc 0** (S=1.11e126) | **rc 2** | F2 |
| 29 | all C | ASan/UBSan on documented + adversarial inputs | rc 0 | - | no diagnostics; analyzer clean |
| 30 | build | `make -C code`, `make -B -C code` | rc 0 | - | warning-free; pre-built binaries hash-identical |
| 31 | sync | `python3 tools/sync_code.py` | - | - | 7 pairs, 14 files, `differences=[]` |

Coverage note on the repo's own checks: `tools/check_notes.py` compares floats with
`abs_tol=rel_tol=1e-8`, so it cannot see F5 (`-0` vs `0`) or F6 (1e-12). It *does* compare finance
`action` flags between C and Python, but every bundled finance fixture has N<=4 and none triggers
F1; the bundled "Asian overflow-safe mean" fixture is N=2, so F6 is also not triggered. The
over-long-token F2 is outside the fixture language entirely.

## Verified-correct highlights

- **RNG.** The xorshift32 state update (`<<13`, `>>17`, `<<5`) is well-defined on `uint32_t` (the
  shifts are by less than the width; unsigned wrap is guaranteed) and the C output is bit-identical
  to the Python source *and* to an independently written numpy `uint32` reference for the first 20
  draws. `(state+0.5)/2^32` lies in `(0,1)`, so the `-log(u)` calls are always finite. The four
  simulation programs produce byte-identical C/Python output over 700k RNG draws.
- **Simulations.** Independent replays reproduce every count/frequency exactly: Poisson(6) counts
  for 100000 repetitions (`P(X>=16)` last class), renewal cycle/time frequencies (0.49876/0.09955,
  theory 0.5/0.1), CTMC time proportions and sojourn means (0.3359/0.6641 vs 1/3/2/3; 0.502/0.993
  vs 0.5/1.0), and stopped-walk mean/side (24.95298/0.49839 vs 25/0.5). The theory columns match
  closed forms to ~1e-13.
- **`linear` math.** 60/60 random cases across pstation/qstation/psteps/pprob/ptime/qprob/qtime
  agree byte-for-byte between C and Python and with numpy to <1e-8. Textbook checks:
  `P=[[.7,.3],[.2,.8]]` gives `pi=(0.4,0.6)`, `psteps` error halves per step, gambler's-ruin
  `pprob=[0,1/3,2/3,1]`, `ptime=[0,2,2,0]`. The notes' scaling claim is true: `qstation` on
  `Q*1e-15` (and even `Q*1e-300`) returns the same stationary distribution, and `qtime` scales to
  `5e14`/`5e299`. n=64 cyclic chain gives the uniform distribution.
- **`finance` math.** Exercise 6.8 (`3 4 2 .5 .25 4 2 0 0`) gives exactly `152/125 = 1.216` at the
  root with all 15 node values matching an exact Fraction tree. An independent reconstruction
  checked 240 nodes over all 8 payoffs x {European, American}: stock paths, payoff (call, put,
  Asian mean including S0, floating-strike lookback put/call, digital, capped call, up-and-out put),
  discounting, delta `(V_H-V_T)/(S(u-d))` and action codes all match. At N=12 all 8191 nodes are
  produced; `N=0` returns the immediate payoff.
- **`bs` math.** The standard case gives `10.4505835722 / 5.57352602226 / 0.636830651176`,
  matches `erfc`-based Black-Scholes and put-call parity, and the 14-case sweep (including negative
  r, huge vol, tiny T, near-zero S/K) matches the closed form to <1e-9. CRR with n=16..512 matches
  an independent iterative tree to <5e-12 and converges to the BS value. The `t=0`/`vol=0`
  deterministic limits and the `delta=1/2` convention are implemented as documented. The CRR
  `d<R<u` check is performed for every n as the notes claim.
- **Robustness/build.** `make -C code` and a forced `make -B -C code` are clean under
  `-std=c11 -Wall -Wextra -Werror -pedantic`; the pre-existing `code/build/*` binaries are
  byte-identical to a fresh rebuild. ASan/UBSan runs on all 7 programs (documented examples, N=12
  finance, N=64 linear, malformed inputs) produced no diagnostics and `clang --analyze` is clean.
  No VLAs, no `M_PI`, no non-standard functions; only `libm` is needed. `tools/sync_code.py`
  confirms all 14 HTML reading copies are byte-identical to the sources.

## Notes on method / limits

- The two Major findings are platform-sensitive: F1 requires an FMA-capable target (Apple Silicon
  reproduces it with the supplied `Makefile`; x86-64 builds without FMA may not), and F2 is a pure
  parsing difference visible anywhere. F6 requires Python 3.12+ (`sum()` compensation) and N>=9.
- The 425-case finance sweep compared C/Python and against exact rationals; the exact-tie action
  mismatches (F4) were classified by recomputing `iv-cv` with `Fraction`.
- Not independently verified here: behaviour under `LC_NUMERIC` other than the C locale (the C
  programs never call `setlocale`, so the default C locale applies), and the `calloc` failure path
  in `finance.c` (unreachable with N<=12 without artificial memory limits).
