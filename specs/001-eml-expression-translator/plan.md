# Implementation Plan: EML Expression Translator

**Branch**: `001-eml-expression-translator` | **Date**: 2026-11-16 | **Last updated**: 2026-11-17 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-eml-expression-translator/spec.md`, including 2026-11-17 clarifications (numeric literal grammar, CSS-only focus reveal, visible failure markers/summary, exact complex-to-real display rule).

## Summary

Build a Python 3.11+ standard-library CLI that parses a single arithmetic expression (closed input only; decimal integers/decimals with optional exponent, no hex/binary/underscore literals), rewrites it into an equivalent binary tree using only the `eml` operator and leaf `1` (constructions ported from the author's EML compiler into `constructions.py`, verified against arXiv:2603.21852v2 SI), evaluates every node over complex numbers, and emits one deterministic, self-contained `out.html` (no JavaScript, no network, no framework). Every node keeps its precomputed value in a native `title` for hover and reveals it on keyboard focus with CSS only; every failing node is visibly marked with its reason, all failures are listed in a summary, and ancestors of failures are marked `undefined` so the deepest specific reason stays attributable. Complex values display as real under the shared `IMAG_ABS_FLOOR`/`ε` rule. Deep subtrees are wrapped in native `<details>`. The CLI also prints the indented text tree and summary to stdout/stderr as appropriate, then opens `out.html`. Link titles and URLs come from `config.toml` read at generation time; construction formulas come only from `constructions.py`.

## Technical Context

**Language/Version**: Python 3.11+ (CPython), standard library only (`argparse`, a small hand-written tokenizer/parser rather than `ast.literal_eval` so hex/binary/underscored literals cannot slip in, `cmath`/`math`, `tomllib`, `pathlib`, `webbrowser`, `html`; `decimal` not required)  
**Primary Dependencies**: None at runtime (stdlib only). `pytest` is a test-only dependency declared in `requirements-dev.txt`; it is not imported by runtime code. Test module basenames are unique, so `tests/`, `tests/unit/`, and `tests/integration/` need no `__init__.py` for pytest discovery. `constructions.py` and `config.toml` are project-owned inputs.  
**Storage**: Files only — read `config.toml` and `constructions.py`; write deterministic `out.html` (overwrite). No database.  
**Testing**: `pytest` (dev-only; installed from `requirements-dev.txt`) for unit/integration tests; a fixed validation corpus (≈30 expressions, including required failure cases) exercised as data-driven tests. Run from the repository root with `python3 -m pytest`; no `__init__.py` is required in test directories as long as test module basenames remain unique.  
**Target Platform**: Local developer/user machines running Python 3.11+ (macOS/Linux/Windows) with a default browser available for `webbrowser.open`.  
**Project Type**: Single-project CLI/tool with generated static HTML artifact.  
**Performance Goals**: Interactive single-expression runs; render/inspect one tree view within 10 seconds for supported corpus expressions (SC-005). No optimization for minimal tree size (FR-016).  
**Constraints**: Deterministic byte-identical `out.html` for the same expression and config (Principle VII; FR-017 citation/explanation fixed, anchor titles and URLs from config). No JS/network/recomputation in page; focus reveal is CSS-only and native `title` is retained for hover (FR-009). Numeric literals limited to decimal integers and decimals with an optional exponent (e.g. `2`, `2.5`, `.5`, `1e-3`); hex, binary, and underscore-separated forms rejected; free variables rejected (FR-002). Shared constants — ε, `IMAG_ABS_FLOOR = 1e-12`, depth/guard limits, and any internal sample ranges — defined once and imported (Principle VI); display a value as real when `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))` (FR-014). Node-level failures are `overflow` or `undefined` (a zero `eml` right child is `undefined`; negative and complex right children are valid) without crash/silent `nan`/`inf`; every failing node is visibly marked with its reason, all failures are listed in a summary, and ancestors of failed nodes are marked `undefined` (FR-011–FR-013).  
**Scale/Scope**: One expression per invocation → one tree → one `out.html`; validation corpus ~30 expressions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How this plan complies |
|-----------|--------|------------------------|
| I. Code for Readability | PASS | Small modules with explicit responsibilities (parse, rewrite, evaluate, render, CLI); clear naming; comments only for intent/paper references. |
| II. Make Dependencies Explicit | PASS | I/O boundaries explicit: CLI args in, config/file reads and HTML write/browser open at edges; pure transformation core (parse→AST→EML tree→values/text/HTML model). |
| III. Test the Transformation, Not the Plumbing | PASS | Unit tests for parsing/rewriting/evaluation/formatting transforms; integration tests for CLI→file generation and corpus end-to-end; mock only external/unowned effects if needed (e.g. `webbrowser.open`) — not owned logic. Bug fixes require failing test first when practical. |
| IV. Favor Simple, Predictable Design | PASS | Immutable/simple tree data structures; pure evaluation that returns a new tree with per-node results; pure formatting functions; side effects localized to CLI/output boundary. |
| V. Construction Table Is the Only Source of Formulas | PASS | All `eml` rewrites sourced from `constructions.py`; no inlined/rederived formulas at call sites or in tests; paper-vs-table discrepancies recorded in `decisions.md`. |
| VI. Every Number Is Named Once | PASS | `ε`, `IMAG_ABS_FLOOR = 1e-12` (used together in the real-display rule `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))`), evaluation guard/depth limits, and any corpus sample ranges defined in one constants module and imported everywhere (including tests). |
| VII. Renderer Computes Nothing, and Its Output Is Deterministic | PASS | Python computes all node values/failure states and writes them into markup (native `title` for hover, CSS-only `:focus` reveal, visible failure markers, failure summary) and text; page has no JS/network; stable traversal/formatting yields byte-identical output for same inputs. |
| VIII. The Agent Implements, the Human Reviews | PASS | Work delivered in reviewable chunks; this plan/tasks will be reviewed before/alongside implementation. |

**Additional constraints**: Stdlib-only runtime (3.11+ provides `tomllib`); any deviation recorded in `decisions.md`. No gate violations requiring Complexity Tracking.

**Post-design re-check (Phase 1)**: PASS — data model, contracts, and quickstart preserve pure-core/boundary split, single-source constants/constructions (including `IMAG_ABS_FLOOR`), deterministic no-JS rendering with CSS-only focus reveal and visible failure markers/summary, closed decimal-only input grammar, and explicit ancestor-`undefined` failure reporting.

## Project Structure

### Documentation (this feature)

```text
specs/001-eml-expression-translator/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── config.toml.md
│   └── html-output.md
└── tasks.md              # created later by /speckit.tasks
```

### Source Code (repository root)

```text
constructions.py          # authoritative eml construction table (plain functions), ported from
                          # the author's EML compiler (VA00/SymbolicRegressionPackage)
