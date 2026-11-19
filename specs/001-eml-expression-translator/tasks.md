---

description: "Task list for EML Expression Translator implementation"
---

# Tasks: EML Expression Translator

**Input**: Design documents from `/specs/001-eml-expression-translator/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md, `.specify/memory/constitution.md`

**Tests**: Test tasks are included because plan.md ("Testing: `pytest` ... fixed validation corpus") and the project constitution (Principle III — unit tests for pure transformations, integration tests at boundaries) require them, and the validation corpus is itself a spec requirement (SC-001–SC-003). `pytest` is a test-only dependency; runtime code remains standard-library only. Write tests first and confirm they fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single-project CLI at repository root per plan.md:
- Root-owned inputs: `constructions.py` (authoritative construction table), `config.toml` (link metadata), `decisions.md` (drift log)
- Package: `eml_calculator/` — `constants.py`, `parser.py`, `rewrite.py`, `evaluate.py`, `render_text.py`, `render_html.py`, `corpus.py`, `cli.py`, `__main__.py`, `__init__.py`
- Tests: `tests/unit/` (pure transforms), `tests/integration/` (boundaries/CLI/corpus)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md: `eml_calculator/`, `tests/unit/`, `tests/integration/` at repository root, plus root `requirements-dev.txt` containing `pytest` (test-only dependency; runtime code stays standard-library only)
- [X] T002 Create `eml_calculator/__init__.py` package marker with a short module docstring for the EML expression translator package
- [X] T003 [P] IGNORE; superseded by Phase 8; config file already created and video keys are no longer used to check against video anchor. Create root `config.toml` per `contracts/config.toml.md` with literal `paper_title = "the paper"`, `paper_url = "https://arxiv.org/abs/2603.21852"`, `video_title = "the video"`, and `video_url = "https://www.youtube.com/watch?v=LxVW3b8jVdE"` (omit both video keys to suppress the anchor)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `eml_calculator/constants.py` as the single source for all shared numbers (Constitution VI): `REL_TOL_EPSILON = 1e-9` (equivalence tolerance ε), `IMAG_ABS_FLOOR = 1e-12`, `MAX_NODE_EVAL_DEPTH` and overflow guard limits, `DEFAULT_FREE_VAR_SAMPLES`/sample-range descriptors for internal construction verification only, and deterministic default paths for `config.toml` and `out.html`; document the real-display predicate verbatim: `abs(imag) <= max(IMAG_ABS_FLOOR, ε × max(1, abs(real)))`
- [X] T005 [P] Create root `constructions.py` as the authoritative `eml` construction table: plain functions ported from `EML_toolkit/EmL_compiler` in `VA00/SymbolicRegressionPackage` (MIT, DOI 10.5281/zenodo.19183008), verified against the Supplementary Information of arXiv:2603.21852v2; cover literals, unary minus, `+ - * / ^`, `exp ln sqrt sin cos tan`, `pi`, `e`, and `i` (`i` is an internal imaginary-unit construction only — not a user input per FR-002); do not re-derive formulas inline at call sites or in tests (Constitution V); where table and paper disagree, the paper wins and a note is recorded in `decisions.md`
- [X] T006 [P] Define the immutable tree model in `eml_calculator/rewrite.py` per `data-model.md`: `TreeNode` with fields `kind` (`eml` | `leaf_one`), `id/index`, `left`/`right`, and `display_label` (`eml` or `1`) only — no evaluation fields; `EMLTree` with structural fields `root`, `node_count`, `source_text` and an initially empty `evaluations` mapping (node id → Evaluation Result) that evaluation fills by returning a new tree, not by mutating the input. Also define the `EvaluationResult` and `FailureSummary` types in `eml_calculator/evaluate.py` per `data-model.md` (types only, no evaluation logic). Each `eml` node has exactly two children and each leaf is the constant `1`
- [X] T007 Create `eml_calculator/corpus.py` with a fixed validation corpus of ~30 closed expressions as data (kind `equivalence` | `failure`, expected outcomes, optional named sample range, notes), including `1+1`, division by zero, an `eml` node whose right child evaluates to zero, a tree deep enough to overflow floating-point evaluation, and a successful complex case using a negative right child (π via `ln(-1)`); import `REL_TOL_EPSILON` and sample ranges from `eml_calculator/constants.py` and define no formulas (FR-002, SC-001–SC-003)
- [X] T008 [P] Implement `load_page_config()` in `eml_calculator/cli.py` using `tomllib` to read root `config.toml` and return literal `paper_title`/`paper_url` plus optional `video_title`/`video_url`; raise a clear user-facing generation error for missing/unreadable config, invalid TOML, or missing required `paper_title`/`paper_url` (`contracts/config.toml.md`); absent optional video keys are not an error

**Checkpoint**: Foundation ready — shared constants, construction table, tree model, corpus data, and config loading exist; user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Translate an expression to eml/1 form (Priority: P1) 🎯 MVP

**Goal**: Enter a supported arithmetic expression and receive an equivalent expression built only from `eml` and `1`, with a verified root value.

**Independent Test**: Enter `1+1` and verify the result is an `eml`/`1` expression whose evaluated root value matches the original expression; equivalently test at library level that `parse → rewrite → evaluate` yields only `eml`/`1` and a root equal to the source within `REL_TOL_EPSILON`.

### Tests for User Story 1 (mandated by plan.md and Constitution III)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Write tokenizer/parser unit tests in `tests/unit/test_parser.py` for decimal integers and decimals with optional exponent (`2`, `2.5`, `.5`, `1e-3`), parentheses, unary minus, binary `+ - * / ^`, functions `exp ln sqrt sin cos tan`, constants `pi`/`e`, precedence (`^` right-associative and tighter than unary minus), and rejection with clear errors of `0x10`, `0b10`, `1_000`, free variables (`x`), unknown constants (`tau`, `phi`), and unsupported elements
- [X] T010 [P] [US1] Write rewriter unit tests in `tests/unit/test_rewrite.py` asserting output alphabet is only `eml` and `1` (FR-003), named constants and non-`1` literals expand to `1` leaves, composed constructions remain valid `eml`/`1` form, and no formulas are inlined outside `constructions.py` (Constitution V)
- [X] T011 [P] [US1] Write evaluation/equivalence unit tests in `tests/unit/test_evaluate.py` asserting root value matches source within `REL_TOL_EPSILON` for corpus expressions and over `DEFAULT_FREE_VAR_SAMPLES`, and that `1+1` evaluates to `2` within tolerance
- [X] T012 [P] [US1] Write CLI success-path integration test in `tests/integration/test_cli.py` (mock only `webbrowser.open`) asserting exit code `0`, printed indented text tree and summary (source expression, value, node count), and creation/overwrite of `out.html`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement the hand-written tokenizer and recursive-descent parser in `eml_calculator/parser.py` producing a Source Expression Structure with `kind`, `children`, `token/value`, and optional `span`; numeric literals are decimal integers and decimals with an optional exponent (`2`, `2.5`, `.5`, `1e-3`); hexadecimal, binary, and underscore-separated forms are rejected with a clear input error; the grammar is closed — free variables (e.g. `x`) and any other identifiers are rejected with a clear input error, never assigned a sample value; unknown named constants (`tau`, `phi`) produce a clear error naming the constant; unsupported operators/functions/identifiers produce a clear error naming the element; no `ast.literal_eval`
- [X] T014 [US1] Implement `rewrite(source) -> EMLTree` in `eml_calculator/rewrite.py` using only functions from root `constructions.py` (directly tabulated forms plus compositions of tabulated forms), expanding every literal and named constant into `1` leaves, assigning deterministic pre-order node indices and `node_count`; produce *a* valid equivalent tree with no minimization and no inline formulas (FR-003–FR-005, FR-016)
- [X] T015 [US1] Implement the single complex-number evaluation pass in `eml_calculator/evaluate.py` (`evaluate_source`, `evaluate_tree`) using the types from T006: compute each node once with children before parents using `cmath` and return a new `EMLTree` with the same structure and `evaluations` keyed by node id (do not mutate the input tree); enforce that for `kind=eml` the evaluated value of `right` must be non-zero (a zero right child is a node-level `undefined` failure per FR-011; negative and complex right children evaluate normally), treat non-finite results as failures rather than silent `nan`/`inf`, and expose root values for equivalence comparison within `REL_TOL_EPSILON`. No later task implements a second evaluator.
- [X] T016 [US1] Implement the CLI entry point in `eml_calculator/cli.py` and `eml_calculator/__main__.py`: `argparse` with exactly one positional expression argument, orchestration `parse → rewrite → evaluate → render`, deterministic stdout of indented text tree plus summary (source expression as supplied, root value, total node count), write `out.html`, attempt `webbrowser.open` on its path, and return exit status `0`/`1`/`2` per `contracts/cli.md`
- [X] T017 [US1] Add initial structural renderers in `eml_calculator/render_text.py` and `eml_calculator/render_html.py` so the MVP CLI emits an indented text tree and a self-contained `out.html` with one element per `eml` and one per `1` leaf (enhanced in later stories)

**Checkpoint**: User Story 1 is fully functional and testable independently — `python -m eml_calculator "1+1"` produces an `eml`/`1` tree equivalent to the source (MVP).

---

## Phase 4: User Story 2 - Inspect the generated tree structure (Priority: P2)

**Goal**: Read the result as an indented text tree and a rendered browser tree that show the same node structure and a consistent total node count.

**Independent Test**: Translate `1+1` and confirm the text tree and rendered tree show the same nodes in the same structure and the reported node count matches both (SC-004).

### Tests for User Story 2 (mandated by plan.md and Constitution III)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T018 [P] [US2] Write unit tests in `tests/unit/test_render_text.py` asserting one node per line, `eml(` opening a node, its two children indented beneath it, `)` closing it, and leaves shown as `1` (FR-006)
- [X] T019 [P] [US2] Write unit tests in `tests/unit/test_render_html.py` asserting the rendered tree mirrors the text structure with one node per `eml` and one leaf per `1`, exactly one element per tree node including nodes inside `<details>` sections, and no node omitted/truncated/summarized away (FR-007, FR-020)

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `render_text(tree)` in `eml_calculator/render_text.py`: deterministic, stable-traversal indented output with `eml(`/`)` and `1` leaves, one node per line, matching the tree pre-order used for node indices
- [X] T021 [P] [US2] Implement the structural HTML tree in `eml_calculator/render_html.py`: nested semantic markup with one element per `eml` and one per `1`, native `<details>`/`<summary>` wrapping deep subtrees with the outermost levels open by default, no JavaScript, and no node elided (FR-007, FR-020)
- [X] T022 [US2] Display the total node count (every `eml` node and every `1` leaf) in the CLI summary (`eml_calculator/cli.py`) and in `out.html` (`eml_calculator/render_html.py`), keeping it identical across text and rendered representations (FR-010, SC-004)
- [X] T023 [US2] Add an integration assertion in `tests/integration/test_cli.py` that for `1+1` the text tree nodes, HTML tree nodes, and reported node count all match (SC-004)

**Checkpoint**: User Stories 1 AND 2 both work independently; text and browser views are structurally identical with a consistent node count.

---

## Phase 5: User Story 3 - Inspect node values and understand failures (Priority: P3)

**Goal**: Hover/focus any node to see its precomputed value, see the node count, and receive specific per-node reasons for invalid or failing evaluations without crashes or silent `nan`/`inf`.

**Independent Test**: Translate a valid expression and inspect node hover/focus values and node count; separately submit the required failure cases and verify each reports a specific, node-attributed, non-crashing failure with visible markers and a summary (SC-002, SC-003, SC-006).

### Tests for User Story 3 (mandated by plan.md and Constitution III)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US3] Extend `tests/unit/test_evaluate.py` with failure-taxonomy tests: `undefined` when an `eml` right child is zero, `undefined` for division by zero, `overflow` for non-finite results, successful complex evaluation for negative right children (`ln(-1) = iπ`) and negative bases raised to fractional powers, ancestors of failed nodes marked `undefined` unless they have a more specific reason, no `nan`/`inf` surfaced, and `display_as_real` exactly when `abs(imag) <= max(IMAG_ABS_FLOOR, ε × max(1, abs(real)))` using shared constants only
- [X] T025 [P] [US3] Extend `tests/unit/test_render_html.py` asserting every node carries its precomputed value in a native `title`, is keyboard-focusable (`tabindex="0"`) with a CSS-only `:focus` reveal of the same value, has no `<script>`/JS, shows a visible failure marker with the exact reason text for failed nodes, and includes a summary listing every failing node and reason
- [X] T026 [P] [US3] Create `tests/integration/test_corpus.py` running all ~30 corpus cases end-to-end: equivalence within `REL_TOL_EPSILON` for valid cases, correct node-attributed reasons for each required failure case, no crashes, and no silent `nan`/`inf` (SC-001–SC-003, SC-006)

### Implementation for User Story 3

- [X] T027 [US3] Extend the T015 evaluator **in place** in `eml_calculator/evaluate.py`: mark ancestors of a failed node with reason `undefined` unless they have their own more specific reason, preserving attribution of the deepest specific reason (FR-012), and assemble `FailureSummary` from the evaluated tree's existing `EMLTree.evaluations`; do not recompute node values or introduce a second evaluator. Use depth/overflow guards from `constants.py` and never surface `nan`/`inf` (FR-013).
- [X] T028 [US3] Add a complex-to-real formatting helper in `eml_calculator/evaluate.py` where `display_as_real` is true exactly when `abs(imag) <= max(IMAG_ABS_FLOOR, ε × max(1, abs(real)))`, where `IMAG_ABS_FLOOR = 1e-12` and `ε` are shared constants from `constants.py`; meaningful imaginary parts remain representable in complex form; no threshold is retyped in the formatter or tests (FR-014, Principle VI)
- [X] T029 [US3] Bake node values and failure states into `eml_calculator/render_html.py`: native `title` on every node, `tabindex="0"` and a CSS-only `:focus` rule revealing the precomputed value, visible failure markers with exact reason text in the tree, and a failure summary listing every failing node and reason with ancestors `undefined`; no JavaScript, no recomputation, and all dynamic strings HTML-escaped (FR-009, FR-012, FR-013)
- [X] T030 [US3] Implement the exit-code `1` path in `eml_calculator/cli.py`: when the tree is generated but a node-level failure prevents a root value, still write `out.html` with failures baked in, print the text tree and failure summary, and return `1`; a run MUST NOT exit `0` while reporting a failure (FR-021, SC-009)

**Checkpoint**: All user stories are independently functional; node values are inspectable on hover/focus, every failing node is visible with its reason and summarized, and no failure crashes or silently yields `nan`/`inf`.

---

## Phase 6: User Story 4 - Verify the claim from the page itself (Priority: P3)

**Goal**: Reach the paper and video from the page itself, with fixed citation/framing copy and the source expression and value above the tree.

**Independent Test**: Generate the page with `video_title`/`video_url` configured and again with both omitted; confirm citation, paper anchor, video anchor (when configured), explanation, source expression, and value appear in the required order with the configured hrefs/link titles and no other anchors (SC-007, SC-008).

### Tests for User Story 4 (mandated by plan.md and Constitution III)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T031 [P] [US4] IGNORE; superseded by Phase 8 (T040-T056) Extend `tests/integration/test_cli.py` with page-metadata/error tests: with `video_title`/`video_url` configured the anchors appear with the configured titles and hrefs and no others; with both video keys omitted only the paper anchor appears and no placeholder; source expression and value appear above the tree and match CLI output; two runs are byte-identical; and inputs `tau`, `0x10`, `0b10`, `1_000`, `x`, and an unsupported element exit `2` with a clear error and no `out.html` (FR-017–FR-021, SC-007–SC-009)

### Implementation for User Story 4

- [X] T032 [US4] IGNORE; superseded by Phase 8 (T040-T056) Implement the fixed page header in `eml_calculator/render_html.py` in exact order: citation text `Odrzywołek, *All elementary functions from a single binary operator*, arXiv:2603.21852v2`; anchor with text from `paper_title` and href from `paper_url`; anchor with text from `video_title` and href from `video_url` only when both are configured (omitted entirely otherwise, no placeholder/empty href); and 2–3 fixed sentences explaining the tree and that hovering a node shows its value; no other anchors anywhere; HTML-escape all dynamic strings including config titles (FR-017, SC-007)
- [X] T033 [US4] IGNORE; superseded by Phase 8 (T040-T056) Render the source expression exactly as supplied and its precomputed root value (or the failure summary in place of the value when it cannot be evaluated) below the citation block and above the tree in `eml_calculator/render_html.py`; nothing is recomputed in the browser (FR-019, SC-008)
- [X] T034 [US4] IGNORE; superseded by Phase 8 (T040-T056) Wire generation-time config into HTML output in `eml_calculator/cli.py` by calling `load_page_config()` and passing `paper_title`/`paper_url` and optional `video_title`/`video_url` to the renderer, surfacing a clear user-facing generation error for invalid config per `contracts/config.toml.md` (FR-018)

**Checkpoint**: All four user stories work independently; the page is self-verifying with fixed citation/explanation and config-sourced anchor titles/hrefs, correct conditional anchors, and source/value shown above the tree.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Record any spec/implementation drift, paper-vs-table discrepancies, and dependency notes in `decisions.md` (constitution governance; no silent artifact edits)
- [X] T036 Run the full suite with `python3 -m pytest -q` from repository root (after `python3 -m pip install -r requirements-dev.txt`) and fix any regressions across `tests/unit/` and `tests/integration/`. Test directories need no `__init__.py`; keep test module basenames unique.
- [X] T037 [P] Validate every scenario in `specs/001-eml-expression-translator/quickstart.md` end-to-end, including all seven validation scenarios (SC-005)
- [X] T038 [P] Audit generated `out.html` for byte-identical determinism across runs, absence of `<script>`/network/external assets, exactly the required anchors, and HTML escaping of all dynamic strings (expression, values, titles, failure markers, summary)
- [X] T039 Do a final readability/single-source pass across `eml_calculator/` and root `constructions.py`: no shared number retyped outside `constants.py` (VI), no formula outside `constructions.py` (V), no hidden dependencies or side effects outside CLI/output boundaries (II)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T004 constants first; T005/T006/T008 independent; T007 depends on T004) — **BLOCKS all user stories**
- **User Stories (Phase 3–6)**: All depend on Foundational (Phase 2) completion
  - US1 (P1) is the MVP and should be completed/validated first
  - US2 (P2), US3 (P3), US4 (P3) can then proceed in parallel if staffed, or sequentially P1 → P2 → P3
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational — depends on US1's tree/CLI to render, but its rendering tests are independently runnable against a synthetic `EMLTree`
- **User Story 3 (P3)**: Can start after Foundational — enriches evaluation/render models from US1/US2; independently testable via corpus failure cases
- **User Story 4 (P3)**: Can start after Foundational — enriches HTML generation from US2/US3; independently testable via page-metadata assertions
- Each story has its own checkpoint and is independently testable; no story requires a later story to be complete.

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution III)
- Models/data structures before services; core transforms before rendering/integration
- Story complete and validated at its checkpoint before moving to next priority

### Parallel Opportunities

- All Setup/Foundational tasks marked [P] can run in parallel (T004 must precede T007)
- All tests for a story marked [P] can be written in parallel (different test files)
- Within US1, parser (T013) can run in parallel with test authoring; rewrite/evaluate/CLI/render follow their dependencies
- Within US2, `render_text.py` (T020) and `render_html.py` (T021) can run in parallel
- US2, US3, and US4 can be worked on in parallel by different developers once US1 is validated (watch for shared files `render_html.py`, `cli.py`, `evaluate.py` — coordinate those edits)
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (write first, confirm they FAIL):
Task: "test_parser.py" (T009)
Task: "test_rewrite.py" (T010)
Task: "test_evaluate.py" (T011)
Task: "test_cli.py success path" (T012)

# Then implementation:
Task: "parser.py" (T013)   # parallel with rewrite/evaluate authored against interfaces
Task: "rewrite.py" (T014)  # depends on parser output + foundational tree model
Task: "evaluate.py" (T015) # single pass; uses T006 result types
Task: "cli.py/__main__.py" (T016)
Task: "render_text.py + render_html.py" (T017)
```

