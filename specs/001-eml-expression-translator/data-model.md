# Data Model: EML Expression Translator

**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md) | **Last updated**: 2026-11-19

This document describes the conceptual entities, fields, relationships, validation rules, and state transitions used by the feature. It is implementation-guiding, not code. It incorporates the 2026-11-17 clarifications on literal formats, CSS-only focus reveal, visible per-node failures with summary, ancestor `undefined` marking, and the exact complex-to-real display rule, plus the 2026-11-19 fragment-driven page header.

## Entities

### 1. Input Expression
- **Description**: The raw arithmetic expression provided as the single CLI argument.
- **Fields**:
  - `raw_text` (string): exact user-supplied text (preserved for display per FR-019/SC-008).
  - `source_location` (implicit): CLI argument position/index for error reporting.
- **Validation rules**:
  - Must be present and parseable under the supported grammar (FR-001, FR-002).
  - Numeric literals are decimal integers and decimals with an optional exponent (`2`, `2.5`, `.5`, `1e-3`); hexadecimal, binary, and underscore-separated forms are rejected with a clear input error.
  - The grammar is closed: free variables (e.g. `x`) and any other identifiers are rejected with a clear input error, never assigned a sample value.
  - Unsupported operators/functions/identifiers produce a clear input error naming the element.
  - Unknown named constants (e.g. `tau`, `phi`) produce a clear input error naming the constant (not an implicit variable).
- **Relationships**: Parsed into one **Source Expression Structure**.

### 2. Source Expression Structure
- **Description**: Parsed, pre-rewrite representation of the input (AST-like tree/expression nodes).
- **Fields (conceptual)**:
  - `kind`: literal | named_constant (`pi`,`e`) | unary_minus | binary_op (`+ - * / ^`) | function_call (`exp,ln,sqrt,sin,cos,tan`) | group.
  - `children`: ordered child expressions as applicable.
  - `token/value`: literal value or operator/function identifier.
  - `span` (optional): location for precise error attribution.
- **Validation rules**:
  - Grammar-conformant only; no evaluation required at this stage except structural validity.
  - Numeric literals other than `1` are allowed in input but will not appear as leaves in output (FR-002, edge case).
- **Relationships**: Rewritten into one **EML Tree**. Source `raw_text` retained alongside for display.

### 3. EML Tree
- **Description**: The rewritten expression where every internal node is `eml(x, y)` and every leaf is `1` (FR-003).
- **Fields**:
  - `root` (Tree Node): root of the binary tree.
  - `node_count` (integer): total nodes (internal `eml` nodes + `1` leaves), consistent across text and rendered views (FR-010, SC-004).
  - `source_text` (string): original input expression as supplied (for page/CLI display).
  - `evaluations` (dict: node id → Evaluation Result): per-node results computed once by the single evaluation pass; empty on a freshly rewritten tree, filled on the tree returned by evaluation.
- **Validation rules**:
  - Structurally valid binary form: each internal node has exactly two children (`left`, `right`); each leaf is the constant `1`.
  - Represents *a* valid equivalent tree; no minimality requirement (FR-016).
  - The imaginary unit `i` may appear as an internal construction in `constructions.py` for complex evaluation; it is not a supported user input (FR-002 lists only `pi` and `e`).
- **Relationships**: Contains **Tree Nodes** and carries their **Evaluation Results** in a side mapping keyed by node id. Rendered to text and HTML.

### 4. Tree Node
- **Description**: A single node in the EML tree.
- **Fields**:
  - `id/index` (stable): deterministic identity/order for rendering and reporting (e.g. pre-order index).
  - `kind`: `eml` | `leaf_one`.
  - `left`, `right` (Tree Node | null): children for `eml`, null for leaf.
  - `display_label`: `eml` or `1` for structural rendering.
