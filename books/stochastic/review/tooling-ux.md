# Tooling, Evidence and HTML/UX Audit

- Project: Durrett, Essentials of Stochastic Processes (3rd ed.) reading notes
- Auditor: verif-audit (shared task task-4)
- Audit date: 2026-10-11 (Asia/Shanghai)
- Method: line-by-line reading; targeted experiments in /tmp copies; independent recomputation
  of all 150 fixtures; byte-level hash/count checks of reviewed JSON; static HTML/CSS/JS
  inspection plus recorded browser/HTTP evidence. No tracked file was modified. The full
  sanitizer run was not independently re-run (shared compiler resources); its recorded
  artifacts were verified. --extract-only was re-run on a clean copy.

## 1. Verdict per area

| Area | Score | Justification |
|---|---:|---|
| tools/check_notes.py | 4/10 | It really compiles/runs the 7 C/Python pairs with strict flags and sanitizers, and checks structure, ids, counts, links and 150 numeric fixtures. But content checks are metadata/structure-only: junk text, an emptied MathML body, a fake excerpt, a wrong-but-in-range PDF page and a stale code block all pass --extract-only (reproduced). Invalid-input checks accept crashes. Some report fields are hard-coded. |
| tools/sync_code.py + tools/readable_numbers.py | 5/10 | sync_code keeps the 14 intended code blocks byte-identical and escape/unescape round-trips entity-like source exactly in the normal path. It silently ignores extra/stale code blocks not bound to an expected id, does not verify data-language, and uses a regex rather than an HTML parser. readable_numbers is safe for Python (AST check) and protects C strings/comments, but its C lexer corrupts valid hex-float literals; readable_text can rewrite URL/path segments. |
| deploy/build_release.py | 5/10 | Local file/HTML links and PDF inclusion work; CSP inline-script hashes match the final pages; archive/SHA256SUMS/release metadata are internally consistent (verified against the published archive). But the tarball is not deterministic, publish is not atomic, CSS url()/@import/<base>/meta-refresh dependencies are not validated, and the release ships review JSON with absolute /ABSOLUTE/PATH/... paths. |
| Evidence integrity | 5/10 | All whole-file bytes/sha256 fields in 147 entries across 7 JSONs match current files; counts match (9/236/1028/66/132/150/115/2/146/4/3/7926/7/14); raw browser layouts, HTTP responses and screenshot hashes match. However the README presents 36 historical 4-viewport layouts as the acceptance record, while final pages were tested at 1800/390 only (18 variants); the 36 historical hashes match 0/36 current pages. Raw evidence files are not hash-pinned, timestamps are assembly times, and canonical per-block hashes depend on untracked tmp/ scripts. |
| HTML/CSS/UX | 7/10 | Strong static implementation: semantic landmarks, 17px/1.9 type, 860px measure, 240px TOC, 3-column layout at >=1440px with 280px rail, mobile collapse, native MathML, SVG accessible names, good contrast, local scroll wrappers, no external resources in current pages, no-JS fallback. Gaps: final-page browser checks cover only 1800/390; print does not expand closed details; deep-link auto-open and rail correctness are not programmatically asserted; MathML inside annotations is excluded from badMath. |

Overall: 5/10. The suite is a useful consistency and smoke-test harness, not a content
verifier. It can show that the bundle is internally self-consistent and that fixed numeric
examples currently pass; it cannot prove that the notes faithfully reproduce the book.

## 2. What the suite does and does not guarantee

### A green run guarantees

1. Structure/consistency: exactly 9 HTML pages; unique ids; allowed tags and balanced
   open/close tags under its own stack; one shared first style block across pages; required
   annotation interface anchors; no duplicate program blocks.
2. Coverage/order: HTML exercise sequence equals source_manifest.json for chapters 1-6
   (236 exercises); numbered statement set equals the manifest (115 theorems/lemmas + 2
   definitions = 117); 66 annotation groups / 132 cards; 146 excerpt blocks; 4 preface
   paragraphs; 3 axioms; anchors/indexes present.
3. Code file/HTML identity: after entity decoding, the 14 embedded program bodies equal
   the standalone code files byte-for-byte; sync_code --write can restore them in the
   normal <code id=...> case.
