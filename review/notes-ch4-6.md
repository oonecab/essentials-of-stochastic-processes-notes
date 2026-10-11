# Quality audit: Chapters 4-6 and Appendix A (notes-ch4-6)

Scope: notes/chapter04_continuous_time_markov_chains.html,
notes/chapter05_martingales.html, notes/chapter06_mathematical_finance.html,
notes/appendix_a_probability_review.html, notes/book_overview.html.
Source of truth: Essentials of Stochastic Processes (Richard Durrett) (z-library.sk, 1lib.sk, z-lib.sk).pdf.
Method: page-by-page pdftotext -layout/-raw comparison; extraction of every
details.source-statement and details.exercise from the HTML; independent recomputation
with exact fractions, linear algebra, option trees, Black-Scholes and CRR in Python;
full scans of theorem/exercise numbering, sub-parts and page citations. Repo JSONs were
used only to dispute claims, never as evidence. No file other than this report was modified.

## Per-page verdict (0-10)

| Page | Score | Verdict |
|---|---|---|
| book_overview.html | 9 | Accurate map, exercise counts, page-offset explanation (omitted printed pages 146/268 shift the offset) and notation table. Minor: it does not show the book's own section titles, so the reader cannot map by title alone. |
| chapter04_...html | 8.5 | Complete coverage and excellent book-typo annotations (Kimura, HKY, Examples 4.19/4.21). But the worked Example 4.29 traffic solution is wrong (inherits the book's 11/7), and several birth-death exercise solutions are boilerplate-heavy. |
| chapter05_...html | 9.5 | Theorem hypotheses, stopping/integrability conditions, Wald and negative-drift sign annotations are all correct; all 10 exercise answers were independently recomputed and pass. Only improvement: state the optional-stopping sufficient conditions even earlier in the prose. |
| chapter06_...html | 9 | Binomial trees, American exercise, Black-Scholes and CRR numbers are almost all correct, with good book-typo notes. Two defects: Exercise 6.20's 64/25=2.208 is wrong, and Example 6.4's note falsely claims the book printed 144.72. |
| appendix_A_...html | 9 | A.1-A.4 numbers match the book, the three probability axioms are given in the standard nonnegativity/normalization/countable-additivity form with the upper bound correctly derived, and Theorems A.1-A.12 are covered with proper extra hypotheses. Minor: a few "English original" blocks are not definition sentences, and cross-links are sparse. |

## Findings

### F1 (Major) Example 4.29 two-station traffic equations solved incorrectly
- File / anchor: notes/chapter04_continuous_time_markov_chains.html, section 4.6, id=body-review-s46, line 562.
- PDF page: p194 (printed 186), Example 4.29.
- Description: The notes write "solve alpha1=1+alpha2/4, alpha2=2+alpha1/2, giving
  (11/7,20/7); service rates (4,7/2) give rho=(11/28,40/49)". Solving the two displayed
  equations gives alpha2=20/7 and then alpha1=1+5/7=12/7, not 11/7; rho1 should be
  (12/7)/4=3/7, not 11/28. The book itself prints r1=1+20/28=11/7 on p194 (but
  1+20/28=12/7), i.e. an arithmetic slip; the notes silently copy it instead of correcting it.
- Evidence / repro:
  python3 -c "from fractions import Fraction as F; print(F(1)+F(1,4)*F(20,7))"  ->  12/7
  Solving [[1,-1/4],[-1/2,1]] (r1,r2) = (1,2) gives (1.71428571, 2.85714286), i.e. (12/7, 20/7).
- Suggested fix: use alpha1=12/7, alpha2=20/7, rho=(3/7,40/49); if L/W are quoted,
  L1=3/4, L2=40/9, W=(187/36)/3=187/108. Add a note that the book's 11/7 is an arithmetic slip.

### F2 (Minor) Exercise 6.20 alternative answer decimal is wrong
- File / anchor: notes/chapter06_mathematical_finance.html, id=ex-6-20, line 791.
- PDF page: p258 (printed 250), Exercise 6.20.
- Description: The notes write "the ordinary American call price for the literal S payoff is
  64/25=2.208". 64/25=2.56. Independent backward induction for payoff (S_n-4)^+ gives
  HH=12.8, HT=TH=1.6, TT=0, H=0.4(12.8+1.6)=5.76, T=0.4(1.6+0)=0.64, V0=0.4(5.76+0.64)=2.56;
  the discounted terminal expectation is 5*(4/5)^3=64/25=2.56. Only the decimal is wrong.
- Evidence / repro: python3 -c "print(64/25)"  ->  2.56
- Suggested fix: change 2.208 to 2.56 in both the inline formula and the text.

### F3 (Minor) Example 6.4 note falsely claims the book printed "144.72"
- File / anchor: notes/chapter06_mathematical_finance.html, section 6.3, id=derive-c6-parity-knockout, line 326.
- PDF page: p243 (printed 235), Example 6.4 tree.
- Description: The notes say "the root numerator is also misprinted as 144.72". The PDF
  prints 414.72/49 in both the call and put trees; 414.72/49 = 10368/1225, which is exactly
  the correct value for the tree's S0=36, and the notes themselves use 414.72/49 just after.
  The real inconsistency is only the text S0=32 versus the tree root S0=36.
- Evidence / repro: pdftotext -f 243 -l 243 -raw <pdf> - | grep -n "144\|414"  -> two
  occurrences of 414.72 and none of 144.72; 10368/1225 = 8.463673 = 414.72/49.
- Suggested fix: delete the 144.72 claim; state instead that the tree's 414.72/49 is
  internally consistent with the figure's S0=36 and only conflicts with the prose S0=32.

### F4 (Minor) Definition ctmc omits the "q_ij limit exists" hypothesis
- File / anchor: notes/chapter04_continuous_time_markov_chains.html, section 4.1, id=definition-ctmc, line 192.
- PDF page: p156 (printed 148), around (4.1).
- Description: The notes define q_ij = lim_{h->0} p_h(i,j)/h directly. The book explicitly
  conditions it: "If this limit exists (and it will in all the cases we consider) we will
  call q(i,j) the jump rate". The notes add finite total rate and non-explosion elsewhere,
  but the definition sentence itself drops the existence hypothesis, which is not automatic
  for a general continuous-time chain.
- Evidence / repro: PDF p156 raw text: "q.i; j/ D lim ... If this limit exists (and it will
  in all the cases we consider) we will call q.i; j/ the jump rate."
