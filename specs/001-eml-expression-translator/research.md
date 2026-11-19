# Phase 0 Research: EML Expression Translator

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Date**: 2026-11-16 | **Last updated**: 2026-11-19

All technical choices below are resolved from the user input, the feature spec (including 2026-11-17 clarifications), and the project constitution, including the 2026-11-19 top-fragment clarification, so that implementation can proceed without `NEEDS CLARIFICATION` markers.

## Decisions

### 1. Runtime and dependencies
- **Decision**: CPython 3.11+, standard library only. CLI via `argparse`. Config parsed with `tomllib` (read-only). HTML escaping via `html.escape`. Browser open via `webbrowser.open` on the generated file path.
- **Rationale**: Explicit user constraint and Constitution “Additional Constraints” (stdlib-only; 3.11+ makes TOML parsing available without third-party deps). Keeps boundaries obvious and portable.
- **Alternatives considered**: Third-party parser/TOML/templating libraries — rejected (violates stdlib-only; would require `decisions.md` justification and add unnecessary complexity). `ast`-based parsing of a restricted expression subset vs. a small hand-written tokenizer/parser — both acceptable; choose the simpler, safer approach that enforces the supported grammar (FR-002) without evaluating Python code.

### 2. Authoritative constructions
- **Decision**: Every `eml` rewrite is produced by calling/composing plain Python functions defined in root `constructions.py`, which mirrors the Supplementary Information of arXiv:2603.21852v2. Directly tabulated forms call their table function; non-tabulated supported forms are obtained by composing tabulated constructions only (FR-004, FR-005). No formulas re-derived inline or duplicated in tests.
- **Rationale**: Constitution Principle V is absolute. `constructions.py` is the single executable source of formulas.
- **Alternatives considered**: Encoding formulas in data tables or deriving at call sites — rejected (duplication/drift risk and violates Principle V). If table and paper disagree, correct table and record note in `decisions.md`.

### 3. Single-source constants (Principle VI)
- **Decision**: Define once in `eml_calculator/constants.py` and import everywhere (including tests):
  - `REL_TOL_EPSILON` — relative tolerance `ε` for corpus equivalence checks **and** for the complex-to-real display rule (default `1e-9`; one value in one place).
  - `IMAG_ABS_FLOOR = 1e-12` — absolute floor for the complex-to-real display rule. A value is displayed as real exactly when `abs(imag) <= max(IMAG_ABS_FLOOR, REL_TOL_EPSILON * max(1.0, abs(real)))` (FR-014). No separate display RTOL is introduced; the shared `ε` is the relative term.
  - `MAX_NODE_EVAL_DEPTH` (and any overflow guard limits) to detect runaway/overflow-prone evaluation paths and attribute failures to a specific node.
  - `DEFAULT_FREE_VAR_SAMPLES` / sample-range descriptors used **only** by internal construction-verification tests. Runtime input is closed; free variables are rejected (FR-002).
- **Rationale**: Constitution Principle VI forbids retyping shared numbers; the 2026-11-17 clarification fixes the exact real-display predicate and requires the absolute floor and `ε` to be shared constants (FR-014, SC-001, Assumptions).
- **Alternatives considered**: Hard-coding thresholds in evaluator/renderer/tests — rejected. A separate `IMAG_DISPLAY_RTOL` distinct from `ε` — rejected because the clarified rule explicitly reuses `ε`.

### 4. Parsing and supported input (FR-001, FR-002, FR-015)
- **Decision**: Accept exactly one positional CLI argument: the expression string. No interactive/page input. Support numeric literals, parentheses, unary minus, binary `+ - * / ^`, functions `exp ln sqrt sin cos tan`, and named constants `pi`, `e` (input-only; expanded to `1`-based `eml` forms in output). Numeric literals are decimal integers and decimals with an optional exponent (e.g. `2`, `2.5`, `.5`, `1e-3`); hexadecimal (`0x10`), binary (`0b10`), and underscore-separated (`1_000`) forms are rejected. The grammar is closed: free variables such as `x` and all other identifiers are rejected with a clear user-facing error; unknown named constants (`tau`, `phi`) are explicit errors naming the constant, not parse fallthroughs or implicit variables. Use a small hand-written tokenizer/parser rather than `ast.literal_eval`, which would accept the rejected literal forms.
- **Rationale**: Matches FR-001/002/015 and edge cases, including the 2026-11-17 clarification on literal formats and the earlier closed-input clarification. Input-only constants still become `eml`/`1` trees (FR-002).
- **Alternatives considered**: `ast`-based parsing — rejected because it would accept Python literal syntax that the spec forbids. Accepting free variables in runtime input — rejected; sample ranges are confined to internal construction verification.