4. Program execution: 7 C sources compile as strict C11 (-Wall -Wextra -Werror -pedantic)
   and under ASan+UBSan; Python and C outputs agree on 150 hard-coded fixtures; four
   fixed-seed simulations pass coarse analytic smoke checks; 42 malformed inputs exit
   non-zero; the CRR sequence converges.
5. Known PDF/bundle: source and web PDF both match the manifest SHA-256; PDF links point
   at the bundled PDF with a fragment in 1..282; local links resolve; build_release packs
   HTML/code/JSON/PDF, computes CSP hashes from the final inline scripts, and emits a
   current archive whose SHA-256 and SHA256SUMS are internally consistent.
6. Partial evidence binding: whole-file, 18 current browser-layout, screenshot and HTTP
   response hashes match current files.

### A green run does NOT guarantee

- Exercise text, solution mathematics, proof validity, theorem/quote/excerpt fidelity,
  statement truth, or semantic PDF-page accuracy. Nothing compares rendered text or MathML
  to the PDF or to a mathematical oracle.
- That a statement's MathML corresponds to its data-tex; only brace balance, absence of
  merror, positive rendered height and leading-zero form are checked.
- HTML/CSS validity beyond the hand-written tag allowlist: ARIA, attribute semantics, CSS
  parsing, @import/url(), <base>, meta-refresh and external-dependency safety are unchecked.
- Runtime JS beyond page load, error events, one rail-visibility rule and two code-toggle
  booleans; deep-link auto-open and per-link behaviour are not exhaustively tested.
- Graceful rejection of invalid input: any non-zero exit (including a crash) is accepted.
- Deterministic releases or atomic publication.
- That the 150 fixtures are genuinely independent: the checker consumes a JSON oracle and
  never verifies provenance. This audit independently matched all 150, so the current data
  is correct, but the harness does not enforce independence.
- Statistical correctness of simulations beyond one fixed seed and coarse tolerances.
- That historical 36-layout/40-layout browser records describe the final HTML; their page
  hashes do not match current pages.

## 3. Findings

Severity: Blocker = invalidates the central claim; Major = materially weakens the
guarantee; Minor = limited/local; Nit = polish.

### F-01 - Blocker - content truth is not checked; junk content passes
- File:line: tools/check_notes.py:33-40 (statement/excerpt metadata only), 62-65
  (exercise count/steps), 90-100 (text only checked for leading zeros/headings/leftover
  TeX), 181-196 (coverage by number, not text), 208-224 (hard-coded pass fields).
- Description: the parser records only metadata and counts. It never compares exercise
  text, solution algebra, excerpts, statements or MathML to the book or any oracle.
