"""Tokenizer/parser unit tests (T009)."""

from __future__ import annotations

import re

import pytest

from eml_calculator.parser import parse


def shape(node) -> tuple:
    """Structural fingerprint of a parsed source expression (no formulas)."""
    return (node.kind, node.value, tuple(shape(child) for child in node.children))


@pytest.mark.parametrize("text", ["2", "2.5", ".5", "1e-3"])
def test_decimal_literals_accept_exponent_and_leading_dot(text):
    node = parse(text)
    assert node.kind == "literal"
    assert float(node.value) == float(text)


@pytest.mark.parametrize("text", ["0x10", "0b10", "1_000"])
def test_rejected_literal_forms_name_the_element(text):
    with pytest.raises(ValueError, match=text.replace("_", "\\_")):
        parse(text)


def test_precedence_and_right_associative_power():
    assert shape(parse("-2^2")) == (
        "unary_minus", "-",
        (("binary_op", "^", (("literal", 2, ()), ("literal", 2, ()))),),
    )
    assert shape(parse("2^3^2")) == (
        "binary_op", "^",
        (
            ("literal", 2, ()),
            ("binary_op", "^", (("literal", 3, ()), ("literal", 2, ()))),
        ),
    )


def test_parentheses_unary_and_binary_operators():
    node = parse("-(1+2)*3")
    assert node.kind == "binary_op" and node.value == "*"
    assert node.children[0].kind == "unary_minus"
    assert node.children[1].value == 3


@pytest.mark.parametrize("name", ["exp", "ln", "sqrt", "sin", "cos", "tan"])
def test_supported_functions(name):
    node = parse(f"{name}(1)")
    assert node.kind == "function_call" and node.value == name
    assert len(node.children) == 1


@pytest.mark.parametrize("name", ["pi", "e"])
def test_named_constants(name):
    node = parse(name)
    assert node.kind == "named_constant" and node.value == name


@pytest.mark.parametrize("text, expected", [
    ("tau", "tau"),
    ("phi", "phi"),
    ("x", "x"),
    ("2**3", "*"),
    ("floor(1)", "floor"),
])
def test_closed_grammar_errors_name_the_unsupported_element(text, expected):
    with pytest.raises(ValueError, match=re.escape(expected)):
        parse(text)