### 5. EML tree model and rewrite (FR-003, FR-006, FR-007, FR-016)
- **Decision**: Internal `EMLTree` is a binary tree: internal node = `eml(left, right)`; leaf = `1`. Rewrite produces *a* valid equivalent tree (no minimization). Text form: one node per line, `eml(` opens, children indented beneath, `)` closes, leaves `1`. Rendered browser form mirrors the same structure (one visual node per `eml`, one per `1`) using semantic HTML/CSS only (no JS). Each node is keyboard-focusable, keeps its precomputed value/failure in a native `title` for hover, and reveals the same precomputed value on `:focus` using CSS only (FR-009); no JavaScript and no recomputation.
- **Rationale**: Satisfies FR-003/006/007/009/016 and the 2026-11-17 focus clarification; deterministic structure enables SC-004.
- **Alternatives considered**: SVG/Canvas/JS tree libraries — rejected (no JS/framework; renderer must compute nothing). JS-driven focus handlers — rejected; CSS `:focus` suffices and preserves determinism.

### 6. Evaluation, domain, and failures (FR-008–FR-014, SC-001–SC-003)
- **Decision**: Evaluate all nodes in Python using complex arithmetic (`cmath` where appropriate). Enforce the complex-domain rule: for every `eml` node the evaluated right child must be non-zero; a zero right child is an `undefined` failure. Negative and complex right children are valid — `cmath.log(-1)` is `iπ`, which is how π is obtained. Map evaluation problems to exactly: `overflow` and `undefined` (division by zero, zero right child, non-finite results). Never crash; never silently emit `nan`/`inf`; attach failure state to the specific node. Every failing node is visibly marked with its reason **in addition to** its native `title`, all failing nodes and reasons are listed in a failure summary, and every ancestor of a failed node is marked `undefined` unless it has its own more specific reason, so the deepest specific reason stays attributable (FR-012, SC-006). Display a value as real exactly when `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))`; otherwise keep it representable in complex form (FR-014).
- **Rationale**: Directly implements FR-011–FR-014 and the 2026-11-17 clarifications; supports diagnostic, node-attributed reporting (FR-012, SC-006) without silent `nan`/`inf`.
- **Alternatives considered**: Raising exceptions to abort — rejected for supported error cases (must not crash; must attribute). Returning raw float `nan/inf` — rejected. Marking only the deepest node and leaving ancestors blank — rejected; clarified rule requires ancestors `undefined`.

### 7. Deterministic HTML output and page content (FR-007, FR-009, FR-010, FR-017–FR-019, Principle VII)
- **Decision**: Generate a single self-contained `out.html` (overwritten each run). Page-top H1, summary paragraph, "References" heading, and Article/Video label markup come from the source-controlled root `top_fragment.html` read at generation time (FR-017/FR-018); only link titles and URLs come from `config.toml`, and the separate fixed citation paragraph is removed. Above the tree the order is: H1; summary; "References" heading; Article row using config `paper_title`/`paper_url`; Video row using config `video_title`/`video_url` (empty strings when absent). Then, still above the tree, show the source expression (exactly as supplied) and its precomputed evaluated value, or the failure summary in place of the value when it cannot be evaluated (FR-019). No other anchors. Total node count displayed and consistent with text/rendered forms. Failure reporting includes visible per-node reason markers and a summary listing every failing node and reason, with ancestors marked `undefined`. Determinism via stable ordering/indentation/escaping/serialization (no timestamps, no random IDs, normalized whitespace/line endings as chosen once).
- **Rationale**: Meets all page/attribution/determinism requirements and makes inspection possible without JS; the failure summary is required for node-attributed diagnosis (FR-012, SC-006).
- **Alternatives considered**: Multiple files or external CSS/JS/assets — rejected (must be one self-contained file, no JS/network).

