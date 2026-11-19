# Decisions

Choices that are expensive to reverse, and the reasons. Newest first. Anything here that conflicts with `spec.md` is a bug in one of them; record it rather than editing quietly.

---

## 2026-11-19 — Disposition of cross-artifact analysis findings after Phase 8

**Analysis** (`/speckit.analyze`, read-only): no CRITICAL or HIGH findings; all 21 FRs and 9 SCs have task coverage; constitution Principles II, V, VI, and VII pass.

- research.md's resolved-clarifications summary still says "omit video row if unset". It is a stale one-line summary; the detailed decision in the same file, FR-017/FR-018, and contracts/html-output.md all require literal substitution with no renderer-side omission. Disposition: superseded by the 2026-11-19 fragment decision below; no implementation change needed.
- contracts/cli.md's I/O boundary list names the config read but not the top-fragment read. FR-018/FR-021 and contracts/html-output.md already define that boundary and its error path, so the CLI contract line is an incomplete inventory, not a conflicting requirement. Disposition: covered by the fragment decision below.
- The 2026-11-17 decision "Link titles live in config.toml" says the citation and explanation stay fixed in source. The 2026-11-19 fragment decision below explicitly supersedes that sentence; retained as history, not an active requirement.

## 2026-11-19 — The owner-authored header lives in an HTML fragment, not Python constants or config

**Decision.** The page-top H1, summary paragraph, "References" heading, and Article/Video label markup are supplied by the project owner in a source-controlled root file `top_fragment.html`, read at generation time (deterministic default `./top_fragment.html`). `config.toml` keeps exactly four unchanged keys — `paper_title`, `paper_url`, `video_title`, `video_url` — used only for link text and hrefs; `paper_title` is a plain string that may contain the author name and the article title. The separate fixed citation paragraph is removed: literal header content comes from the fragment, and only link titles/URLs come from config.

**Why.** The header is owner-authored prose and layout, not a formula (Principle V) or a shared number (Principle VI). Putting it in Python constants would entangle presentation with renderer code and turn a wording change into a code change; putting it in `config.toml` would blur that file's contract into holding markup, tempt styling into TOML strings, and force the four-key link schema to grow. An HTML fragment keeps the owner's markup verbatim and source-controlled, keeps config limited to link literals, and preserves determinism because the fragment is read once at generation time and never fetched or paraphrased at runtime. The renderer still computes nothing (Principle VII): Python constants remain the single source for numbers, and the fragment is the single source for page-top prose.

