# Feature Specification: EML Expression Translator

**Feature Branch**: `[001-eml-expression-translator]`  
**Created**: 2026-11-16  
**Status**: Draft  
**Input**: User description: "Translate arithmetic expressions into equivalent eml/1 binary trees, show text and browser tree views, evaluate nodes with hover/focus values, report node counts, and surface domain/evaluation failures per node based on Odrzywołek, All elementary functions from a single binary operator (arXiv:2603.21852v2)."

## Clarifications

### Session 2026-11-16

- Q: Should the command line accept free variables such as `x` in an expression, or only closed expressions with no variables? (FR-002) → A: Closed input only; reject free variables, and use sample ranges only in internal construction-verification tests.

### Session 2026-11-17

- Q: Should each node's value be available on keyboard focus as well as on mouse hover? (FR-009) → A: Hover and keyboard focus; focusable nodes keep native `title` for hover and reveal the precomputed value on focus with CSS only.
- Q: How should the page identify which nodes failed and which failure reasons to show? (FR-012, SC-006) → A: Visibly mark every failing node with its reason in addition to its native `title`, list all failures in a summary, and mark ancestor nodes `undefined` so the deepest specific reason stays attributable.
- Q: Which numeric literal formats must the parser accept in an expression? (FR-002) → A: Decimal integers and decimals with an optional exponent (for example `2`, `2.5`, `.5`, `1e-3`); hexadecimal, binary, and underscore-separated forms are rejected.
- Q: When should a complex node value be displayed as a real number instead of keeping its imaginary part? (FR-014) → A: Display as real when `|imag| <= max(1e-12, ε × max(1, |real|))`, with the absolute floor and `ε` defined once as shared constants.

### Session 2026-11-17 (artifact corrections)
- Q: Should the link titles be configurable with the URLs in `config.toml`? (FR-017, FR-018) → A: Yes. Both anchors' titles and URLs are literals in config, read at generation time. The citation text and explanation remain fixed in source.
- Q: Should a negative right child of `eml` be a domain failure under complex evaluation? (FR-011, FR-012) → A: No. `cmath.log` is defined for negative arguments; only a zero right child is an `undefined` failure. `non-positive operand` is removed from the reason vocabulary.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Translate an expression to eml/1 form (Priority: P1)

As a curious reader or reviewer, I can enter an arithmetic expression and receive an equivalent expression built only from `eml` and `1`, so I can see that the reduction is real.

**Why this priority**: This is the core value of the feature; without a correct translation there is nothing meaningful to inspect.

**Independent Test**: Enter a supported expression such as `1+1` and verify that the result is an `eml`/`1` expression whose evaluated root value matches the original expression.

**Acceptance Scenarios**:

1. **Given** the translator is ready for input, **When** a user enters `1+1`, **Then** the system produces an equivalent expression composed only of `eml` nodes and `1` leaves.
2. **Given** a supported expression using accepted operators or functions, **When** the user submits it, **Then** the translated result evaluates to the same value as the original expression within the stated tolerance.
3. **Given** an expression that requires composition of tabulated constructions, **When** it is translated, **Then** the output remains in valid `eml`/`1` form.

---

### User Story 2 - Inspect the generated tree structure (Priority: P2)

As a user, I can read the result as an indented text tree and as a rendered browser tree, so I can understand the nesting without counting parentheses.

**Why this priority**: The translation’s educational value depends on making the generated structure observable and navigable.

**Independent Test**: Translate `1+1` and confirm the text tree and rendered tree show the same node structure and that the reported node count matches both.

**Acceptance Scenarios**:

1. **Given** a translated expression, **When** the result is shown, **Then** the text form places one node per line with `eml(` opening a node, its two children indented beneath it, `)` closing it, and leaves shown as `1`.
2. **Given** the same translated expression, **When** the browser view is shown, **Then** it renders the same structure with one node per `eml` and one leaf per `1`.
3. **Given** the `1+1` translation, **When** both representations are compared, **Then** they contain the same nodes in the same structure.

---

### User Story 3 - Inspect node values and understand failures (Priority: P3)

