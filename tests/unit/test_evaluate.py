"""Evaluation and equivalence unit tests (T011, extended by T024)."""

from __future__ import annotations

import math

import pytest

from eml_calculator.constants import (
    DEFAULT_FREE_VAR_SAMPLES,
    IMAG_ABS_FLOOR,
    REL_TOL_EPSILON,
)
from eml_calculator.corpus import equivalence_cases
from eml_calculator.evaluate import evaluate_source, evaluate_tree, format_complex
from eml_calculator.parser import parse
from eml_calculator.rewrite import rewrite


def close(actual: complex, expected: complex) -> bool:
    return abs(actual - expected) <= REL_TOL_EPSILON * max(1.0, abs(expected))


def root_of(expression: str) -> complex:
    tree = evaluate_tree(rewrite(parse(expression), expression))
    result = tree.evaluations[tree.root.id]
    assert result.status == "ok", result.message
    assert result.value is not None
    return result.value


def test_one_plus_one_evaluates_to_two():
    assert close(root_of("1+1"), complex(2, 0))


@pytest.mark.parametrize("case", equivalence_cases(), ids=lambda c: c.id)
def test_corpus_root_matches_source(case):
    source_result = evaluate_source(parse(case.expression))
    assert source_result.status == "ok", source_result.message
    assert source_result.value is not None
    assert close(source_result.value, complex(case.expected)) if case.expected is not None else True
    assert close(root_of(case.expression), source_result.value)


@pytest.mark.parametrize("sample", DEFAULT_FREE_VAR_SAMPLES)
def test_samples_verify_equivalence_over_shared_range(sample):
    expression = f"{sample}+1"
    assert close(root_of(expression), evaluate_source(parse(expression)).value)


def test_evaluation_returns_new_tree_without_mutating_input():
    from eml_calculator.rewrite import rewrite as build

    tree = build(parse("1+1"), "1+1")
    assert tree.evaluations == {}
    evaluated = evaluate_tree(tree)
    assert tree.evaluations == {}
    assert evaluated.evaluations != {}


def test_format_complex_uses_shared_real_display_rule():
    real_imag = complex(1.0, IMAG_ABS_FLOOR / 2)
    complex_value = complex(1.0, IMAG_ABS_FLOOR * 1e6)
    assert format_complex(real_imag) == "1"
    assert "i" in format_complex(complex_value)
    assert not any(token in format_complex(complex_value) for token in ("nan", "inf"))


def test_non_finite_source_is_reported_not_silently_returned():
    result = evaluate_source(parse("1/0"))
    assert result.status == "failed"
    assert result.failure_reason in {"overflow", "undefined"}
    assert result.message
    assert result.value is None or math.isfinite(result.value.real)
