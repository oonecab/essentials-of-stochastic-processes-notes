# Audit report: preface and Chapters 1-3

Scope: `notes/preface.html`, `notes/chapter01_markov_chains.html`,
`notes/chapter02_poisson_processes.html`, `notes/chapter03_renewal_processes.html`.

Source of truth: Durrett, *Essentials of Stochastic Processes*, 3rd ed. (2016),
282-page PDF; printed page = PDF page - 9 for these chapters.

Method: extracted every `data-source-number` statement, exercise question, and
`ol.solution-steps` solution from the HTML; compared against the corresponding
PDF pages line by line; independently recomputed stationary distributions,
absorption probabilities/times, matrix powers, hitting probabilities, and all
numerical answers with Python/SymPy. The repository's own `*_review.json` and
`validation.json` were treated as claims, not evidence.

## Page verdicts

| Page | Score | Justification |
|---|---:|---|
| `preface.html` | 9.0 | All four English paragraphs match PDF pages 5-6 verbatim; the Chinese translation is accurate; all five preface sections have two substantive annotations. No math or translation error found. |
| `chapter01_markov_chains.html` | 7.5 | Very complete: 31 numbered theorems/lemmas (1.1-1.31), both numbered definitions (1.1, 1.2), 56 numbered examples, and all 77 exercises are present in order. Several genuine book typos are correctly flagged (1.16, 1.23, 1.46, Example 4.4 mislabel). However, exercise 1.11(b) is answered incorrectly and self-contradictorily. |
| `chapter02_poisson_processes.html` | 9.0 | All 16 numbered results (2.1-2.16), 14 examples, and 61 exercises present; every numerical solution re-derived matched. The note correctly flags book errors in Theorem 2.4, Theorem 2.15, Example 2.12, and Example 2.14. Only wording/citation nits. |
| `chapter03_renewal_processes.html` | 9.0 | All 11 numbered results (3.1-3.11), 10 examples, and 24 exercises present; all exercise solutions re-derived matched. The note's correction of the book's Theorem 3.7 (service-start chain vs. real-time idle fraction) is valid and was confirmed by simulation. Minor example-label issue. |

## Findings

### F1 (Major) Exercise 1.11(b): detailed balance is claimed to fail, but it holds

- Location: `notes/chapter01_markov_chains.html:1061` (`<details id="ex-1-11">`,
  summary "1.11 - stationary but not detailed balance"); decisive step at line 1070.
- PDF page: 89 (printed 80), Exercise 1.11.
- Description: For
  `P = [[1/5,2/5,2/5],[1/10,3/5,3/10],[1/5,3/5,1/5]]`
  the note correctly obtains `pi = (1/7,4/7,2/7)`, then writes
  "`pi_1 p_12 = 2/35`, `pi_2 p_21 = 2/35`, the two are different" and concludes
  "therefore the chain does not satisfy detailed balance". The title also asserts
  it is "stationary but not detailed balance".
- Evidence/repro: SymPy check of all ordered pairs:
  `pi_1 p_12 = 2/35 = pi_2 p_21`;
  `pi_1 p_13 = 2/35 = pi_3 p_31`;
  `pi_2 p_23 = 6/35 = pi_3 p_32`.
  Hence `pi_i p_ij = pi_j p_ji` for every pair: the chain is reversible. The
  note's own step [6] already prints both sides as `2/35`, so the "different"
  claim is directly self-contradictory.
- Impact: A whole sub-part is answered with the opposite conclusion, and the
  reason given contradicts the arithmetic shown one sentence earlier.
- Suggested fix: Rename the summary to "stationary and detailed balance";
  replace step [6] with the three equalities above; conclude that the chain is
  reversible. If an irreversible example is wanted, use a different matrix.

### F2 (Minor) Book "Chapter Summary" sections are renamed and not summarized

- Locations: `notes/chapter01_markov_chains.html` section `#s112` (line 792,
  title "1.12 solving routes for this chapter"); `notes/chapter02_poisson_processes.html`
  section `#s25` (line 478, title "2.5 choosing conditions and units");
  `notes/chapter03_renewal_processes.html` section `#s34` (line 414, title
  "3.4 numerator and denominator").
- PDF pages: Ch1 1.12 Chapter Summary (printed 46-47 / PDF 55-56); Ch2 2.5
  Chapter Summary (printed 114-115 / PDF 123-124); Ch3 3.4 Chapter Summary
  (printed 140-141 / PDF 149-150).
- Description: The book's section number 1.12/2.5/3.4 is the Chapter Summary,
  a formula recap. The note replaces each with study advice. The numbered
  statements and the per-page index cover most of the content, but the book's
  summary structure/title is not preserved.
- Suggested fix: Either keep the summary formulas as an extra block or add a
  note saying the section has been replaced by a study route; at minimum do not
  present the new title as if it were the book's 1.12/2.5/3.4.

### F3 (Minor) Example 3.6 label attached to an unnumbered counterexample

- Location: `notes/chapter03_renewal_processes.html`, body derivation
  `#derive-c3-queue-identities` (line 355), sentence beginning "Example 3.6:
  interarrival U(2,3), constant service one ...".