## Parallel Example: User Story 2

```bash
Task: "test_render_text.py" (T018)
Task: "test_render_html.py" (T019)

Task: "render_text.py" (T020)  # parallel with
Task: "render_html.py" (T021)  # different files
```

## Parallel Example: User Story 3

```bash
Task: "test_evaluate.py failures" (T024)
Task: "test_render_html.py values/failures" (T025)
Task: "test_corpus.py end-to-end" (T026)

Task: "evaluate.py failure summary" (T027)  # extends existing results; no re-evaluation
Task: "evaluate.py display helper" (T028)
Task: "render_html.py baked values" (T029)
Task: "cli.py exit 1 path" (T030)
```

## Parallel Example: User Story 4

```bash
Task: "test_cli.py page metadata/errors" (T031)  # write first, confirm it FAILs

Task: "render_html.py header" (T032)  # then same-file work sequential:
Task: "render_html.py source/value" (T033)
Task: "cli.py config wiring" (T034)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently — `python -m eml_calculator "1+1"` yields an `eml`/`1` tree whose root equals 2 within `REL_TOL_EPSILON`; run `tests/unit/test_parser.py`, `test_rewrite.py`, `test_evaluate.py`, and CLI integration test
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy/Demo (**MVP**)
3. Add US2 → Test structural parity/node count independently → Deploy/Demo
4. Add US3 → Test node values/failures via corpus independently → Deploy/Demo
5. Add US4 → Test page metadata/links independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T004 before T007)
2. Once Foundational and US1 are done:
   - Developer A: US2 (text/HTML structure, node count)
   - Developer B: US3 (evaluation failures, titles/focus/summary)
   - Developer C: US4 (page metadata/config/links)
3. Coordinate edits to `render_html.py`, `evaluate.py`, and `cli.py`; stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps a task to a specific user story for traceability; Setup/Foundational/Polish tasks have no label
- Every task follows `- [X] [TaskID] [P?] [Story?] Description with exact file path`
- Constitution V: all formulas only in root `constructions.py`; Constitution VI: all shared numbers only in `eml_calculator/constants.py`
- Constitution VII: renderer computes nothing; deterministic, byte-identical `out.html` with no JS/network
- Verify tests fail before implementing; commit after each task or logical group; stop at each checkpoint to validate a story independently
- Avoid vague tasks, same-file parallel conflicts, and cross-story dependencies that break independence

---

## Phase 8: Header Fragment Revision (post-implementation US4)

**Purpose**: Replace the fixed citation/explanation header from Phase 6 with owner-authored, source-controlled `top_fragment.html`; link text and URLs remain the only config-derived strings in the header. Existing T031–T034 stay `[X]` as historical completion records; this phase supersedes their fixed-header expectations without editing them. This also supersedes the fixed-citation/framing expectations in the Phase 6 Goal, Independent Test, and Checkpoint (and T031–T034): aside from rendering the fragment literally, the implementation constructs no page-top content, including the citation.

**⚠️ Contract**: Same expression + config + `top_fragment.html` ⇒ byte-identical `out.html` (FR-017–FR-019, FR-021, SC-007–SC-009).

### Tests for Phase 8 (write first, confirm failures)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T040 [P] Add a fragment fixture and header-order unit tests in `tests/unit/test_render_html.py`: a synthetic `top_fragment.html` with distinctive H1, summary paragraph, "References" heading, Article label, and Video label markup; call `render_html(..., top_fragment=fragment)` and assert that all non-token fragment markup appears verbatim in order (H1 → summary → References → Article row → Video row) above the source expression/value and tree, and that each `{{...}}` token is replaced only by the corresponding escaped config value including a fragment containing single-brace CSS, which MUST survive unchanged(FR-017, FR-019).
- [X] T041 [P] Extend `tests/unit/test_render_html.py` with regression tests that the old fixed citation paragraph and its `<em>`-wrapped article title are absent; the Article anchor inner HTML contains only the escaped `paper_title` text with no renderer-added `<em>` or other styling (FR-017, SC-007)
- [X] T042 [P] Extend `tests/unit/test_render_html.py` asserting the Article anchor alone uses `href` = `paper_url` and link text = `paper_title` from config, including a paper title that contains an author name and article title; assert no other anchor is introduced (FR-017, SC-007)
- [X] T043 [P] Extend `tests/unit/test_render_html.py` asserting that absent `video_title`/`video_url` values substitute as empty strings with no generation error, no renderer-added omission logic, and no unexpanded `{{...}}` tokens left in the output; H1/summary/References/Article and all other fragment content is unchanged (FR-017, FR-018, SC-007)
- [X] T044 [P] Extend `tests/unit/test_render_html.py` with escaping tests using config values containing `&`, `<`, `>`, and `"`; assert all four config-derived strings (`paper_title`, `paper_url`, `video_title`, `video_url`) are HTML-escaped in their respective text/attribute contexts and no injected markup or attribute is executed (FR-017, FR-021)
- [X] T045 [P] Create `tests/unit/test_top_fragment.py` with loader tests for a new `load_top_fragment()` boundary: returns the exact file text for a valid UTF-8 `top_fragment.html`, and raises a clear user-facing error naming the path for a missing file, a directory path, and a read that raises `OSError` (FR-018, FR-021)
- [X] T046 [P] Extend `tests/unit/test_render_html.py` with determinism tests asserting two calls with the same tree, config, and fragment string are byte-identical; changing the fragment text changes only the fragment-driven output (Principle VII, FR-017)