config.toml               # link titles and URLs, read at generation time
requirements-dev.txt      # pytest only, test-time; no runtime third-party dependencies
decisions.md              # reverse-expensive choices, spec/implementation drift, dependency notes

eml_calculator/
├── __init__.py
├── __main__.py           # python -m eml_calculator entry
├── cli.py                # argparse, orchestration, open/write boundaries
├── constants.py          # ε, display thresholds, limits, sample defaults (single source)
├── parser.py             # expression string -> source expression structure
├── rewrite.py            # source structure -> EML tree via constructions.py
├── evaluate.py           # node values computed once (children before parents), failure attribution
├── render_text.py        # indented text tree
├── render_html.py        # deterministic self-contained HTML (titles baked in, <details> nesting)
└── corpus.py             # validation corpus definitions/loading (data, no formulas)

tests/
├── unit/
│   ├── test_parser.py
│   ├── test_rewrite.py
│   ├── test_evaluate.py
│   ├── test_render_text.py
│   └── test_render_html.py
└── integration/
    ├── test_cli.py
    └── test_corpus.py
```

**Structure Decision**: Single flat package `eml_calculator/` at repo root plus root-level `constructions.py`/`config.toml` as specified by user input; `tests/unit` for pure transforms and `tests/integration` for boundaries/corpus/CLI wiring, matching Constitution Principle III.

## Complexity Tracking

No constitution violations. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
