# Contract: CLI (`eml_calculator`)

**Last updated**: 2026-11-17 (clarified input grammar and failure reporting)

## Purpose
Defines the command-line interface and observable behavior for translating one expression into an `eml`/`1` tree, emitting text and `out.html`, and opening the result.

## Invocation
- **Module form**: `python -m eml_calculator "<expression>"`
- **Input**: exactly one required positional argument — the arithmetic expression string (FR-001, FR-015).
- **Working directory assumptions**: `config.toml` is read from a deterministic, documented location (project/root or alongside invocation as defined at implementation; contract requires generation-time read, not network). `out.html` is written to a deterministic path (default: `./out.html` in current working directory) and overwritten if present.

## Supported expression grammar (input)
- Numeric literals: decimal integers and decimals with an optional exponent only (e.g. `2`, `2.5`, `.5`, `1e-3`). Hexadecimal (`0x10`), binary (`0b10`), and underscore-separated (`1_000`) forms are rejected.
- Parentheses `(` `)`.
- Unary minus.
- Binary operators: `+  -  *  /  ^`.
- Functions: `exp`, `ln`, `sqrt`, `sin`, `cos`, `tan`.
- Named constants: `pi`, `e` (input-only; expanded in output).
- The grammar is closed: free variables (e.g. `x`) and any other identifiers are rejected with a clear user-facing error; they are never assigned sample values.

Unsupported elements produce a clear, user-facing error that identifies the unsupported operator/function/element. Unknown named constants (e.g. `tau`, `phi`) produce a clear error naming the constant.

## Outputs

### On success (valid, evaluable expression)
- **stdout**: indented text tree of the rewritten `eml`/`1` expression (FR-006), plus a concise summary including at least: source expression (as supplied), evaluated root value/display, and total node count. Formatting is deterministic.
- **File**: `out.html` written as a deterministic, self-contained HTML document per [html-output.md](./html-output.md) containing baked-in node values (native `title` attributes), no JS, no network.
- **Side effect**: attempts to open `out.html` in the default browser (`webbrowser.open` on its path).
- **Exit code**: `0`.

### On supported evaluation/domain failure (translatable expression)
- **stdout**: indented text tree when structurally produced; summary includes source expression, total node count, and a failure summary listing every failing node with reason `overflow` or `undefined` (a zero right child is `undefined`). Ancestors of failed nodes are reported `undefined` unless they have their own more specific reason. No silent `nan`/`inf`.
- **stderr**: may include a clear diagnostic summary identifying the failing node/reason (implementation chooses stream split but must remain explicit and testable).
- **File**: `out.html` still generated with failure states baked into native `title` attributes, visible per-node failure markers, the full failure summary, and ancestors marked `undefined`.
- **Exit code**: `1`.

### On input/parse/unsupported-syntax error
- **stderr**: clear, user-facing error identifying the problem (and the unsupported/unknown element name where applicable).
- **stdout/file**: no `out.html` required for unparseable/unsupported input unless partial output is explicitly defined; prefer no misleading artifact.
- **Exit code**: `2`.

## Exit status

| Status | Meaning | Artifact |
| :--- | :--- | :--- |
| `0` | Root evaluated; tree is complete | `out.html` written |
| `1` | Tree generated, node-level failure prevented a root value | `out.html` written; failure visibly marked at the node, summarized, ancestors `undefined` |
| `2` | Input rejected: unparseable, unsupported element, or unknown constant | no `out.html` |

A run MUST NOT exit `0` while reporting a failure anywhere (FR-021, SC-009).

## Determinism and boundaries
- Core transformations (parse, rewrite, evaluate, render model) are pure/deterministic given inputs and config.
- I/O boundaries: read `config.toml`, read `constructions.py` (module), write `out.html`, open browser.
- Same expression + same config + same construction table => byte-identical `out.html` and identical text tree output.

## Examples (illustrative)
- `python -m eml_calculator "1+1"` → valid `eml`/`1` text tree, `out.html` with matching structure and node count, root equals 2 within tolerance.
- `python -m eml_calculator "ln(-1)"` → evaluates to `iπ` in complex form; no failure and no silent `nan`/`inf`. Use `1/0` for an `undefined` failure at a specific node.
- `python -m eml_calculator "tau"` → clear input error naming unknown constant `tau`.
- `python -m eml_calculator "0x10"` (or `0b10`, `1_000`, `x`) → clear input error rejecting the unsupported literal/free variable; exit `2`.