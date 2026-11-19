# Contract: HTML Output (`out.html`)

**Last updated**: 2026-11-19 (fragment-driven header order; only link titles/URLs from config)

## Purpose
Defines the structure and guarantees for the single, self-contained generated HTML file.

## File properties
- **Name/path**: `out.html` (written/overwritten deterministically; default cwd).
- **Self-contained**: all markup and styling inline in the one file.
- **No JavaScript**: page MUST NOT contain `<script>` or executable JS.
- **No network**: no external resource fetches (no remote CSS/JS/fonts/images/iframes required for correctness).
- **Deterministic**: same expression, same config, and same `top_fragment.html` produce byte-identical output (stable ordering, escaping, whitespace/indentation, and value formatting).

## Required content and order (above the tree)

The page-top header is fragment-driven, in this order (FR-017):

1. **H1** — literal heading content from the source-controlled root `top_fragment.html`.
2. **Summary paragraph** — literal summary text from `top_fragment.html`.
3. **"References" heading** — literal heading content from `top_fragment.html`.
4. **Article row** — label markup from `top_fragment.html`; the anchor has `href` = configured `paper_url` and link text = configured `paper_title` as a plain string. `paper_title` may contain the author name and article title; the renderer MUST NOT wrap it in `<em>` or other styling.
5. **Video row** — label markup from `top_fragment.html`; the anchor's `href` and link text are substituted from `video_url` and `video_title`. When either value is absent, an empty string is substituted; the renderer neither omits the row nor raises an error. The owner-authored fragment controls what is rendered.

Literal H1, summary, and label content comes from `top_fragment.html`, a source-controlled root file read at generation time. Only link titles and URLs come from `config.toml`; the separate fixed citation paragraph is removed. A missing or unreadable `top_fragment.html` is a user-facing generation error (FR-017, FR-018, FR-021).

## Fragment substitution
- The fragment uses exactly four lowercase double-brace tokens: `{{paper_title}}`, `{{paper_url}}`, `{{video_title}}`, `{{video_url}}`.
- Substitution is literal string replacement, not `str.format`; single braces in the fragment (e.g., inline CSS `body { ... }`) are preserved and need no escaping.
- All four tokens are always substituted: config values for the paper keys, config value or `""` for the video keys. All other fragment bytes are unchanged.
- Values are HTML-escaped before substitution (`quote=True` for href attributes).

Below the fragment-driven header and still above the tree:

6. **Source expression**: displayed exactly as supplied (FR-019).
7. **Evaluated value**: precomputed value for the source/root; when it cannot be evaluated, the **failure summary** appears in place of the value (FR-019).

No renderer-added anchors may appear anywhere in the document; the page's anchors are exactly those supplied by `top_fragment.html` (FR-017, SC-007).

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
- The owner-authored `top_fragment.html` markup (H1, summary, "References" heading, Article/Video labels) is inserted as supplied; only link titles/URLs and other dynamic strings are escaped. The fragment is not generated, paraphrased, or fetched at runtime.
- Structural presentation (indentation/connecting layout, focus reveal) is achieved with HTML/CSS only; no JavaScript, no network requests.