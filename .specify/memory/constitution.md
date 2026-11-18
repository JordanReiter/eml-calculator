<!--
Sync Impact Report (temporary; remove before commit)
- Version change: 1.1.0 → 1.2.0 (MINOR: principle materially changed)
- Amended principles: V. The Construction Table Is the Only Source of Formulas — the authority for constructions is now the author's EML compiler (`VA00/SymbolicRegressionPackage`, `EML_toolkit/EmL_compiler`), with the Supplementary Information as the verification standard where the two disagree. Rationale: the SI expresses constructions as a discovery-chain figure and adjacency matrix; the compiler is the same derivations in executable form, so ports can be diffed rather than transcribed.
- Added principles: none
- Added constraints: none this version
- Deferred TODOs: none
-->
# The 2 Button Calculator Constitution

## Core Principles

### I. Code for Readability
Code MUST be written for the next reader first. Prefer clear names, straightforward control flow, and small, well-scoped units over cleverness. Comments explain intent when the code cannot. Reviews treat readability as a correctness concern: if behavior is hard to follow, it is not done.

### II. Make Dependencies Explicit
Dependencies MUST be visible at boundaries. Construct or inject what a unit needs rather than hiding it behind implicit globals or ambient state where practical. When a dependency is external (I/O, network, filesystem, time, randomness), that boundary MUST be obvious in the code so behavior is explainable and testable.

### III. Test the Transformation, Not the Plumbing
Unit tests MUST cover pure transformation logic. Integration tests MUST cover the boundaries. Do not mock what you own; mock what you do not. A green CI without a failing test for the bug you just fixed is not green.

This principle applies to every change that fixes or introduces behavior: the test suite should make the intended transformation fail first where feasible, then pass.

### IV. Favor Simple, Predictable Design
Favor simple data structures over complex ones. Avoid side effects. Prefer pure functions and explicit data flow for core logic. When complexity is unavoidable, it MUST be localized and justified in review so the default path stays easy to reason about.

### V. The Construction Table Is the Only Source of Formulas
Every `eml` construction MUST come from the single table in `constructions.py`, ported from the EML compiler in `VA00/SymbolicRegressionPackage` (`EML_toolkit/EmL_compiler`), whose derivations are verified against the Supplementary Information of arXiv:2603.21852v2. Constructions MUST NOT be re-derived by hand, inlined at call sites, or duplicated in tests. Where the table and the paper disagree, the paper wins and the table is corrected with a note explaining the change.

### VI. Every Number Is Named Once
Shared constants — the equivalence tolerance `ε`, the sample range for free variables, the evaluation depth limit — MUST be defined in one module and imported by name. Tests MUST NOT re-type their values. A number written in two places is a discrepancy waiting to be discovered by a test that passes anyway.

### VII. The Renderer Computes Nothing, and Its Output Is Deterministic
Node values MUST be computed in Python and written into the markup. The generated page MUST NOT contain JavaScript, MUST NOT make network requests, and MUST NOT recompute any value. The same expression MUST produce a byte-identical output file.

### VIII. The Agent Implements, the Human Reviews
This project is the control case for the development process: the framework is the variable, the language is not. Implementation is written by the agent and reviewed by the human. This principle is deliberately the opposite of the one governing the 2D Congressional Ledger, where the human writes the code. Neither principle applies outside its own project.

## Additional Constraints

- **Scope of this constitution**: Governance applies to development of “The 2 Button Calculator” repository artifacts. Product behavior is defined by feature specifications and plans under `specs/`.
- **Runtime dependencies**: CPython 3.11+ and the standard library. Any third-party runtime dependency MUST be recorded in `decisions.md` with the reason the standard library is insufficient.
- **Build and review cadence**: Work MUST be delivered in reviewable chunks so changes can be reviewed by the user in small, coherent steps.

## Development Workflow and Quality Gates

- Changes SHOULD be small enough to review quickly; split work when a single change mixes unrelated concerns.
- Testing expectations:
  - Pure transformations: unit tests required.
  - Boundary/integration points (external systems, I/O, end-to-end wiring): integration tests required at those boundaries.
  - Mocking policy: do not mock code you own; mock external/unowned dependencies only as needed.
  - Bug fixes: include or demonstrate a test that failed before the fix when practical; a “green” suite alone is insufficient evidence of a corrected bug.
- Reviewers MUST verify compliance with these principles and call out hidden dependencies, unnecessary side effects, or tests that only exercise plumbing.
- Drift between specification and implementation MUST be recorded in `decisions.md`. Neither artifact is silently adjusted to match the other.

## Governance

- **Authority**: This constitution supersedes conflicting informal practice for this project. Feature specs, plans, and tasks MUST remain consistent with it unless an explicit, approved amendment changes the constitution.
- **Amendments**: Any change to this document MUST be proposed in a pull request (or equivalent review) that includes: rationale, the exact text changes, and a version bump per the rules below. Material changes SHOULD note migration or follow-up work for affected specs/templates.
- **Versioning policy (semantic versioning)**: `MAJOR.MINOR.PATCH`
  - **MAJOR (X.n.n)**: Backward-incompatible governance or principle redefinitions/removals.
  - **MINOR (n.X.n)**: New principle/section added or materially expanded guidance.
  - **PATCH (n.n.X)**: Clarifications, wording, typo fixes, non-semantic refinements.
- **Compliance review**: Reviewers MUST verify changes against Core Principles and Quality Gates. Complexity or exceptions MUST be justified in the review.
- **Build/review chunking**: Work MUST be broken into reviewable chunks (see Development Workflow and Quality Gates) so the user can review progress incrementally.

**Version**: 1.2.0 | **Ratified**: 2026-11-16 | **Last Amended**: 2026-11-16