# Contract: HTML Output (`out.html`)

**Last updated**: 2026-11-17 (clarified focus reveal, visible failure reporting, and real-display rule)

## Purpose
Defines the structure and guarantees for the single, self-contained generated HTML file.

## File properties
- **Name/path**: `out.html` (written/overwritten deterministically; default cwd).
- **Self-contained**: all markup and styling inline in the one file.
- **No JavaScript**: page MUST NOT contain `<script>` or executable JS.
- **No network**: no external resource fetches (no remote CSS/JS/fonts/images/iframes required for correctness).
- **Deterministic**: same expression and same config produce byte-identical output (stable ordering, escaping, whitespace/indentation, and value formatting).

## Required content and order (above the tree)
1. **Citation text** (fixed): `Odrzywołek, *All elementary functions from a single binary operator*, arXiv:2603.21852v2`.
2. **Paper anchor**: `<a href="{paper_url}">{paper_title}</a>` (both from config literals).
3. **Video anchor** (conditional): `<a href="{video_url}">{video_title}</a>` only when `video_url` and `video_title` are configured; omitted entirely otherwise with no placeholder/empty href.
4. **Explanation**: 2–3 fixed sentences explaining what the tree is and that hovering a node shows its value.
5. **Source expression**: displayed exactly as supplied (FR-019).
6. **Evaluated value**: precomputed value for the source/root; when it cannot be evaluated, the **failure summary** appears in place of the value (FR-019).

No other anchors may appear anywhere in the document (FR-017, SC-007).

## Tree rendering
- Renders the same rewritten `eml`/`1` structure as the text form: one node per `eml`, one leaf per `1` (FR-007).
- **Every node present**: exactly one element per node of the tree, including nodes inside collapsed sections (FR-020). Deep trees are made navigable with native `<details>`/`<summary>` around subtrees, with the outermost levels open by default. This requires no JavaScript and changes no node.
- **Node values baked in**: every node keeps its precomputed evaluated value or explicit failure reason in a native `title` attribute for mouse hover, and is keyboard-focusable so the same precomputed value is revealed on `:focus` using CSS only (FR-009). The page contains no JavaScript and performs no recomputation.
- **Node count**: total node count is displayed and consistent with the text and rendered representations (FR-010, SC-004).
- **Failures**: every failing node is visibly marked in the tree with its specific reason (`overflow`, `undefined`; a zero right child is `undefined`) in addition to its native `title`; a failure summary lists every failing node and reason; every ancestor of a failed node is marked `undefined` unless it has its own more specific reason, so the deepest specific reason stays attributable. No node is silently shown as `nan`/`inf` (FR-012, FR-013, SC-006).
- **Accessibility/semantics**: use semantic, readable markup (lists/nested elements or equivalent) so structure is inspectable without JS; titled nodes use native focusability (e.g. `tabindex="0"`) and a CSS-only focus rule to reveal the baked-in value, with no script and no network access.

## Formatting rules
- A value is displayed as real exactly when `abs(imag) <= max(IMAG_ABS_FLOOR, ε × max(1, abs(real)))`, where `IMAG_ABS_FLOOR = 1e-12` and `ε` are shared constants defined once in `constants.py`; values with a meaningful imaginary part remain representable in complex form (FR-014, Principle VI).
- HTML-escape all dynamic/user-derived strings (expression, values, config link titles, node `title` values, visible failure markers, summary messages) to preserve structure and safety.
- Structural presentation (indentation/connecting layout, focus reveal) is achieved with HTML/CSS only; no JavaScript, no network requests.