- **Validation rules**:
  - For `kind=eml`, `left` and `right` must exist.
  - During evaluation, an `eml` node's right child must have a non-zero evaluated value; a zero right child is a node-level `undefined` failure (FR-011). Negative and complex right children are valid (FR-014).
  - An ancestor of a failed node MUST have its Evaluation Result in `EMLTree.evaluations` marked `failed` with reason `undefined` unless it has its own, more specific failure reason, preserving attribution of the deepest specific reason (FR-012).
- **Relationships**: Part of one **EML Tree**; its **Evaluation Result** is held in the tree's `evaluations` mapping under its stable id; contributes to the **Failure Summary** when failed.

### 5. Evaluation Result
- **Description**: Outcome of evaluating a Tree Node (or source expression, for comparison/display).
- **Fields**:
  - `status`: `ok` | `failed`.
  - `value` (complex/real, when `ok`): numeric result.
  - `display_value` (string): formatted for UI/text; shown as real when the predicate below holds (FR-014).
  - `value_display` (string, precomputed): value or failure reason placed in the native `title` for hover and revealed on keyboard focus via CSS only (FR-009); never recomputed in the browser.
  - `display_as_real` (boolean): true exactly when `abs(imag) <= max(IMAG_ABS_FLOOR, ε × max(1, abs(real)))`, where `IMAG_ABS_FLOOR = 1e-12` and `ε` are shared constants from `constants.py`; otherwise the value remains representable in complex form (FR-014).
  - `failure_reason` (enum, when `failed`): `overflow` | `undefined`.
  - `attributed_node` (node id): the specific node where failure is detected/reported (FR-012, FR-013).
  - `message` (string): specific, user-facing reason suitable for visible markers, summary, text, and native `title` display.
  - `visible_failure_marker` (string | null): when failed, the reason text rendered visibly in the tree in addition to the native `title` (FR-012).
- **Validation rules**:
  - `failure_reason` must be one of the allowed values when failed.
  - Real-display predicate uses the shared `ε` and `IMAG_ABS_FLOOR` constants; no threshold is retyped in the formatter or tests (Principle VI, FR-014).
  - Must never be represented as silent `nan` or `inf` to the user (FR-013, SC-003).
  - Root equivalence for valid cases: root `value` matches source expression value within relative tolerance `ε` over stated sample ranges (FR-008, SC-001).
- **State transitions**:
  - `pending` (implicit during traversal) → `ok` with value, or `failed` with reason at node.
  - A failure at a child that prevents a valid `eml` computation is attributed and surfaced according to evaluation rules so the user can identify the specific failing node and reason (no crash).

### 6. Failure Summary
- **Description**: Complete, node-attributed list of evaluation/domain problems generated when one or more nodes fail (FR-012, SC-006).
- **Fields**:
  - `entries` (list of `{node_id, failure_reason, message}`): every failing node, including ancestors marked `undefined`; no failing node is omitted even inside collapsed sections.
  - `source_value_available` (boolean): whether the source expression produced a value; when false, this summary appears in place of the source value above the tree (FR-019).
- **Validation rules**:
  - Every node with a failed **Evaluation Result** appears exactly once; deepest specific reasons remain attributable because ancestors use `undefined` (FR-012).
  - Reasons are limited to `overflow` and `undefined`; no silent `nan`/`inf` (FR-013).
  - Rendered in text/HTML without introducing additional anchors (FR-017).
- **Relationships**: Derived from the **EML Tree** node evaluations; consumed by text and HTML renderers and by the CLI summary.

### 7. Validation Corpus
- **Description**: Fixed set of ~30 expressions used to verify equivalence and failure reporting (Key Entities, SC-001–SC-003).
- **Fields**:
  - `id/name` (string).
  - `expression` (string).
  - `kind`: `equivalence` | `failure`.
  - `expected`: for equivalence — source/root match within `ε` (and internal construction-verification sample spec where used); for failure — expected `failure_reason` and attributable node/condition.
  - `sample_range` (optional): named sample points/range used only for internal construction-verification checks of the input variable, defined via shared constants/data; runtime input remains closed (FR-002).
  - `notes` (optional): e.g. includes `1+1` structural check, overflow-depth case.
