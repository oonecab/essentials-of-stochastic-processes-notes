# Consolidated review - Durrett Essentials of Stochastic Processes reading notes

Date: 2026-10-11 (Asia/Shanghai). Method: lead recon + 4 independent auditors
(notes-core, notes-advanced, code-audit, verif-audit); lead reproduced every
headline finding. Source evidence is in review/notes-ch1-3.md,
review/notes-ch4-6.md, review/code-audit.md, review/tooling-ux.md and
review/check_notes_full.log.

## Scores

| Area | Score |
|---|---:|
| Notes content (correctness/coverage) | 8.5/10 |
| Notes presentation / UX | 9/10 |
| Code implementation | 7.5/10 |
| Verification / evidence engineering | 5/10 |
| Overall | ~7.5/10 |

## Verified coverage facts (lead + auditors)

- 115 numbered theorems/lemmas + 2 numbered definitions: set exactly equals the book;
  162 numbered examples (56+14+10+31+19+9+23); 236 exercises (77+61+24+39+10+25).
- All 236 exercise numbers and all 117 statement page citations resolve to the
  manifest page that actually contains the item; only 1 link/manifest mismatch
  (Theorem 3.7 links #page=142, manifest says 143).
- All 150 fixtures in tools/notes_cases.json reproduced independently with a
  separate implementation (105 linear exact-rational, 30 finance tree, 15 BS/CRR).
- All 147 whole-file digests in the 7 review JSONs match current files; release
  archive/SHA256SUMS/CSP/browser/HTTP evidence internally consistent.
- check_notes.py full run passes (strict C11, ASan/UBSan, 150 fixtures, 42 invalid
  inputs, 4 simulations, CRR convergence).

## Content errors found (notes)

- MAJOR Ex 1.11(b) (ch1, ex-1-11, PDF 89): claims the chain is stationary but not
  detailed-balance; it IS reversible. Step even prints 2/35 = 2/35 then says
  "different". Fix the title and the sub-answer.
- MAJOR Example 4.29 (ch4, body-review-s46, PDF 194): traffic solution (11/7,20/7)
  and rho1=11/28 copied from the book's arithmetic slip; the displayed equations
  give (12/7,20/7), rho1=3/7.
- MINOR Ex 6.20 (ch6, ex-6-20): text says 64/25=2.208; 64/25=2.56.
- MINOR Example 6.4 (ch6, derive-c6-parity-knockout): note falsely claims the book
  printed 144.72; PDF p243 prints 414.72/49 (consistent with the tree S0=36).
- MINOR Definition ctmc (ch4, definition-ctmc): drops the book's "if this limit
  exists" hypothesis.
- MINOR Book Chapter Summary / section numbering not preserved (1.12, 2.5, 3.4,
  4.7, 4.8, 5.5, 6.7 replaced/renamed).
- MINOR ~11/39 ch4 exercise solutions use shared generic boilerplate steps.
- MINOR 30 formula decimals missing a leading zero (data-tex `\approx.xxxxxx`):
  ch1 4, ch2 15, ch3 5, ch4 6. check_notes reports leading_decimal_zeros=pass
  because readable_text's regex excludes a letter before the dot.
- NIT mislabelled "Example 3.6"; English excerpts quoting adjacent prose; sparse
  appendix cross-links; h2->h4 heading skip; print does not open closed details.

## Code findings

- MAJOR FMA contraction: clang/arm64 `-O2` contracts `p*vh+(1-p)*vt`; C and Python
  finance differ in action flags and last digits. Repro: `5 4 3 0.6666666666666666
  0.0 10 0 1 10` (7 action pairs differ). `-ffp-contract=off` restores equality.
  Makefile should set `-ffp-contract=off`.
- MAJOR C `%127s` silently splits >127-char input tokens; C accepts what Python
  rejects (linear/finance/bs).
- MINOR exit codes differ (C 3/4 vs Python 2); exact American tie (iv==cv)
  continues instead of exercises; bs prints 0 vs Python -0; Python 3.12
  compensated sum vs C naive Asian mean (N>=9); 1e-12 pivot threshold rejects a
  valid 2^-50-rate generator; near-unit diagonal I-P cancellation (0.500005530491
  vs 0.5); no error messages; no `clean` target.
- Verified sound: all algorithms correct; RNG 3-way bit-identical; 4 simulations
  replayed; make/-Werror clean; ASan/UBSan/clang-analyze clean; 14/14 HTML copies
  byte-identical.

## Verification / engineering findings

- BLOCKER (structural) check_notes.py never verifies content truth: junk text,
  emptied MathML, fake excerpts, wrong-but-in-range page anchors, stale code and
  external CSS all pass `--extract-only`; README wording implies more.
- MAJOR invalid-input loop accepts any nonzero exit (crashes pass).
- MAJOR browser acceptance stale: final pages tested only at 1800/390 (18
  variants); the README's 36-layout/4-width record is historical and 0/36 hashes
  match current pages.
- MAJOR site.tar.gz not deterministic (gzip MTIME).
- MAJOR CSS @import/url(), <base>, meta-refresh unscanned; release can ship
  external dependencies with link_validation=pass.
- MAJOR sync_code ignores extra/stale code blocks and never checks data-language.
- MAJOR published release leaks /ABSOLUTE/PATH/... paths in notes/*.json.
- MAJOR readable_numbers corrupts valid C hex floats (latent).
- MINOR close() tolerance 1e-8; single-seed sim smoke tests; non-atomic publish;
  evidence timestamps are assembly times; fixture generators live in tmp/.
