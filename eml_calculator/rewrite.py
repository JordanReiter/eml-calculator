"""Structural tree model and the source -> EML tree rewrite.

Nodes are structural only: no values, no side effects, no evaluation state.
The single evaluation pass returns a *new* tree whose ``evaluations`` mapping
holds per-node results.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from fractions import Fraction

import constructions as c

from .evaluate import EvaluationResult
from .parser import SourceNode

__all__ = ["TreeNode", "EMLTree", "rewrite"]


@dataclass(frozen=True)
class TreeNode:
    """One node: either an ``eml`` internal node with two children, or ``1``."""

    id: int
    kind: str  # "eml" | "leaf_one"
    left: TreeNode | None = None
    right: TreeNode | None = None
    display_label: str = "eml"

    @property
    def is_leaf(self) -> bool:
        return self.kind == "leaf_one"


@dataclass(frozen=True)
class EMLTree:
    """A rewritten expression and its (initially empty) evaluation side table."""

    root: TreeNode
    node_count: int
    source_text: str
    evaluations: dict[int, EvaluationResult] = field(default_factory=dict)
    zero_check_node_ids: frozenset[int] = frozenset()
    log_argument_node_ids: dict[int, int] = field(default_factory=dict)


_BINARY_CONSTRUCTIONS = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "div",
    "^": "power",
}

_FUNCTION_CONSTRUCTIONS = {
    "exp": "exp",
    "ln": "log",
    "sqrt": "sqrt",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
}

_ZERO_CHECK_BINARY = frozenset({"/", "^"})
_ZERO_CHECK_FUNCTIONS = frozenset({"ln", "sqrt"})


def _to_eml(source: SourceNode) -> c.EMLExpr:
    """Map a source node to a construction from the authoritative table."""
    kind = source.kind
    if kind == "group":
        return _to_eml(source.children[0])
    if kind == "literal":
        assert isinstance(source.value, Fraction)
        return c.rational(source.value.numerator, source.value.denominator)
    if kind == "named_constant":
        return c.const_pi() if source.value == "pi" else c.const_e()
    if kind == "unary_minus":
        return c.neg(_to_eml(source.children[0]))
    if kind == "binary_op":
        assert isinstance(source.value, str)
        constructor = getattr(c, _BINARY_CONSTRUCTIONS[source.value])
        left = _to_eml(source.children[0])
        right = _to_eml(source.children[1])
        if source.value in _ZERO_CHECK_BINARY:
            return constructor(left, right, zero_check=True)
        return constructor(left, right)
    if kind == "function_call":
        assert isinstance(source.value, str)
        constructor = getattr(c, _FUNCTION_CONSTRUCTIONS[source.value])
        argument = _to_eml(source.children[0])
        if source.value in _ZERO_CHECK_FUNCTIONS:
            return constructor(argument, zero_check=True)
        return constructor(argument)
    raise ValueError(f"unsupported source node '{kind}'")


def _to_tree(
    expr: c.EMLExpr,
    ids,
    zero_check_ids: set[int],
    expression_node_ids: dict[int, int],
    log_argument_ids: dict[int, int],
) -> TreeNode:
    node_id = next(ids)
    expression_node_ids[id(expr)] = node_id
    if expr.is_one:
        return TreeNode(id=node_id, kind="leaf_one", display_label="1")
    left = _to_tree(expr.left, ids, zero_check_ids, expression_node_ids, log_argument_ids)
    right = _to_tree(expr.right, ids, zero_check_ids, expression_node_ids, log_argument_ids)
    if expr.zero_check:
        zero_check_ids.add(node_id)
    if expr.log_argument is not None:
        argument_id = expression_node_ids[id(expr.log_argument)]
        log_argument_ids[node_id] = argument_id
    return TreeNode(id=node_id, kind="eml", left=left, right=right, display_label="eml")


def rewrite(source: SourceNode, source_text: str) -> EMLTree:
    """Rewrite one parsed source expression into an ``eml``/``1`` tree."""
    expression = _to_eml(source)
    ids = itertools.count()
    zero_check_ids: set[int] = set()
    expression_node_ids: dict[int, int] = {}
    log_argument_ids: dict[int, int] = {}
    root = _to_tree(expression, ids, zero_check_ids, expression_node_ids, log_argument_ids)
    return EMLTree(
        root=root,
        node_count=next(ids),
        source_text=source_text,
        zero_check_node_ids=frozenset(zero_check_ids),
        log_argument_node_ids=log_argument_ids,
    )