- PDF page: 144 (printed 135), the PASTA counterexample; the book's numbered
  Example 3.6 is "Waiting Time in the Queue" on PDF page 141.
- Description: The note attributes the U(2,3) counterexample to "Example 3.6".
  The book's Example 3.6 is a different (numbered) example; the U(2,3) example
  is unnumbered. The arithmetic correction in the same sentence (busy fraction
  1/2.5 = 0.4, vs. the book's 1/(1+2.5) = 2/7) is correct.
- Suggested fix: Relabel as "PASTA counterexample (unnumbered)" or "the
  GI/G/1 example on printed p. 135".

### F4 (Minor) Definition of Poisson process quotes the construction, not the book's definition

- Location: `notes/chapter02_poisson_processes.html:248`
  (`<details id="definition-poisson-process">`).
- PDF page: the book's actual definition is on printed 101 / PDF 110; the
  quoted construction is on printed 102 / PDF 111.
- Description: The English "original" blockquote gives the construction
  `N(s)=max{n:T_n<=s}` with i.i.d. exponential interarrivals. The book's
  definition is the (i) N(0)=0, (ii) Poisson increments, (iii) independent
  increments statement. The Chinese statement covers the definition, and the
  quote is verbatim from the construction, so this is a citation/attribution
  issue rather than a mathematical error. The page citation omits PDF 110.
- Suggested fix: In the English blockquote use the book's definition sentence
  (or mark the quote as "construction" and cite PDF 110-112).

### F5 (Nit) Exercise 2.54 wording: "difference of the two exponents"

- Location: `notes/chapter02_poisson_processes.html:804` (solution step [3] of
  Exercise 2.54).
- PDF page: 133 (printed 124).
- Description: After deriving
  `Var(S_t) = S_0^2 [ e^{lambda t(m^2+sigma^2-1)} - e^{2 lambda t(m-1)} ]`,
  the note says the two exponents differ by `lambda t[(m-1)^2+sigma^2]`.
  That is the difference of the *exponents* in the bracket; the *values*
  differ by a factor `exp(lambda t[(m-1)^2+sigma^2])-1`. The variance formula
  itself is correct.
- Suggested fix: Reword to "The two exponents differ by ...; hence the bracket
  is nonnegative."

### F6 (Nit) Exercise 2.7(c) branch description is garbled

- Location: `notes/chapter02_poisson_processes.html:772` (solution step [4] of
  Exercise 2.7).
- PDF page: 126 (printed 117).
- Description: The final probabilities (Anne 1/9, Betty 4/9, Carol 4/9) are
  correct, but the sentence "Anne last requires Betty to finish first
  (probability 1/3); then Carol on the fast teller finishes before Anne
  (probability 1/3)" is not the actual configuration: if Betty finishes first,
  Carol goes to the slow teller and Anne remains on the fast teller, so Anne
  is last iff Carol's slow service finishes before Anne's fast residual
  (`P = 1/3`). The number is right; the explanation is misleading.
- Suggested fix: Rewrite the two branches explicitly with the teller each
  customer uses.

### F7 (Nit) Statement order inside section 1.3 differs from the book

- Location: `notes/chapter01_markov_chains.html`, section `#s13`; the
  statement index lists `definition-stopping-return`, `definition-communication`
  (Definition 1.1), then `theorem-1-2`, before `lemma-1-3` etc.
- PDF page: 25 (printed 16); the book's order is Theorem 1.2, Lemma 1.3,
  Definition 1.1, Lemma 1.4, ...
- Description: All numbers are correct, but in-page order (and index order)
  puts the stopping-time and communication definitions before the strong
  Markov property theorem, unlike the book. This is a deliberate pedagogical
  reordering, but it means the page order does not match the source.
- Suggested fix: Add a one-line note "definitions moved before Theorem 1.2 for
  reading order" or reorder to match the book.

## Verified-correct highlights

The following were independently recomputed and found correct; several are
places where the note correctly contradicts the printed book.

- Theorem 3.7 (PDF 143, printed 134): The book writes `E_0 T_0 = mu/(mu-lambda)`
  and identifies the stationary probability of the service-start chain with the
  real-time idle fraction `1-rho`. The note adds the correction
  `pi_0 = (1-rho)/a_0`, `E_0 T_0 = a_0/(1-rho)`. For M/M/1 with `lambda=1`,
  `mu=2` (`rho=1/2`, `a_0=2/3`) the corrected values are `pi_0=3/4`,
  `E_0 T_0=4/3`; a direct simulation of `X_{n+1}=(X_n+A_n-1)^+` over 5e6 steps
  gives `pi_0 = 0.75009`. The book's `1/2` and `2` are wrong; the note is right.
- Theorem 1.16 (PDF 48, printed 39): The note adds the infinite-state caveat.
  This is necessary: e.g. simple symmetric random walk on Z satisfies the cycle
  condition but has no stationary probability distribution; the constructed
  measure is not normalizable.
- Theorem 1.23 (PDF 53/61, printed 44/52): The book prints "Theorem 1.23
  (Convergence Theorem)" on printed p. 52, duplicating the number of the
  Cesaro-average result on printed p. 44. The note correctly explains that the
  p. 52 statement is the convergence theorem (Theorem 1.19).
- Theorem 1.28 (PDF 64, printed 55): The note correctly unifies the book's
  lowercase `V_a, V_b` with the sets `A, B`.
- Exercise 1.9(c) (PDF 88, printed 79): row 2 `(0.2,0.4,0.2)` sums to 0.8;
  the note proves no stationary distribution exists and gives the conditional
  `(1,2,2)/5` only under the explicit repair `0.4 -> 0.6`. Correct handling.
- Exercise 2.58 (PDF 133, printed 124): the book's geometric mass
  `P(N=n)=(1-p)^{n-1}` sums to `1/p`; the note flags the missing factor `p` and
  derives `T ~ Exp(lambda p)`. Correct.
- Example 2.12 (PDF 122, printed 113): the book computes `140/512 = 0.273`;
  the correct sum is `1+9+36+84 = 130`, i.e. `65/256 = 0.253906`. The note
  flags and corrects this.
- Example 2.14 (PDF 124, printed 115): the book prints `0.4069` for "four cars
  before two trucks"; the correct value is `112/243 = 0.4609`. The book also
  prints variance `55`, but the correct compound-Poisson variance is
  `10*5.5+5*1 = 60` (sd `sqrt(60)`). The note corrects both.
- Theorem 2.15 proof (PDF 122, printed 113): the book conditions on `N(t)=4`
  while computing the density for 3 arrivals; the note flags `N(t)=3`.
- Example 3.3 (PDF 137, printed 128): the book's derivative denominator uses
  `(T-0.1T^2)^2` although `E t_i = T-0.05T^2`; the note flags the `0.1T^2`
  typo. The optimum `T = (-1+sqrt(1.6))/0.03 = 8.8304` is also reproduced.
- Example 3.6 / PASTA counterexample (PDF 144, printed 135): for interarrivals
  U(2,3) and constant service 1, the book says busy fraction
  `1/(1+2.5)=2/7`; the correct value is `1/2.5=0.4`. The note is right.
- Example 1.46 (PDF 69, printed 60): the book's exit-probability vector has
  `h_3=3/5`; solving `h_3=0.5h_3+0.2` gives `h_3=2/5`, consistent with the
  book's own limit matrix. The note flags this.
- Example 1.28 (PDF 40-41, printed 31-32): weights `1,10,45,60`, sum `116`;
  reproduced exactly.
- Example 1.30 (knight walk, PDF 42-43): degrees `2,3,4,6,8` with counts
  `4,8,20,16,16`, total degree `336`; corner return mean `168`. Reproduced.
- Example 1.18, 1.20, 1.39, 1.51, 1.52, 1.53 and Ch. 2-3 worked examples:
  checked representative numerics (e.g. `(22,16,9)/47`; `(1/2,3/16,3/16,1/8)`;
  coupon-collector die `6 H_6 = 14.7`; `(g_1..g_5)=(82.2,81,79.2,75.6,64.8)`;
  car-cost `8.8304`; `W_Q=37`, `L=7`; `a_0=2/3` M/M/1 case).

## Measured coverage and checks

- Numbered results: Ch1 31/31 theorem+lemma, plus Definition 1.1 and 1.2;
  Ch2 16/16; Ch3 11/11. Total 58/58 numbered results and 2/2 numbered
  definitions. All numbers and kinds match `notes/source_manifest.json` and the
  PDF headings.
- Exercises: Ch1 1.1-1.77 (77), Ch2 2.1-2.61 (61), Ch3 3.1-3.24 (24);
  162/162 present, in order, with all sub-parts. Every exercise has at least
  three top-level solution steps (counts: Ch1 3-5, Ch2 3-4, Ch3 3-4).
- Independent recomputation: all 24 Ch3 exercises and all 61 Ch2 exercises
  were re-derived/checked; about 55 of the 77 Ch1 exercises were independently
  recomputed with SymPy (stationary distributions, absorption probabilities,
  absorption times, matrix powers, hitting probabilities, numerical answers).
  The only wrong exercise answer found is F1 (1.11b).
- Numbered examples: Ch1 56 (1.1-1.56), Ch2 14 (2.1-2.14), Ch3 10 (3.1-3.10);
  all 80 are discussed in the matching section/derivation blocks.
- Annotations: two annotation cards per content section (verified structurally
  in `details.reading-notes` for every section of all four pages).
- English excerpts: all 71 statement/exercise quotations were matched against
  the PDF; 18 were compared word-by-word (including the four preface
  paragraphs). No misquote was found; several quotes preserve the book's own
  grammatical slips (e.g. "If Nn(y) be the number of visits").
- Links: no broken internal `#anchor` in any of the four pages; every exercise
  `#page=N` PDF link matches the manifest page for that exercise.
- Fidelity of corrections: the note's two most consequential corrections
  (Theorem 1.16 infinite-state caveat and Theorem 3.7 service-start chain) were
  re-derived from first principles; both are valid.