### 8. Configuration (FR-018)
- **Decision**: `config.toml` read at generation time (not runtime-fetched, not constructed). Schema keeps four unchanged keys with literals: `paper_title` (plain string, may include author name and article title; no fixed sample literal), `paper_url` (expected `https://arxiv.org/abs/2603.21852`), `video_title`, and optional `video_url`. Absent video keys substitute as empty strings; the renderer performs no row omission or error handling. Titles and URLs are written as escaped literals into HTML; literal page-top content comes from `top_fragment.html`.
- **Rationale**: Spec requires literals in source-controlled config and literal substitution with no renderer-side omission.
- **Alternatives considered**: CLI flags for URLs or runtime discovery — rejected.

### 9. Validation corpus (SC-001–SC-004, Key Entities)
- **Decision**: Maintain a fixed corpus of ~30 expressions as data in `eml_calculator/corpus.py` (or an adjacent data module) referencing named constants for `ε` and sample ranges. Include required failure cases: division by zero, an `eml` node with a zero right child, and a tree deep enough to overflow standard floating-point evaluation; include a successful complex case with a negative right child (π via `ln(-1)`); plus `1+1` structural/node-count check and a spread of supported operators/functions/constants/compositions. Each case records expected kind (equivalent value within tolerance / specific node failure reason). Integration tests run the corpus end-to-end.
- **Rationale**: Spec mandates corpus-driven verification and specific failure scenarios; keeping it as owned data aligns with testing principle III.
- **Alternatives considered**: Ad-hoc/manual-only checks — rejected (not measurable/repeatable).

### 10. CLI behavior and `out.html` opening
- **Decision**: Invocation like `python -m eml_calculator "1+1"` (and/or console script) parses args, generates outputs, writes `out.html` in the working directory (or a deterministic, documented location per contract), prints the indented text tree and summary (expression, value, node count, failures if any) to stdout, prints user-facing errors to stderr with non-zero exit on input/unsupported errors, and attempts to open `out.html` via `webbrowser.open`. Opening is a boundary side effect; core generation remains testable without it.
- **Rationale**: Matches stated UX (CLI arg, emit/open out.html) while preserving explicit boundaries and testability.
- **Alternatives considered**: Serving over HTTP — rejected (no server).

### 11. Owner-authored top fragment as generation-time input (FR-017, FR-018, FR-021)
- **Decision**: A source-controlled root `top_fragment.html` (deterministic default `./top_fragment.html`) supplies the page-top H1, summary paragraph, "References" heading, and Article/Video label markup. It is read at generation time and inserted as supplied; only article/video link text and hrefs come from `config.toml`. A missing or unreadable fragment is a user-facing generation error (exit `2`). No runtime fetch, no paraphrase, no JavaScript.
- **Rationale**: The 2026-11-19 clarification makes the owner the author of the header prose and removes the fixed citation paragraph; keeping it in one source-controlled HTML file preserves determinism (Principle VII) and the pure-renderer boundary (Principle II).
- **Alternatives considered**: Python string constants (rejected — presentation in code), new config keys for header text (rejected — would grow the four-key link contract and put markup in TOML), fixed citation/explanation in source (superseded by the clarification).

## Resolved Clarifications Summary

| Topic | Resolution |
|-------|------------|
| Language/deps | Python 3.11+, stdlib only, argparse/tomllib/webbrowser; hand-written parser (no `ast.literal_eval`) |
| Formula source | `constructions.py` only (Principle V) |
| Shared numbers | Single `constants.py` (ε = relative tolerance, `IMAG_ABS_FLOOR = 1e-12`, limits, internal samples) |
| Determinism | No JS/network/time/random; stable serialization; `title` values precomputed |
| Input grammar | Closed; numeric literals decimal/decimal-with-exponent only; hex/binary/underscore/free variables rejected |
| Node value inspection | Native `title` for hover + CSS-only `:focus` reveal of the precomputed value; no JS |
| Failure taxonomy | `overflow`, `undefined` (zero right child) at specific node; every failing node visibly marked, all failures summarized, ancestors marked `undefined` |
| Complex display | Real when `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))`; otherwise complex form |
| Config/links | `config.toml` keeps four keys for link titles/URLs; omit video row if unset; no fixed citation paragraph |
| Page-top content | Owner-authored root `top_fragment.html`: H1, summary, "References", Article/Video labels; only link titles/URLs from config |
| Corpus | ~30 fixed expressions incl. required failures; data-driven tests |
| Translation scope | Any valid equivalent tree; no minimization |
