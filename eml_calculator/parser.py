"""Hand-written tokenizer and recursive-descent parser for closed input.

``ast.literal_eval`` is deliberately not used: it would accept hexadecimal,
binary, and underscore-separated literals that FR-002 rejects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

__all__ = ["SourceNode", "parse"]

NAMED_CONSTANTS = frozenset({"pi", "e"})
SUPPORTED_FUNCTIONS = frozenset({"exp", "ln", "sqrt", "sin", "cos", "tan"})
BINARY_OPERATORS = frozenset({"+", "-", "*", "/", "^"})

_NUMBER = re.compile(r"(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_INVALID_LITERAL = re.compile(r"0[xXbBoO][0-9A-Fa-f_]+|\d[\d_]*_\d[\d_]*")


@dataclass(frozen=True)
class SourceNode:
    """Parsed source expression, before any EML construction."""

    kind: str  # literal | named_constant | unary_minus | binary_op | function_call
    value: Fraction | str
    children: tuple[SourceNode, ...] = ()
    span: tuple[int, int] | None = None


@dataclass(frozen=True)
class _Token:
    kind: str  # NUMBER | NAME | OP | LPAREN | RPAREN | EOF
    value: str
    start: int


def _reject_invalid_literals(text: str) -> None:
    match = _INVALID_LITERAL.search(text)
    if match:
        raise ValueError(f"unsupported numeric literal '{match.group()}' at position {match.start()}")


def _tokenize(text: str) -> list[_Token]:
    _reject_invalid_literals(text)
    tokens: list[_Token] = []
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
            continue
        if char == "(":
            tokens.append(_Token("LPAREN", char, position))
            position += 1
            continue
        if char == ")":
            tokens.append(_Token("RPAREN", char, position))
            position += 1
            continue
        if char in BINARY_OPERATORS:
            tokens.append(_Token("OP", char, position))
            position += 1
            continue
        number = _NUMBER.match(text, position)
        if number:
            tokens.append(_Token("NUMBER", number.group(), number.start()))
            position = number.end()
            continue
        name = _NAME.match(text, position)
        if name:
            tokens.append(_Token("NAME", name.group(), name.start()))
            position = name.end()
            continue
        raise ValueError(f"unsupported element '{char}' at position {position}")
    tokens.append(_Token("EOF", "", len(text)))
    return tokens


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.tokens = _tokenize(text)
        self.index = 0

    @property
    def current(self) -> _Token:
        return self.tokens[self.index]

    def _take(self) -> _Token:
        token = self.current
        self.index += 1
        return token

    def _expect(self, kind: str, label: str) -> _Token:
        if self.current.kind != kind:
            raise ValueError(f"expected {label} at position {self.current.start}")
        return self._take()

    def parse(self) -> SourceNode:
        node = self._expression()
        if self.current.kind != "EOF":
            token = self.current
            raise ValueError(
                f"unsupported element '{token.value}' at position {token.start}"
            )
        return node

    def _expression(self) -> SourceNode:
        left = self._term()
        while self.current.kind == "OP" and self.current.value in {"+", "-"}:
            operator = self._take()
            right = self._term()
            left = SourceNode(
                "binary_op",
                operator.value,
                (left, right),
                (operator.start, right.span[1] if right.span else None),
            )
        return left

    def _term(self) -> SourceNode:
        left = self._unary()
        while self.current.kind == "OP" and self.current.value in {"*", "/"}:
            operator = self._take()
            right = self._unary()
            left = SourceNode(
                "binary_op",
                operator.value,
                (left, right),
                (operator.start, right.span[1] if right.span else None),
            )
        return left

    def _unary(self) -> SourceNode:
        if self.current.kind == "OP" and self.current.value == "-":
            operator = self._take()
            operand = self._unary()
            return SourceNode("unary_minus", "-", (operand,), (operator.start, operand.span[1]))
        return self._power()

    def _power(self) -> SourceNode:
        base = self._primary()
        if self.current.kind == "OP" and self.current.value == "^":
            operator = self._take()
            exponent = self._unary()  # right-associative and tighter than unary minus
            return SourceNode("binary_op", "^", (base, exponent), (operator.start, exponent.span[1]))
        return base

    def _primary(self) -> SourceNode:
        token = self.current
        if token.kind == "NUMBER":
            self._take()
            return SourceNode("literal", Fraction(token.value), (), (token.start, token.start + len(token.value)))
        if token.kind == "LPAREN":
            self._take()
            node = self._expression()
            closing = self._expect("RPAREN", "')'")
            return SourceNode("group", "()", (node,), (token.start, closing.start + 1))
        if token.kind == "NAME":
            self._take()
            return self._named(token)
        if token.kind == "OP":
            raise ValueError(f"unsupported operator '{token.value}' at position {token.start}")
        raise ValueError(f"unsupported element '{token.value or self.text}' at position {token.start}")

    def _named(self, token: _Token) -> SourceNode:
        name = token.value
        end = token.start + len(name)
        if self.current.kind == "LPAREN":
            if name not in SUPPORTED_FUNCTIONS:
                raise ValueError(f"unsupported function '{name}' at position {token.start}")
            self._take()
            argument = self._expression()
            closing = self._expect("RPAREN", "')'")
            return SourceNode("function_call", name, (argument,), (token.start, closing.start + 1))
        if name in NAMED_CONSTANTS:
            return SourceNode("named_constant", name, (), (token.start, end))
        if name in SUPPORTED_FUNCTIONS:
            raise ValueError(f"function '{name}' requires parentheses at position {token.start}")
        if len(name) == 1:
            raise ValueError(f"free variable '{name}' is not supported at position {token.start}")
        raise ValueError(f"unknown constant '{name}' at position {token.start}")


def parse(text: str) -> SourceNode:
    """Parse one closed arithmetic expression into a Source Expression Structure."""
    if not text or not text.strip():
        raise ValueError("empty expression")
    return _Parser(text).parse()