- Evidence/repro: in a /tmp copy, keeping the style identical across pages, I applied all
  of the following: replaced a visible text token with JUNK; emptied a MathML body while
  keeping data-tex; replaced an original-excerpt body with FAKE ENGLISH; changed one PDF
  anchor to #page=1 (in range, wrong page); appended a stale <code>stale old program
  x=1</code> block; added @import url(https://evil.example/theme.css) and
  background-image:url(https://evil.example/bg.png) to every page's style. Then
  python3 tools/check_notes.py --extract-only exited 0, reporting 236 exercises, 146
  excerpts and mathml 7924 (the prior validation said 7926). No count expectation is
  enforced.
- Fix: either (a) weaken README/validation claims to "structure + code smoke test only",
  or (b) add a content verifier that extracts PDF text, normalizes it, and checks
  questions/quotes/statements, and pin expected counts in source_manifest.json.

### F-02 - Major - invalid-input checks accept crashes
- File:line: tools/check_notes.py:121-126 (command), 279-320 (invalid list),
  320-322 (only command(..., False)).
- Description: command(..., success=False) only requires returncode != 0 and absence of
  two sanitizer strings. It does not require the programs' graceful validation path
  (exit code 2 / validation message).
- Evidence/repro: check_notes.command([sys.executable, '-c', 'import os;os.abort()'], '',
  False) returned normally. A segfault, abort(), SIGFPE or uncaught Python exception in an
  invalid case is therefore counted as "invalid input rejected".
- Fix: in the invalid loop require returncode == 2 and optionally a validation marker on
  stderr; treat signals/sanitizer output as failures.

### F-03 - Major - browser acceptance claim outruns current evidence
- File:line: notes/README.md:46 (claims 1800/1440/1024/390 and 36 layouts),
  notes/statements_review.json:7164 (current layout_variants 18, widths 1800/390),
  notes/statements_review.json:7236 (historical layout_variants 36),
  notes/code_deployment_review.json:566-571 (final 18 variants, widths 1800/390).
- Description: final HTML was browser-checked at only two widths. The 36-layout records
  live in review_history[0] and describe the pre-code-extraction revision.
- Evidence/repro: all 36 historical html_sha256 values match 0/36 current pages; the
  current 18 layout hashes match 18/18. The README sentence claiming 36 layouts at four
  widths for the final pages is therefore misleading.
- Fix: rerun the browser harness on final pages at 1440 and 1024 (or correct the README),
  and point validation only at current-hash-bound records.

### F-04 - Major - release tarball is not deterministic
- File:line: deploy/build_release.py:122-126.
- Description: tarfile.open(archive, 'w:gz') writes the current time into the gzip header
  MTIME, so identical content produces different .tar.gz bytes.
- Evidence/repro: two builds in the same /tmp copy gave site.tar.gz hashes d28deaf4... and
  e6b83968...; the gzip MTIME decoded to the build time 2026-10-11T11:48:26Z. Archive
  hash claims are reproducible only for an existing build, not for a rebuild.
- Fix: wrap the tar in gzip.GzipFile(fileobj=..., mode='wb', mtime=0), use
  tarfile.open(fileobj=gz, mode='w'), and pin format/metadata (USTAR, mtime=0, uid/gid 0,
  sorted names).

### F-05 - Major - CSS/external dependencies bypass checker and release builder
- File:line: tools/check_notes.py:87-93 and 114 (style text collected but never parsed);
  deploy/build_release.py:36-52 (HTML resource attributes only), 84-101 (link scan).
- Description: @import and url() inside <style>/style attributes, <base href> and
  <meta http-equiv=refresh> are not scanned. External CSS can be packaged into a
  supposedly offline release.
- Evidence/repro: the F-01 page with @import url(https://evil.example/theme.css) passed
  check_notes --extract-only. python3 deploy/build_release.py ... exited 0, printed
  "link_validation": "pass", and the packaged chapter01 HTML still contained
  evil.example/theme.css, JUNK and stale old program.
- Fix: parse CSS text (including @import, url(), image-set()), style attributes, <base>
  and meta refresh; validate local targets against blobs; reject or allowlist external
  dependencies explicitly.

### F-06 - Major - sync_code silently tolerates stale/extra code and wrong language tags
- File:line: tools/sync_code.py:12-13 (regex), 47-81 (replace/seen logic).
- Description: only <code> blocks whose id is in the expected binding are examined. An
  extra <code> block without id/data-language, or with a different id and a non-program
  data-language, is ignored. The data-language attribute is never compared with the
  binding. The regex also mis-parses > inside attribute values.
- Evidence/repro: the F-01 /tmp page contains <code>stale old program x=1</code>;
  python3 tools/sync_code.py exited 0 with "differences": []. A C block labelled
  data-language="python" would also be replaced with C without a sync_code error (the
  later compile check catches this case, but sync_code alone does not).
- Fix: parse all <code> elements, require every code block to belong to a binding, verify
  data-language, use an HTML parser rather than a regex, and make --write atomic.

### F-07 - Major - release leaks absolute local paths in review JSON
- File:line: deploy/build_release.py:75-83 (notes/*.json are packaged).
- Description: code_deployment_review.json and validation.json embed
  file:///ABSOLUTE/PATH/... and /ABSOLUTE/PATH/... paths; the archive ships them.
- Evidence/repro: scanning the published archive found the local home-directory path in
  notes/code_deployment_review.json (2 occurrences) and notes/validation.json (2).
- Fix: exclude review JSON from the public site or sanitize absolute paths before
  packaging (rewrite file:///... to relative/removed, drop machine-local screenshot paths).

### F-08 - Major - readable_numbers corrupts valid C hex-float literals
- File:line: tools/readable_numbers.py:31-38.
- Description: the C "lexer" is a chain of regexes that does not understand hexadecimal
  floating constants; it treats the .8 inside 0x1.8p3 as a leading-zero decimal.
- Evidence/repro: readable_code('double h=0x1.8p3;', 'c') -> 'double h=0x10.8p3;';
  readable_code('double r=0x.8p3;', 'c') -> 'double r=0x0.8p3;'. A future source with
  hex floats would be rejected/rewritten by check_notes. Current programs have none.
- Fix: recognize 0[xX] hex floats including p exponents as whole tokens, or stop mutating
  C and use a real tokenizer; signal change rather than rewriting when unsure.

### F-09 - Minor - readable_text rewrites .5 in URLs/paths
- File:line: tools/readable_numbers.py:7-11.
- Description: the negative lookbehind excludes only [A-Za-z0-9_.]; slash, colon or dash
  before .5 still triggers replacement.
- Evidence/repro: readable_text('http://a/.5') -> 'http://a/0.5'; version/path text in
  prose can be corrupted and check_notes would report an "omitted leading zero".
- Fix: skip replacement inside URL/path/version contexts, or restrict normalization to
  standalone numeric contexts.

### F-10 - Minor - close() tolerance hides small absolute errors
- File:line: tools/check_notes.py:127-131.
- Description: math.isclose(..., abs_tol=1e-8, rel_tol=1e-8) accepts up to 1e-8 absolute
  error, so expected exact zeros can be wrong by 1e-9 and expected 1e12 can be off by
  10,000.
- Evidence/repro: close([0.0], [1e-9], 'x') and close([1e12], [1e12+10000], 'x') both
  pass; close([1.0], [1.00000002], 'x') fails.
- Fix: use mode-specific tolerances tied to output precision, and assert exact zeros
  separately where probabilities/leakage near zero matter.

### F-11 - Minor - simulation checks are coarse fixed-seed smoke tests
- File:line: tools/check_notes.py:258-278; code/chapter02_poisson_processes/poisson.py,
  code/chapter03_renewal_processes/renewal.py,
  code/chapter04_continuous_time_markov_chains/ctmc.py,
  code/chapter05_martingales/stopping.py.
- Description: Poisson uses one seed and a 6-sigma + 5e-5 band; renewal/CTMC use +-0.01;
  stopping uses +-0.3 for a mean and +-0.01 for a probability. The report hard-codes
  simulation_runs: 4. No RNG quality, independence or multiple-seed test is performed.
- Evidence/repro: reading the four programs and the checks above; all use the fixed
  state 20261010 and 100,000 trials.
- Fix: label these as smoke tests; add multiple seeds, independent test statistics, and
  deterministic identities where possible.

### F-12 - Minor - HTML parser/CSS blind spots and false positives
- File:line: tools/check_notes.py:14-18 (tag allowlist), 60 (block-in-p list incomplete),
  73-82 (data-tex braces only), 90-100 (text regex), 114 (styles), 187 (only first style
  compared).
- Description: blockquote/details/aside/nav etc. inside <p> are not flagged; only the
  first style block per page is compared for equality; data-tex is never cross-checked
  against MathML; the text regex can flag prose containing a dollar pair; valid SVG tags
  outside the list (e.g. use/tspan) would be rejected.
- Evidence/repro: the F-01 page emptied a MathML body while keeping data-tex and still
  passed; re.search(r'\$[^$\n]+\$', 'price $5 to $10') matches, so such prose would be
  reported as an unconverted formula.
- Fix: use a real HTML/CSS validator or a larger tolerant allowlist; cross-check
  data-tex with MathML; replace the dollar heuristic with a TeX-context parser.

### F-13 - Minor - publish is not atomic
- File:line: deploy/build_release.py:119-143.
- Description: out.mkdir() appears first, then files are moved one by one from staging.
  A failure mid-loop leaves a partial release directory; there is no fsync/rename-complete
  barrier.
- Evidence/repro: code inspection; no rollback path exists.
- Fix: build in a temp directory and rename it to out atomically (os.replace on the same
  filesystem), or publish a completion marker last.

### F-14 - Minor - evidence timestamps are assembly times; raw evidence is not hash-pinned
- File:line: notes/validation.json (runtime_evidence), tmp/finalize_code_deploy.py.
- Description: validation.runtime_evidence.checked_at_utc is the JSON assembly time, not
  the run time. The referenced report.json/runtime log/browser-layouts.json are not listed
  with hashes, so their integrity is unbound.
- Evidence/repro: checked_at_utc = 2026-10-11T09:59:24Z, while tmp/notes-check/report.json
  currently has mtime 19:04 local (a later identical re-run) and
  tmp/code-deploy-runtime.txt has mtime 17:49 local; the report content still equals
  validation.program_checks.
- Fix: record run start/end wall-clock and a hash manifest of every referenced evidence
  artifact; treat report.json as an immutable, content-addressed artifact.

### F-15 - Minor - canonical per-block hashes are not reproducible from the delivered package
- File:line: notes/annotations_review.json (canonical_group_sha256/canonical_html_sha256),
  notes/readability_review.json (derivation_blocks/retained_proofs html_sha256),
  notes/review_manifest.json (body_additions html_sha256); canonicalization logic lives in
  tmp/finalize_annotations.py, tmp/finalize_readability.py, tmp/finalize_statements.py.
- Description: whole-file and browser/HTTP hashes are independently reproducible, but
  these block hashes depend on untracked tmp scripts, BeautifulSoup serialization and
  previous revisions.
- Evidence/repro: scanning all block hashes found no whole-file matches (expected), and the
  canonicalization code is not under tools/.
- Fix: publish the canonicalization scripts and inputs, or drop block-hash claims and
  bind only to reproducible whole-file hashes.

### F-16 - Minor - fixture provenance is incomplete; independence is not enforced
- File:line: tools/notes_cases.json; tmp/build_notes.py (sympy exact linear fixtures);
  tmp/readability_fixtures.py (22 exact-rational/path-enumeration fixtures).
- Description: 150 fixtures are correct and all 150 matched an independent recomputation
  (numpy LAPACK, statistics.NormalDist, independent tree recursion). But the generator for
  the 34 finance/bs fixtures is not preserved, and the JSON oracle carries no provenance
  metadata or fixture hash.
- Evidence/repro: our independent validator checked all 150 with max relative error below
  1e-9 and printed zero mismatches; the copied generators show exact arithmetic for
  linear/finance additions. A future edit could still replace expected values with program
  output and the checker would not notice.
- Fix: store the fixture generator under tools/ (or an appendix script) and add a
  provenance digest/label to notes_cases.json.

### F-17 - Minor - print and deep-link verification gaps
- File:line: notes/chapter01_markov_chains.html style @media print (approx. style lines
  133/171 in the single-line style block); tmp/code_deploy_browser.js:14 (opens all
  details), 19-21 (asserts openExercises == exercises), 25-29 (only two hash screenshots).
- Description: print CSS hides sidebars but never opens closed <details>, so exercise
  solutions/notes may be omitted from print/PDF unless the reader manually opened them.
  The browser script opens every .exercise before asserting the open count, so the
  deep-link auto-open feature is not programmatically verified; only two hash-navigation
  screenshots exist.
- Evidence/repro: static inspection of the print rules and of the browser script.
- Fix: add a beforeprint hook or print-specific expansion for key details; in the browser
  suite assert a target <details> is open before manually opening anything, and test a
  sample of hash links with JS and without JS.

### F-18 - Nit - unchecked indexing produces tracebacks instead of clean failures
- File:line: tools/check_notes.py:182 (chapter page lookup), 187 (styles[0]),
  279 (recordings[name]).
- Description: a missing chapter page raises StopIteration; a page without a style block
  raises IndexError; a missing recorded JSON raises KeyError. These are not currently
  triggered, but they obscure the real diagnosis.
- Fix: explicit existence checks with AssertionError messages.

## 4. Verified-correct highlights

- All 147 whole-file bytes/sha256 records across the 7 review JSONs match the current
  files exactly (annotations 15, code_deployment 41, readability 10, review_manifest 19,
  statements 14, validation 48).
- The independent fixture recomputation matched all 150/150 cases: 105 linear,
  30 finance, 15 Black-Scholes, max relative error < 1e-9. 22 fixtures have an exact
  rational/path-enumeration generator; the linear CASES in tmp/build_notes.py use sympy
  exact inverses.
- Counts match the claims: 9 pages, 236 exercises, 1028 solution steps, 66 annotation
  groups, 132 cards, 150 formal statements, 115 theorems/lemmas, 2 definitions, 146
  excerpt blocks, 4 preface paragraphs, 3 axioms, 7926 MathML elements, 7 figures,
  7 program pairs / 14 standalone source files.
- --extract-only passes on a clean /tmp copy and its report matches
  validation.program_checks; tmp/notes-check/report.json now equals
  validation.program_checks, and tmp/code-deploy-runtime.txt ends with OVERALL PASS.
  (The full sanitizer run was not independently re-run by this auditor.)
- Current browser evidence is internally consistent: tmp/code-deploy-http/browser-layouts.json
  equals code_deployment_review.browser_review.layouts field-for-field; 18/18
  html_sha256 values match current pages; 6/6 current screenshots match bytes+sha256;
  raw HTTP responses match the 24 review responses and current file hashes; PDF range
  returned 206 bytes 0-4095/2579008 with %PDF-1.4.
- CSP claim verified: the two inline scripts are shared by all 9 pages, and their
  base64 SHA-256 hashes in deploy/releases/20261011T180044/nginx-static.inc match the
  scripts currently embedded in the pages.
- The published release is internally consistent: release.json records 41 files and
  7,456,490 bytes; SHA256SUMS agrees with all 41 archive members; archive.sha256 and
  release.json archive_sha256 match the real site.tar.gz
  (130285b75110ebc21d48fe346ec4ddfab3dbcc90ff80d6fc921789fa1ef11f27); deploy acceptance
  report matches archive bytes/sha and 82 root/subpath responses.
- PDF/PDF-page sampling: pdfinfo reports 282 pages; pdftotext confirms Theorem 1.1 on
  PDF page 20, Theorem 1.2 on page 22 and the Chapter 1 exercises on page 87 / printed
  page 78, matching source_manifest.json samples. The checker itself only validates the
  range, not the mapping.
- HTML/CSS static quality: lang=zh-CN, viewport meta, skip link, main landmark,
  summary/details controls, aria-labelled TOC/rail, role/title/aria-label on every SVG
  figure, 17px/1.9 base type, 860px measure, 240px TOC, 3-column layout at >=1440px
  (240/860/280), 1099px/640px collapse rules, native MathML with no JS typesetting,
  overflow wrappers for pre/table/figure, contrast ratios 6.3-7.8:1 for text, and no
  external resource references in the current pages (MathML namespace and one DOI
  hyperlink only).
- --release-id and --web-root validation reject malformed values tested (bad timestamp,
  relative path, /.., semicolons); the accepted path is restricted to an Nginx-safe
  character set.

## 5. Method and limits of this audit

- All experiments were performed on copies under /tmp; the tracked workspace was not
  modified. The full sanitizer run was not re-run because code compilation was in
  progress elsewhere; the recorded full-run artifacts and their agreement with
  validation.json were checked instead.
- The independent fixture validator is /tmp/fix_audit.py: it uses numpy linear solves,
  statistics.NormalDist and a separate path-recursive finance tree, not the C/Python
  programs.
- No supported headless-browser driver (puppeteer/playwright module) was installed. A
  Playwright browser cache exists but no driver API, so HTML/CSS/UX conclusions are from
  static inspection plus the recorded raw browser evidence; the final pages were not
  independently re-rendered at 1440/1024.
- The F-01/F-05/F-06 bad-content repro is in /tmp/earaudit_bad2 (cleaned after the audit);
  the exact sequence is described in F-01. The release-determinism test used
  /tmp/earaudit with two clean builds of release id 20990101T000000.

## 6. One-line summary

The verifier is good at proving internal consistency and running the numeric programs, and
the current file hashes/counts/fixtures are correct; it is not a content verifier. The
biggest risks are (1) structural/content checks that pass on junk, (2) final-page browser
coverage being only two viewports while the README claims four/36 layouts, (3)
non-deterministic and non-atomic release building, and (4) CSS/external-dependency blind
spots that can package non-offline pages with a green link_validation result.