As a user, I can hover or focus any node to see the value it resolves to, see the total node count, and receive specific per-node reasons for invalid or failing evaluations, so I can locate where a translation goes wrong or becomes too large.

**Why this priority**: Node-level feedback turns a static curiosity into a diagnostic tool and prevents silent incorrect results.

**Independent Test**: Translate a valid expression and inspect node hover/focus values and node count; separately submit expressions with domain or evaluation problems and verify each reports a specific, non-crashing failure at the correct node.

**Acceptance Scenarios**:

1. **Given** a translated tree, **When** a user hovers or focuses a node, **Then** the system displays that node’s evaluated value.
2. **Given** a translated tree, **When** it is displayed, **Then** the system shows the total node count for the generated tree.
3. **Given** an expression whose evaluation violates a required domain condition (including a zero value for the right child of an `eml` node), **When** translation or evaluation is performed, **Then** the system visibly marks the failing node with a specific reason instead of showing `nan`.
4. **Given** an expression that overflows or becomes undefined during evaluation, **When** the failure occurs, **Then** the system visibly marks every failing node and its reason, lists the failures in a summary, and does not crash or silently show `nan` or `inf`.

---

### User Story 4 - Verify the claim from the page itself (Priority: P3)

As a reviewer, I can reach the paper and the video from the page itself, so I can check the claim without taking the page's word for it.

**Why this priority**: The page will be opened by someone who has not read the brief. Without the source and a sentence of framing, the tree is an unexplained diagram.

**Independent Test**: Generate the page and confirm the citation, the paper anchor, the video anchor, and the explanation all appear above the tree, with the hrefs and link text specified in config.

**Acceptance Scenarios**:

1. **Given** a generated page, **When** it is opened, **Then** the citation appears above the tree, worded as specified.
2. **Given** a generated page, **When** it is opened, **Then** an anchor with the configured paper title points to the configured paper URL and, when a video URL is configured, an anchor with the configured video title points to it.
3. **Given** a generated page, **When** it is opened, **Then** two or three sentences below the citation explain what the tree is and that hovering a node shows its value.
4. **Given** no video URL is configured, **When** the page is generated, **Then** the video anchor is absent and no placeholder text is visible.

---

### Edge Cases

