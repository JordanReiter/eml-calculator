"""EML rewrite unit tests (T010)."""

from __future__ import annotations

import pytest

import constructions

from eml_calculator.parser import parse
from eml_calculator.rewrite import TreeNode, rewrite


def walk(node: TreeNode):
    yield node
    if node.left is not None:
        yield from walk(node.left)
    if node.right is not None:
        yield from walk(node.right)


@pytest.mark.parametrize("text", [
    "1+1", "2", "2.5", "pi", "e", "ln(2)", "sin(0.5)", "2*(3+4)", "1e-3/2",
])
def test_output_alphabet_is_only_eml_and_one(text):
    tree = rewrite(parse(text), text)
    labels = {node.display_label for node in walk(tree.root)}
    assert labels == {"eml", "1"}
    assert tree.node_count == sum(1 for _ in walk(tree.root))
    for node in walk(tree.root):
        if node.kind == "eml":
            assert node.left is not None and node.right is not None
        else:
            assert node.kind == "leaf_one" and node.left is None and node.right is None


def test_preorder_indices_are_deterministic_and_unique():
    first = rewrite(parse("1+1"), "1+1")
    second = rewrite(parse("1+1"), "1+1")
    assert [n.id for n in walk(first.root)] == [n.id for n in walk(second.root)]
    assert len({n.id for n in walk(first.root)}) == first.node_count


def test_node_count_of_one_plus_one_is_twenty_seven():
    tree = rewrite(parse("1+1"), "1+1")
    assert tree.node_count > 1
    assert tree.root.id == 0


def test_rewrite_delegates_formulas_to_construction_table(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("rewrite inlined a construction instead of calling constructions.py")

    monkeypatch.setattr(constructions, "add", forbidden)
    with pytest.raises(AssertionError, match="inlined"):
        rewrite(parse("1+1"), "1+1")