### Integration tests for Phase 8 (write first, confirm failures)

- [X] T047 Extend `tests/integration/test_cli.py` with CLI tests using a temporary root containing fixture `config.toml` and `top_fragment.html` and a mocked `webbrowser.open`: with both video keys configured, generated `out.html` has the fragment-driven H1 → summary → References → Article row → Video row, exactly the anchors present in the fragment, link texts/hrefs substituted from config, and source expression/value above the tree; with the video keys absent, their tokens substitute as empty strings with no error, no generated omission, and no unexpanded `{{...}}` tokens left in the output; exit status is `0` (FR-017–FR-019, SC-007, SC-008)
- [X] T048 Extend `tests/integration/test_cli.py` with a missing/unreadable fragment generation-error test: run the CLI from a temporary root with valid config but no `top_fragment.html` (and a monkeypatched read failure for an unreadable path), assert exit status `2`, a clear "generation error" message naming the fragment path, and no misleading `out.html` is created (FR-018, FR-021, SC-009)
- [X] T049 Extend `tests/integration/test_cli.py` with a determinism check that runs the CLI twice for the same expression/config/fragment and asserts the two `out.html` files are byte-identical (Principle VII, quickstart scenario 7)

### Implementation for Phase 8

- [X] T050 [P] Add source-controlled root `top_fragment.html` with the owner-approved H1, summary paragraph, "References" heading, Article/Video label rows, and exactly these four lowercase double-brace tokens: `{{paper_title}}`, `{{paper_url}}`, `{{video_title}}`, `{{video_url}}`. Tokens are expanded by literal string replacement (not `str.format`), so single literal braces — including inline CSS — need no escaping; all other fragment bytes are preserved. Keep fixed prose/markup out of Python and `config.toml` (FR-017, FR-018, Principle VII). No video-row delimiters are needed: the renderer does not conditionally omit rows.
- [X] T051 [P] Add `DEFAULT_TOP_FRAGMENT_PATH = "./top_fragment.html"` to `eml_calculator/constants.py` and implement `load_top_fragment(path=None)` in `eml_calculator/cli.py` using `Path.read_text(encoding="utf-8")`, raising a clear `ConfigError` naming the path for missing, unreadable, directory, or invalid-UTF-8 fragment input (FR-018, FR-021)
- [X] T052 Refactor `render_html()` in `eml_calculator/render_html.py` to accept top_fragment and substitute the four tokens `{{paper_title}}`, `{{paper_url}}`, `{{video_title}}`, `{{video_url}}` via literal string replacement (e.g., a single `re.sub` with a mapping (preferred), or sequential `str.replace`), passing all four values on every call with each HTML-escaped (`html.escape(..., quote=True)`) before substitution and `""` for absent video keys; alter no other fragment bytes and add no anchor, styling, or conditional row omission (FR-017, FR-019).
- [X] T053 Remove `CITATION_HTML`, `EXPLANATION`, and all fixed citation/explanation markup from `eml_calculator/render_html.py`; ensure no `<em>` wraps the paper title and no other anchors are added (FR-017)
- [X] T054 Wire generation-time fragment loading into `main()` in `eml_calculator/cli.py`: call `load_top_fragment()` before writing output, catch `ConfigError` as a "generation error" with exit status `2`, pass the exact fragment text to `render_html()`, and do not create/overwrite `out.html` on a fragment error (FR-018, FR-021, SC-009)

### Validation for Phase 8

- [X] T055 Run `/speckit.analyze` after Phase 8 changes; resolve all CRITICAL/HIGH findings or record an explicit disposition in `decisions.md` before considering the phase complete (constitution governance; no silent artifact edits)
- [X] T056 Run the full suite with `python3 -m pytest -q` from repository root; fix all regressions across `tests/unit/` and `tests/integration/` and confirm every Phase 8 test passes