- **Validation rules**:
  - Must include at minimum: division by zero, an `eml` node with a zero right child, a tree deep enough to overflow standard floating-point evaluation, and a successful complex case with a negative right child (π via `ln(-1)`) (SC-002).
  - All numeric thresholds/ranges referenced from single-source constants (Principle VI).
- **Relationships**: Drives integration/corpus tests; independent of per-run CLI input except as test data.

### 8. Page/Output Metadata (Config)
- **Description**: Generation-time metadata rendered into the HTML header (FR-017, FR-018).
- **Fields** (from `config.toml`):
  - `paper_title` (string, required literal): link text for the paper anchor.
  - `paper_url` (string, required literal): expected `https://arxiv.org/abs/2603.21852`.
  - `video_title` (string, optional literal): link text for the video anchor; substitutes as an empty string when absent.
  - `video_url` (string, optional literal): configured video URL; substitutes as an empty string when absent.
- **Page-top literal fields** (from the owner-authored root `top_fragment.html`, not from config or Python constants): H1, summary paragraph, "References" heading, and Article/Video label markup. The separate fixed citation paragraph is removed (see entity 9).
- **Validation rules**:
  - Titles and URLs are literals read from config, not constructed/fetched (FR-018); `paper_title` is a plain string and may contain the author name and article title, with no fixed sample literal required.
  - Optional video values MAY be absent; they substitute as empty strings with no generation error and no renderer-side row omission. The owner-authored fragment controls the rendered rows.
  - Page contains no other anchors (FR-017, SC-007).

### 9. Top Fragment (owner-authored HTML)
- **Description**: Source-controlled root file that owns the literal page-top header content (FR-017, FR-018).
- **Fields**:
  - `path` (string): deterministic default `./top_fragment.html` at the repository root.
  - `h1` / `summary` / `references_heading` / `article_label` / `video_label` (literal HTML markup): supplied by the project owner; inserted as supplied.
- **Validation rules**:
  - Must be present and readable at generation time; missing or unreadable is a user-facing generation error (FR-018, FR-021, exit `2`).
  - Not generated per expression, not paraphrased by the implementation, not fetched at runtime; inserted as literal markup with no added styling of config link text (in particular no `<em>` around `paper_title`).
  - Only article/video link text and hrefs are filled from `config.toml`; no other content is altered and no renderer-added anchors are introduced (FR-017, SC-007).
- **Relationships**: Supplies the page-top H1, summary, "References" heading, and Article/Video label rows above the tree; `config.toml` supplies the four link literals used inside the Article/Video rows.

## Relationships Summary

- Input Expression → (parse) → Source Expression Structure → (rewrite via `constructions.py`) → EML Tree.
- EML Tree → contains many Tree Nodes (binary hierarchy) → each has an Evaluation Result.
- Failed Evaluation Results → Failure Summary (every failing node, ancestors `undefined`) → text/HTML failure reporting.
- Owner-authored `top_fragment.html` (H1/summary/References/labels) + config (link titles/URLs only) + EML Tree + Evaluation Results + Failure Summary → deterministic text output and `out.html`.
- Validation Corpus → exercises parse/rewrite/evaluate/report pipeline in tests.

## Invariants

- Output expression alphabet is only `eml` and `1` (FR-003).
- Node count is total nodes and identical in text and HTML (FR-010, SC-004).
- Same expression + same config + same `top_fragment.html` => byte-identical `out.html` (Principle VII).
- Node values are precomputed; native `title` supports hover and CSS-only `:focus` reveals the same value with no JavaScript (FR-009).
- A value is displayed as real exactly when `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))`, with both constants defined once (FR-014, Principle VI).
- Every failing node is visibly marked with its reason; all failures appear in the summary; ancestors of failures are marked `undefined` (FR-012).
- No user-visible `nan`/`inf`; failures are specific and node-attributed (FR-012, FR-013).