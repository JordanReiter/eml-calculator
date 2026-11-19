# Quickstart / Validation Guide: EML Expression Translator

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Contracts**: [contracts/](./contracts/) | **Last updated**: 2026-11-19

This guide describes runnable validation scenarios to prove the feature works end-to-end, including the 2026-11-17 clarifications and the 2026-11-19 top-fragment clarification. It is a validation/run guide (not an implementation listing).

## Prerequisites
- Python 3.11+ (`python3 --version`).
- Repository checked out on branch `001-eml-expression-translator` with feature artifacts in `specs/001-eml-expression-translator/`.
- Project files present at generation time: `constructions.py` (authoritative construction table), `config.toml` (link metadata per [contracts/config.toml.md](./contracts/config.toml.md)), and root `top_fragment.html` (owner-authored page-top markup per [contracts/html-output.md](./contracts/html-output.md)).
- No third-party runtime dependencies required (standard library only).

## Setup
1. From repository root, ensure `config.toml` supplies the four unchanged keys with link literals only:
   - `paper_title` = a plain string of your choice (it may contain the author name and article title; no fixed sample literal such as `the paper` is required).
   - `paper_url = "https://arxiv.org/abs/2603.21852"`
   - optional `video_title` and `video_url` link literals; when absent, empty strings are substituted into the fragment with no error (no renderer-side row omission).
2. Supply the owner-authored header at the root: create `top_fragment.html` with the H1, summary paragraph, "References" heading, and Article/Video label markup. The renderer inserts this literal markup and fills only the article/video anchors from `config.toml`; a missing or unreadable fragment is a user-facing generation error (exit `2`). The deterministic default path is `./top_fragment.html` at the repository root.
3. Confirm `constructions.py` is available and defines the tabulated `eml` constructions used by the rewriter.
4. Install the test-only dependency and run the test suite from the repository root:
   - `python3 -m pip install -r requirements-dev.txt`
   - `python3 -m pytest -q`
   - The test directories are not packages; pytest discovers them without `__init__.py` because test module basenames are unique.

## Run: translate an expression
Execute the CLI with a single expression argument:

- `python3 -m eml_calculator "1+1"`

**Expected outcomes**
- Prints an indented text tree where `eml(` opens nodes, children are indented, `)` closes, and leaves are `1` (see [contracts/cli.md](./contracts/cli.md)).
- Reports the source expression as supplied, the evaluated value, and the total node count.
- Writes/overwrites `out.html` in the working directory (deterministic for same inputs/config) and attempts to open it in the default browser.
- In `out.html`: the fragment-driven header appears above the tree in order — H1, summary, "References" heading, Article row (config `paper_title`/`paper_url` only), Video row (config `video_title`/`video_url`, empty strings when absent) — followed by the source expression and value; the literal H1/summary/label text comes from `top_fragment.html`, with no separate fixed citation paragraph; every node has a baked-in native `title` with its computed value and is keyboard-focusable with a CSS-only focus reveal; failing nodes are visibly marked and all failures are summarized; no JavaScript and no network requests (see [contracts/html-output.md](./contracts/html-output.md)).

## Validation scenarios

### 1. P1 – Correct `eml`/`1` translation and equivalence
- **Run**: `python3 -m eml_calculator "1+1"` and a sample of supported expressions (operators/functions/constants per spec). Also try accepted literal forms: `2`, `2.5`, `.5`, `1e-3`.
- **Verify**: output contains only `eml` and `1`; root value equals source value within tolerance `ε` (from shared constants). Composed constructions remain valid `eml`/`1` form. Accepted decimal/exponent literals parse; `0x10`, `0b10`, `1_000`, and free variables such as `x` are rejected with clear errors (exit `2`).

### 2. P2 – Structural parity and node count
- **Run**: translate `1+1`.
- **Verify**: text tree and rendered HTML tree show the same nodes in the same structure; displayed node count matches both representations (SC-004).

### 3. P3 – Node inspection values
- **Run**: open generated `out.html` for a valid expression; hover a node with the mouse, then Tab to focus it.
- **Verify**: the native `title` shows the precomputed value on hover; keyboard focus reveals the same precomputed value via CSS only (no JavaScript, no recomputation). A value is displayed as real exactly when `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))` with shared `IMAG_ABS_FLOOR = 1e-12` and `ε`; meaningful imaginary parts remain representable in complex form.

### 4. P3 – Domain and evaluation failures (node-attributed, no crash)
- **Run** cases from the validation corpus, including at minimum:
  - division by zero (e.g. `1/0`)
  - an `eml` node whose right child evaluates to zero
  - a tree deep enough to overflow standard floating-point evaluation
  - negative argument to `ln` (e.g. `ln(-1)`) and a negative base raised to a fractional power as *successful* complex cases
- **Verify**: process does not crash; no silent `nan`/`inf`; each failure case reports `overflow` or `undefined` (zero right child) at the correct node in text/HTML (SC-002, SC-003, SC-006). The complex cases report values with meaningful imaginary parts, not failures. Every failing node is visibly marked with its reason in addition to its native `title`; a failure summary lists every failing node and reason; ancestors of failed nodes are marked `undefined` so the deepest specific reason remains attributable.

### 5. P3 – Fragment header, links, and framing (video present / video omitted)
- **Run**: with a valid `top_fragment.html`, generate a page with `video_title`/`video_url` configured, then generate again with both video keys omitted. Also try a run with `top_fragment.html` missing to check the error path.
- **Verify (video present)**: the header order is H1 → summary paragraph → "References" heading → Article row → Video row, with all literal H1/summary/label content supplied by `top_fragment.html` and no separate fixed citation paragraph; the Article anchor uses config `paper_title` as a plain string (may include author name/article title, no added `<em>` styling) and `paper_url`; the Video anchor uses config `video_title`/`video_url`; no other anchors exist (FR-017, SC-007).
- **Verify (video omitted)**: absent video values substitute as empty strings with no error; no placeholder tokens remain; the rendered rows are exactly those in `top_fragment.html` (SC-007).
- **Verify (source/value and errors)**: source expression and its value appear below the fragment header and above the tree and match CLI-reported values (SC-008); a missing or unreadable `top_fragment.html` produces a clear user-facing generation error and exit `2` with no misleading `out.html`.

### 6. Input errors
- **Run**: `python3 -m eml_calculator "tau"` (and an unsupported operator/function, plus `0x10`, `0b10`, `1_000`, and `x`).
- **Verify**: clear user-facing error naming the unknown constant/unsupported/rejected element; exit `2`; no misleading `out.html`.

### 7. Determinism
- **Run**: generate `out.html` twice for the same expression with unchanged config, constructions, and `top_fragment.html`.
- **Verify**: outputs are byte-identical.

## Notes
- Validation corpus (~30 expressions, including required failures, any free-variable sample ranges, and `ε`) is defined as shared data/constants and exercised by integration tests per [research.md](./research.md) and [data-model.md](./data-model.md).
- This project is the control case where the agent implements and the human reviews (Constitution Principle VIII); validate in reviewable chunks.