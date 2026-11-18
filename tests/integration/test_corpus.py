"""End-to-end validation corpus tests (T026)."""

from __future__ import annotations

import pytest

from eml_calculator.constants import REL_TOL_EPSILON
from eml_calculator.corpus import CASES, equivalence_cases, failure_cases
from eml_calculator.evaluate import build_failure_summary, evaluate_source, evaluate_tree
from eml_calculator.parser import parse
from eml_calculator.rewrite import rewrite


def pipeline(expression: str):
    source = parse(expression)
    tree = evaluate_tree(rewrite(source, expression))
    summary = build_failure_summary(
        tree,
        source_value_available=evaluate_source(source).status == "ok",
    )
    return tree, summary


def close(actual: complex, expected: complex) -> bool:
    return abs(actual - expected) <= REL_TOL_EPSILON * max(1.0, abs(expected))


def assert_no_silent_nonfinite(tree) -> None:
    for result in tree.evaluations.values():
        for text in (result.display_value, result.value_display, result.message):
            assert "nan" not in text.lower()
            assert "inf" not in text.lower()


@pytest.mark.parametrize("case", equivalence_cases(), ids=lambda c: c.id)
def test_equivalence_cases_match_source(case):
    tree, summary = pipeline(case.expression)
    result = tree.evaluations[tree.root.id]
    assert summary.entries == ()
    assert result.status == "ok", result.message
    assert result.value is not None
    source_result = evaluate_source(parse(case.expression))
    assert source_result.status == "ok", source_result.message
    assert source_result.value is not None
    assert close(result.value, source_result.value)
    if case.expected is not None:
        assert close(result.value, complex(case.expected))
    assert_no_silent_nonfinite(tree)


@pytest.mark.parametrize("case", failure_cases(), ids=lambda c: c.id)
def test_failure_cases_report_specific_node_attributed_reason(case):
    tree, summary = pipeline(case.expression)
    result = tree.evaluations[tree.root.id]
    assert result.status == "failed"
    assert result.failure_reason == case.failure_reason
    assert result.attributed_node == tree.root.id
    assert result.message
    assert result.visible_failure_marker == case.failure_reason
    assert any(
        node_id == tree.root.id and reason == case.failure_reason
        for node_id, reason, _ in summary.entries
    )
    assert_no_silent_nonfinite(tree)


def test_corpus_includes_all_required_scenarios():
    ids = {case.id for case in CASES}
    assert {"one_plus_one", "division_by_zero", "zero_right_child", "overflow_depth"} <= ids
    assert any("pi" in case.id or "negative_right" in case.id for case in equivalence_cases())