- A negative argument to `ln` is evaluated in complex form (for example, `ln(-1)` is `iπ`) and remains a representable value, not a failure.
- Division by zero is reported at the correct node with a specific non-crashing reason.
- A negative base raised to a fractional power is evaluated in complex form using the principal branch, with its imaginary part displayed when meaningful.
- A tree deep or large enough to overflow standard floating-point evaluation reports overflow at the specific node without crashing and without silent `nan` or `inf`.
- Numeric literals other than `1` in the input are accepted for parsing but must be represented in the output only through `eml`/`1` constructions.
- Every right child of every `eml` node must evaluate to a non-zero value; a zero right child is a node-level `undefined` failure. Negative and complex right children are valid.
- Values with negligible imaginary part are displayed as real; values with meaningful imaginary parts remain representable.
- Expressions outside the supported operator/function set are rejected with a clear, user-facing error that identifies the unsupported element.
- An unknown named constant (for example `tau` or `phi`) is rejected with a clear, user-facing error that names the constant, rather than failing as a parse error or being treated as an implicit variable.
- A free variable (for example `x`) is rejected with a clear, user-facing error; it is not assigned a sample value or treated as an implicit constant.
- Very large generated trees remain structurally inspectable in both text and rendered forms; node-level failure reporting remains specific even when evaluation cannot complete normally.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a single arithmetic expression as a command-line argument and parse it into an internal expression structure. No other input mechanism exists: the rendered page contains no input element.
- **FR-002**: The parser MUST support numeric literals, parentheses, unary minus, binary operators `+`, `-`, `*`, `/`, `^`, the functions `exp`, `ln`, `sqrt`, `sin`, `cos`, and `tan`, and the named constants `pi` and `e`. Named constants are input-only: in the output form they MUST be expanded into `1` leaves like every other value. Numeric literals MUST be decimal integers or decimals with an optional exponent (for example `2`, `2.5`, `.5`, `1e-3`); hexadecimal, binary, and underscore-separated forms are rejected. The input grammar is closed: free variables (for example `x`) and any other identifiers MUST be rejected with a clear, user-facing error.
- **FR-003**: The system MUST rewrite supported parsed expressions into equivalent expressions whose only operator is `eml` and whose only constant leaf is `1`.
- **FR-004**: The rewrite MUST use the constructions tabulated in the Supplementary Information of Andrzej Odrzywołek, *All elementary functions from a single binary operator* (arXiv:2603.21852v2, submitted 23 Mar 2026, revised 4 Apr 2026) as the authoritative source for directly tabulated forms.
- **FR-005**: The system MUST obtain constructions not tabulated directly by composing tabulated constructions, preserving equivalence to the source expression.
- **FR-006**: The system MUST emit the rewritten expression as indented text with one node per line, where `eml(` opens a node, its two children are indented beneath it, `)` closes it, and each leaf is `1`.
- **FR-007**: The system MUST render the same rewritten expression in a browser as a tree with one node per `eml` and one leaf per `1`.
- **FR-008**: The system MUST evaluate every node in the rewritten tree and ensure the root value equals the source expression’s value within the stated tolerance for valid inputs.
- **FR-009**: The system MUST make each rendered node keyboard-focusable and MUST display that node's precomputed evaluated value on hover and on focus, without requiring JavaScript.
- **FR-010**: The system MUST display the total node count of the generated tree, counting every `eml` node and every `1` leaf, and keep that count consistent with both the text and rendered representations.
- **FR-011**: The system MUST enforce the domain rule that every right child of every `eml` node evaluates to a non-zero value. A zero right child MUST be reported as a node-level `undefined` failure; negative and complex right children MUST be evaluated normally.
- **FR-012**: When one or more node-level evaluation or domain problems occur, the system MUST visibly mark every failing node in the rendered tree with its reason from `overflow` or `undefined`, expose the same reason on hover or focus, and list every failing node and its reason in a summary. An ancestor of a failed node MUST be marked failed with reason `undefined` unless it has its own more specific failure reason.
- **FR-013**: The system MUST not crash and MUST not silently present `nan` or `inf` for any supported error case; failures must be explicit and attributable.
- **FR-014**: The system MUST evaluate expressions over complex numbers and display a value as real when `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))`, where `IMAG_ABS_FLOOR` and `ε` are shared constants; values with a meaningful imaginary part MUST remain representable in complex form.
- **FR-015**: The delivered user experience MUST be limited to one tree result view with node hover/focus value inspection. The page contains no input element, no form, no navigation, and no UI framework; the expression is supplied before the page is rendered.
- **FR-016**: The system MUST produce *a* valid equivalent tree for each supported expression; it MUST NOT attempt to minimize tree size or select a smallest representation.
- **FR-017**: Above the tree, the page MUST contain, in order: the citation text "Odrzywołek, *All elementary functions from a single binary operator*, arXiv:2603.21852v2"; an anchor whose href is the configured paper URL and whose link text is the configured paper title; an anchor whose href is the configured video URL and whose link text is the configured video title, only when a video URL is configured; and two to three sentences explaining what the tree is and that hovering a node shows its value. The page MUST contain no other anchors.
- **FR-018**: The URLs and link titles required by FR-017 MUST be literals in a source-controlled configuration file read at generation time. They MUST NOT be constructed at runtime or fetched over the network. If the configuration file omits the video URL, the video anchor and its title MUST be omitted entirely rather than rendered with a placeholder or an empty href.
- **FR-019**: Below the citation block and above the tree, the page MUST display the source expression exactly as supplied and its evaluated value. If the source expression cannot be evaluated, the failure summary required by FR-012 MUST appear in place of the value. Neither is recomputed in the browser.
- **FR-020**: The rendered page MUST contain exactly one element per node of the generated tree, including nodes inside collapsed sections. Depth is a presentation concern only: no node may be omitted, truncated, or summarized away.
- **FR-021**: Exit status MUST be `0` when the root evaluates, `1` when a node-level failure prevents a root value while the tree was still generated and written, and `2` when the input cannot be parsed or uses an unsupported element.

