"""Fixed validation corpus (FR-002, SC-001–SC-003).

Pure data: expressions, expected outcomes, and notes.  No formulas live here;
every numeric threshold or sample descriptor comes from ``constants.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import OVERFLOW_EXPONENTIAL_COUNT


@dataclass(frozen=True)
class CorpusCase:
    id: str
    expression: str
    kind: str  # "equivalence" | "failure"
    expected: complex | None = None  # equivalence: closed-form value
    failure_reason: str | None = None  # failure: "overflow" | "undefined"
    sample_range: str | None = None
    notes: str = ""


def _overflow_expression() -> str:
    text = "1"
    for _ in range(OVERFLOW_EXPONENTIAL_COUNT):
        text = f"exp({text})"
    return text


CASES: tuple[CorpusCase, ...] = (
    CorpusCase("one_plus_one", "1+1", "equivalence", 2, notes="MVP tree/node-count check"),
    CorpusCase("literal_integer", "2", "equivalence", 2),
    CorpusCase("literal_decimal", "2.5", "equivalence", 2.5),
    CorpusCase("literal_leading_dot", ".5", "equivalence", 0.5),
    CorpusCase("literal_exponent", "1e-3", "equivalence", 0.001),
    CorpusCase("parentheses", "(1+2)*3", "equivalence", 9),
    CorpusCase("subtraction", "5-3", "equivalence", 2),
    CorpusCase("multiplication", "2*3", "equivalence", 6),
    CorpusCase("division", "6/2", "equivalence", 3),
    CorpusCase("power", "2^3", "equivalence", 8),
    CorpusCase("right_assoc_power", "2^3^2", "equivalence", 512),
    CorpusCase("unary_minus", "-(2+1)", "equivalence", -3),
    CorpusCase("exp_one", "exp(1)", "equivalence", None, notes="equals e"),
    CorpusCase("ln_two", "ln(2)", "equivalence", None, sample_range="unit"),
    CorpusCase("sqrt_four", "sqrt(4)", "equivalence", 2),
    CorpusCase("sin_one", "sin(1)", "equivalence", None),
    CorpusCase("cos_one", "cos(1)", "equivalence", None),
    CorpusCase("tan_half", "tan(0.5)", "equivalence", None),
    CorpusCase("pi_constant", "pi", "equivalence", None, notes="negative right child in chain"),
    CorpusCase("e_constant", "e", "equivalence", None),
    CorpusCase("precedence", "1+2*3", "equivalence", 7),
    CorpusCase("ln_negative_one", "ln(-1)", "equivalence", None,
               notes="successful complex case: log(-1) = i*pi (principal branch)"),
    CorpusCase("negative_fractional_power", "(-1)^(1/2)", "equivalence", None,
               notes="successful complex case via principal branch"),
    CorpusCase("exp_ln_roundtrip", "ln(exp(2))", "equivalence", 2),
    CorpusCase("mul_add", "2*(3+4)", "equivalence", 14),
    CorpusCase("scaled_decimal", "1e-3/2", "equivalence", 0.0005),
    CorpusCase("sqrt_two", "sqrt(2)", "equivalence", None, sample_range="unit"),
    CorpusCase("tan_zero", "tan(0)", "equivalence", 0),
    CorpusCase("exp_negative", "exp(-1)", "equivalence", None),
    CorpusCase("trig_mix", "sin(0.5)+cos(0.5)", "equivalence", None),
    CorpusCase("division_by_zero", "1/0", "failure", failure_reason="undefined"),
    CorpusCase("zero_right_child", "ln(0)", "failure", failure_reason="undefined",
               notes="eml node whose source-derived right child evaluates to zero"),
    CorpusCase("zero_right_child_expression", "ln(1-1)", "failure", failure_reason="undefined"),
    CorpusCase("overflow_depth", _overflow_expression(), "failure", failure_reason="overflow",
               notes="tree deep enough to leave floating-point range"),
)


def equivalence_cases() -> tuple[CorpusCase, ...]:
    return tuple(c for c in CASES if c.kind == "equivalence")


def failure_cases() -> tuple[CorpusCase, ...]:
    return tuple(c for c in CASES if c.kind == "failure")