Alternatives considered: a hard-coded citation/explanation in the renderer (superseded by the 2026-11-19 clarification), new config keys for header text (rejected — mixes markup into the four-key link contract), and Python string constants (rejected — presentation belongs in the owner's source-controlled HTML, not implementation code).

## 2026-11-17 — Extended infinities are evaluated with phase, not treated as scope failures

**Decision.** The single evaluator carries finite complex values plus internal
infinities with a phase. It implements `log(0) = -inf`, `log(-inf) = +inf + i*pi`,
and `exp(-inf) = 0` while still reporting a non-finite root as `overflow`.
`EMLTree.log_argument_node_ids` records which `eml` nodes are `log` construction
roots so the evaluator can apply the extended-log identity at that node when
its argument is non-finite; the ordinary composition cannot express that case.
Source-derived zero right children remain node-level `undefined` failures via
`zero_check_node_ids`.

**Why.** The earlier 2026-11-16 decision to scope equivalence only to inputs
whose intermediates stay finite was too narrow: the author's own construction
chain relies on these identities, and exact-zero inputs such as `sin(0)` produced
either a spurious overflow or a wrong `0.5i` root without them. The phase-aware
model makes the corpus equivalent to Python's direct source evaluation while
keeping all failures explicit and node-attributed. This supersedes that earlier
scope decision; no second evaluator was introduced.

## 2026-11-17 — Source comparison fixes Python's negative-zero branch choice

**Decision.** `evaluate_source` preserves a `+0` imaginary component when
applying unary minus to a real value. The ported `const_i()` evaluates to
approximately `-i` under CPython's principal log with the compiler's leading
minus, while `const_pi()` evaluates to approximately `+pi`; the construction
table is not patched to force `+i`.

**Why.** Python turns `complex(1, 0)` into `-1-0j` under unary minus, which sends
`cmath.log(-1)` to `-i*pi` even though the specification names `+i*pi` and the
constructed `log(-1)` produces `+i*pi`. Preserving `+0j` makes source comparison
follow the specified branch without changing the authoritative formulas. The
trigonometric constructions still compare equal to the source because numerator
and denominator use the same signed `i`; `pi` remains positive.

## 2026-11-17 — Test dependency installed in `.venv`; generated artifact ignored

**Decision.** `requirements-dev.txt` still declares `pytest` as test-only, but
`python3 -m pip install -r requirements-dev.txt` fails on this machine with PEP
668 (`externally-managed-environment`). Tests are run with `.venv/bin/python -m
pytest -q`. `/out.html` is ignored because the CLI overwrites it on every run.

**Why.** The system Python is managed by the OS and must not be modified by a
project-level install. A local virtualenv preserves the runtime boundary and
makes the documented test command reproducible on this host.

## 2026-11-17 — `pytest` is test-only; runtime stays standard-library only

**Decision.** `requirements-dev.txt` declares `pytest` for the test suite. Runtime code imports no third-party package. Test directories need no `__init__.py` because pytest discovers subdirectories without them as long as test module basenames are unique — which they are here.

**Why.** Python 3.11 dropped `unittest` discovery's namespace-package support: `python3 -m unittest discover -s tests` silently runs zero tests when `tests/unit/` and `tests/integration/` lack `__init__.py`. Adding package markers just to satisfy a test runner is ceremony; using a runner that handles the layout directly is simpler. A dev-only dependency does not change Principle II's runtime-dependency boundary.

## 2026-11-17 — Evaluation results live beside the tree, not inside immutable nodes

**Decision.** `TreeNode` is structural only. `EMLTree` carries `evaluations`, a dict keyed by stable node id; `EvaluationResult` and `FailureSummary` are defined once in the foundation phase. One evaluator (`evaluate.py`) computes each node once children-first and returns a new `EMLTree` carrying that dict. Failure reporting extends the same pass; it does not re-evaluate.

**Why.** The earlier task list asked for evaluation in US1 and "per-node evaluation" again in US3, while also putting `evaluation` fields on nodes declared immutable. That produced two implementations of one computation and a constructor field that could only be filled later. Splitting results from nodes keeps structural fields immutable, gives renderers a single source per node id, and lets each story extend the same evaluator instead of replacing it.

## 2026-11-17 — Link titles live in `config.toml` with the URLs

**Decision.** `config.toml` holds `paper_title`, `paper_url`, `video_title`, and `video_url`; both anchors' text and href come from config at generation time. The citation text and explanation stay fixed in source.

**Why.** The original request was "the article title/link and video title/link can be stored in a toml file". Reading it as URLs only left the labels hard-coded while the destinations were adjustable, which is the wrong half of the idea. Determinism is unaffected: config is source-controlled and read once when the page is generated; the browser still computes nothing.

## 2026-11-17 — The `eml` domain rule is non-zero, not positive

**Decision.** A right child of an `eml` node may be any non-zero complex value. Only zero is a domain failure, reported as `undefined`. `non-positive operand` is removed from the reason vocabulary.

**Why.** `cmath.log` accepts negative arguments: `ln(-1) = iπ` is exactly how π is constructed, and FR-014 requires complex evaluation. Keeping a real-domain positivity rule would mark the π construction as failed while claiming to support π and complex numbers. Zero has no logarithm in either domain, so it remains a failure.

The corpus consequence is deliberate: `ln(-1)` and `(-1)^(1/2)` become successful complex cases, while division by zero, a zero right child, and floating-point overflow remain failure cases.

## 2026-11-16 — Node-level failure exits `1`, not `0`

**Decision.** Exit `0` only when the root evaluates. Exit `1` when the tree was generated and written but a node-level failure prevented a root value. Exit `2` for rejected input.

**Why.** The translation is strictly less total than what it translates. `sin(1)` is 0.841, but its EML construction nests exponentials and overflows a double well before the answer returns to range: correct mathematics, correct code, unreachable root. Halting in that case destroys the only useful output, which is *where* evaluation stopped being finite.

The distinction is the reason FR-012 has two reasons rather than one error. `overflow` and `undefined` both mean "this representation cannot express that value here", not "we coded it wrong". A wrong construction never reaches runtime at all; it fails SC-001.

What is preserved from the stricter instinct: a run never exits `0` while reporting a failure, and rejected input produces no artifact.

## 2026-11-16 — Constructions ported from the author's compiler, not from the paper's figure

**Decision.** `constructions.py` is ported from `EML_toolkit/EmL_compiler` in `VA00/SymbolicRegressionPackage` (MIT, DOI 10.5281/zenodo.19183008). The Supplementary Information is the verification standard where the two disagree.

**Why.** The paper body has no formula table: Table 4 gives only RPN lengths (`x+y` = 27, `x/y` = 105, `π` = 193). The formulas live in SI Fig. S1 (a discovery chain) and Table S2 (an adjacency matrix). Transcribing a figure produces off-by-one trees and a test suite that agrees with the transcription error. The compiler is the same derivations in executable form, so a port can be diffed.

## 2026-11-16 — Evaluation over complex numbers, via `cmath`

**Decision.** Node values are complex. `cmath.exp` and `cmath.log`.

**Why.** The trig constructions go through `i`, so real-only evaluation means dropping trig or hand-deriving variants. `math.exp` and `math.log` cannot express this at all: `math.log` rejects non-positive arguments and has no complex form.

## 2026-11-16 — Pure Python traps the extended reals; validity is scoped instead

**Decision.** AC-1 scopes equivalence to inputs where every intermediate stays finite. Constructions that depend on `ln 0 = −∞` or `e^(−∞) = 0` report `undefined` at that node.

**Why.** §4.1 of the paper states that EML expressions "do not work out of the box in pure Python" because special floats are trapped and raise, and that NumPy is the working case. Emulating the extended reals would mean a wrapper type around every operation, chosen to satisfy a handful of edge cases the corpus can simply exclude. Capturing the failure per node and naming it is cheaper and more honest than pretending totality.

## 2026-11-16 — Sign correction on the negative real axis is not planned

**Decision.** π and `i` are exercised in the corpus; a wrong sign there is a defect to be recorded, not silently patched.

**Why.** The paper's own compiler patches the sign of `i` by hand, because the EML form of `ln` contains a `1/z` that introduces a 2πi jump on the negative real axis. Any patch is a deviation from the table and belongs in this file with its justification.

## 2026-11-16 — A valid tree, not the smallest one

**Decision.** Output is *a* valid tree. Node count is displayed. No minimization.

**Why.** Minimal-tree output requires search plus pruning plus a bound. Synthesis is a research problem; the deliverable is a translator.

## 2026-11-16 — Presentation: one static HTML file, native tooltips, `<details>` for depth

**Decision.** Python writes `out.html`; node values are baked into `title` attributes; deep subtrees are wrapped in `<details>`/`<summary>`. No JavaScript, no server, no framework.

**Why.** Hover values are computed in Python at generation time, so no value crosses into a scripting layer. `<details>` gives collapsibility with zero JavaScript, which keeps principle VII intact while making a thousand-node tree navigable.

Pruning was considered and rejected: FR-020 and AC-4 require the text and rendered forms to contain the same nodes, and an elided subtree fails that silently, in the direction the tests cannot see.

Auto-opening out.html via webbrowser.open after generation is a CLI implementation convenience, not a spec requirement. It does not affect the rendered page contract (no input, form, navigation, or JavaScript).

## 2026-11-16 — Values computed once, children before parents; errors are data

**Decision.** A node's value and failure reason are computed once, at or immediately after construction, from children that already carry theirs. A node holds either a number or a failure reason; nothing raises out of evaluation.

**Why.** A recursive `value()` that recomputes subtrees turns one pass into one pass per node and re-runs `exp`/`log` at every level. Computing children first makes the single pass natural, and carrying the failure as data is what FR-012's per-node attribution needs.

Leaves are their own node type rather than a bare `1`, so no caller branches on `isinstance` to distinguish "leaf" from "node".

## 2026-11-16 — Language: Python

**Decision.** Python 3.11+, standard library only.

**Why.** This project exists as the control case for the development process. The framework is the variable; the language is deliberately not. Any third-party runtime dependency requires an entry in this file.