### Key Entities *(include if feature involves data)*

- **Input Expression**: The user-provided arithmetic expression, including supported literals, operators, functions, and grouping.
- **Source Expression Structure**: The parsed representation of the input expression before translation into `eml`/`1` form.
- **EML Tree**: The rewritten expression represented as a binary tree where internal nodes are `eml(x, y)` and leaves are `1`.
- **Tree Node**: A single node in the EML tree with position, child relationships (if any), evaluated value or failure state, and display information.
- **Evaluation Result**: The outcome for a node or whole tree, including numeric/complex value, display form, and any domain or evaluation failure reason.
- **Validation Corpus**: A fixed set of approximately 30 closed expressions, including required failure cases, used to verify equivalence and failure reporting. A separate shared sample range is used only for internal construction-verification checks.

### Assumptions

- The source paper’s Supplementary Information provides complete constructions needed for the supported operator/function set in this feature.
- The command line accepts only closed expressions; free variables are out of scope. Internal equivalence checks of tabulated constructions use a shared, explicit sample range for the construction input variable and the relative tolerance `ε`.
- Operator precedence and associativity follow standard mathematical convention: `^` binds more tightly than unary minus and `*`/`/`, which bind more tightly than `+`/`-`; `^` is right-associative.
- “Negligible imaginary part” means `|imag| <= max(IMAG_ABS_FLOOR, ε × max(1, |real|))`, where `IMAG_ABS_FLOOR` has the shared default `1e-12` and `ε` is the shared relative tolerance.
- A supported expression that cannot be evaluated successfully is still translated when structurally possible, so the failure can be reported at the relevant node; if translation itself is impossible due to unsupported syntax, the user receives a clear input error.
- The browser experience is intended for immediate inspection by a single user in one session, without saving, sharing, accounts, or export.
- The citation text and explanation required by FR-017 are fixed text written once in the source; the two anchors' titles and URLs are literals in `config.toml`. Neither is generated per expression or paraphrased by the implementation.
- The video title and URL in FR-018 are supplied by the project owner and configured in `config.toml`. If they are omitted, the anchor is omitted, which is a valid rendered state and not a defect.

### Dependencies

- Access to the constructions tabulated in the Supplementary Information of arXiv:2603.21852v2.
- A fixed validation corpus of approximately 30 closed expressions with expected outcomes and tolerance `ε`, plus a shared sample range for internal construction-verification checks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every closed expression in a fixed corpus of approximately 30 expressions, the generated tree’s root value matches the source expression’s value within relative tolerance `ε`. Internal construction-verification checks additionally cover the shared sample range for the construction input variable.
- **SC-002**: The corpus includes, at minimum, division by zero, an `eml` node whose right child evaluates to zero, and a tree deep enough to overflow standard floating-point evaluation; each case produces a specific, non-crashing failure identified at the correct node. It also includes a case exercising a negative right child (π via `ln(-1)`) as a successful complex evaluation.
- **SC-003**: 100% of expressions in the validation corpus complete without silently producing `nan` or `inf`.
- **SC-004**: For `1+1`, reviewers can confirm that the text tree and rendered tree contain the same nodes in the same structure, and the reported node count matches both representations.
- **SC-005**: A first-time reviewer can enter one supported expression, see the translated tree, and inspect at least one node value within 10 seconds of landing on the experience.
- **SC-006**: For each supported failure case in the corpus, users can identify every failing node and its reason from visible node markers and the failure summary on the page, without consulting logs or external diagnostics.
- **SC-007**: The generated page contains exactly the anchors named in FR-017, each with the href and link text from the configuration, and no others. With no video URL configured, it contains only the paper anchor and shows no placeholder text.
- **SC-008**: For any supported expression, the page shows the expression as supplied and its value, and both match what the command line reported.
- **SC-009**: Every run exits with the documented status for its outcome: `0` for a computed root value, `1` for a generated tree containing a node-level failure, `2` for rejected input. No run exits `0` while reporting a failure.