- Suggested fix: add "in the cases studied here the limit is assumed to exist; a general model
  must include existence as an assumption".

### F5 (Minor) Chapter 4 section numbers/titles do not preserve the book's 4.7/4.8
- File / anchor: notes/chapter04_continuous_time_markov_chains.html, line 567 (heading
  "4.7 ..."), line 604 (exercise section "39 exercises"); chapter05 line 533; chapter06 line 671.
- PDF page: book 4.7 Chapter Summary (p198) and 4.8 Exercises (p200); 5.5 Exercises (p228);
  6.7 Exercises (p255).
- Description: The notes replace the book's section titles with descriptive Chinese headings
  (e.g. book 4.1 Definitions and Examples -> "generator matrix...", book 6.3 Concrete Examples
  -> "path-dependent options..."), repurpose the book's 4.7 (Chapter Summary) as a study
  section, and do not label the exercise sections 4.8/5.5/6.7. Content is present, but a
  reader cross-referencing the book's numbering is misled.
- Evidence / repro: book section headings from pdftotext pp. 155/160/170/178/184/191/198/200,
  209/212/215/219/228, 231/235/240/245/249/253/255.
- Suggested fix: show the original English section title/number next to the descriptive one,
  and label the exercise sections 4.8/5.5/6.7.

### F6 (Minor) Some exercise solutions are boilerplate-heavy, inflating step counts
- File / anchor: chapter04...html exercise section, about 11 of 39 exercises.
- Description: Birth-death exercises share near-verbatim steps ("build a birth-death state
  from total count/good components", "solve pairwise detailed balance for weights"), and
  matrix exercises share "fix the state order and check the generator", "write balance plus
  normalization", "row-reduce the augmented matrix", "read off the distribution and check".
  Each still contains the specific matrix and result, but 2-4 of the 3-6 steps are generic,
  which weakens the claimed "real steps" requirement.
- Evidence / repro: counts over the exercise details blocks: phrase 1 = 11, phrase 2 = 11,
  matrix-template phrases = 7 each.
- Suggested fix: collapse the generic template into one modeling step and replace the rest
  with exercise-specific conditions, coefficients, elimination and semantic checks.

### F7 (Nit) A few "English original" blocks are not the corresponding definition sentence
- File / anchor: definition-ctmc (chapter04 line 192), definition-binomial (chapter06 line 233),
  definition-market (chapter06 line 192), definition-a.s.-convergence (appendix line 424).
- Description: These excerpts quote a nearby transitional sentence (e.g. "To warm up...",
  "The conditions in (6.1) imply 0<p^*<1.", "The main question to be considered here is...")
  rather than the definition itself. The sentences are faithful, but cannot be used to verify
  the labelled definition.
- Suggested fix: quote the actual definitional sentence, or rename the field to "related original text".

### F8 (Nit) Appendix cross-links are sparse
- File / anchor: chapter04/05/06...html link only to appendix #axiom-probability and
  #definition-conditional-probability; the appendix mentions "Lemma 5.2" / "Exercise 2.55" without links.
- Description: Chapter 5 uses conditional Jensen (Appendix A.9) and dominated convergence
  (A.12); Chapters 4 and 6 use variance/moments (A.3-A.8); none of these are linked. The
  cross-link design exists but covers only two anchors.
- Suggested fix: link Appendix A.9/A.12 back to #lemma-5-2/#theorem-5-11, and link the
  chapters' uses of variance/Jensen/DCT to #theorem-A-5/#theorem-A-9/#theorem-A-12.

## Verified-correct highlights (independently recomputed)

1. Coverage and numbering: all 57 numbered results in scope (chapter 4 = 18, chapter 5 = 17,
   chapter 6 = 10, Appendix A = 12) have a details.source-statement whose data-source-number
   matches source_manifest.json. The 5.1 -> 5.6 gap in Chapter 5 is the real book state (there
   is no 5.2-5.5), and the notes keep the book numbering and annotate it rather than inventing results.
2. Exercise coverage/order: 74/74 exercises (chapter 4 = 39, chapter 5 = 10, chapter 6 = 25)
   appear in exactly manifest order; every sub-part (a),(b),... is answered; every exercise has
   an ol.solution-steps with at least 3 steps (range 3-17).
3. Exercise numbers: I independently recomputed the key constants of all 74 exercises with exact
   fractions / linear algebra and found no wrong main answer. Examples: 4.1 pi=(1/2,1/4,1/4) and
   9 trips/year; 4.24 pi=(8,16,24,24,9)/81 and W=43/114; 4.31 P1(T0<T4)=15/47; 5.5
   P_i(ruin)=(sqrt2-1)^i; 5.8 Var=4pqx/(q-p)^3; 6.6 V0=288/5; 6.16 American put 117/25 and
   call 999/125; 6.19 lookback 488/125. (F1/F2 concern a worked example and an alternative value,
   not the main exercise answers.)
4. Financial content: binomial trees/replication (6.6-6.19), American node comparison, put-call
   parity, Black-Scholes (6.22-6.25) and the CRR convergence table all match independent
   computation. The CRR 16..512 sequence 10.32665105 -> 10.44667883 converges to BS 10.45058357
   exactly as tabulated; 6.23-6.25 d1,d2,Phi,C,P reproduce to 9 digits.
5. Book-typo annotations: about 20 spot-checked claims, all correct except F3. Verified:
   Kimura's extra factor in 2*beta*2*p3; HKY matrix swapping target T->G and G->C; Example 4.19
   c=2/1480; Example 4.21 63/60 and all-35/60; Wald's |EX1| that should be E|X1|; Lemma 5.15
   epsilon sign; Lemma 5.16 missing -epsilon and x/epsilon; Example 5.14 boundary-label swap;
   Exercise 5.6 strict-boundary inconsistency; Example 6.1 rounded 1945; Example 6.2 extra
   payoff 2; Example 6.3 inconsistent tree; Example 6.4 prose S0=32 vs tree S0=36; Example 6.6
   2.874 vs 2.784; Example 6.7 54+60 vs 54+6; Appendix generating-function exponent x^(k-1)
   that should be x^(k-m).
6. Appendix A: A.1 Probabilities, Independence; A.2 Random Variables, Distributions; A.3 Expected
   Value, Moments; A.4 Integration to the Limit match the book's four sections. The three axioms
   are given as nonnegativity, normalization and countable additivity (equivalent to the book's
   0<=P(A)<=1 + P(Omega)=1 + additivity), and 0<=P(A)<=1 is correctly derived. Theorems A.1-A.12
   are all present with the necessary integrability additions.
7. Page citations: the notes use printed = PDF - 8 for chapters 4-6 and Appendix A, matching the
   PDF page headers (Example 4.29 printed 186 = PDF 194; Appendix A.4 printed 267 = PDF 275), and
   book_overview.html explains why the offset changes from -9 to -8 after omitted printed page 146.
   Note: the task brief's "Chapter 4 printed 147 = PDF 156" is off by one; printed 147 = PDF 155,
   and the notes/manifest page arithmetic is the correct one.

## Measured coverage statistics

- Numbered theorems+lemmas: 57/57 covered with matching numbers (ch4 18/18, ch5 17/17, ch6 10/10,
  Appendix A 12/12). Numbered definitions in scope: 0 (the book's only two numbered definitions,
  1.1 and 1.2, are in Chapter 1); 6 unnumbered definition/principle blocks also present.
- Exercises: 74/74, exact manifest order (ch4 39/39, ch5 10/10, ch6 25/25), all sub-parts present.
- Solution steps: 74/74 have ol.solution-steps; minimum 3 steps, median about 5.
- English excerpts: 57/57 numbered results have an English block; spot checks show the great
  majority are verbatim/near-verbatim, with 4-5 related-prose exceptions (F7).
- Page citations: 50+ sampled theorem/exercise citations all match the PDF page headers.
- Book-typo/annotation claims: about 20 checked; 19 correct, 1 false (F3).
