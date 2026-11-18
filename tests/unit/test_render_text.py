"""Text-tree rendering tests (T018, T020, T023)."""

from __future__ import annotations

from eml_calculator.rewrite import EMLTree, TreeNode
from eml_calculator.render_text import render_text


def sample_tree() -> EMLTree:
    left = TreeNode(id=1, kind="leaf_one", display_label="1")
    right_left = TreeNode(id=3, kind="leaf_one", display_label="1")
    right_right = TreeNode(id=4, kind="leaf_one", display_label="1")
    right = TreeNode(id=2, kind="eml", left=right_left, right=right_right)
    root = TreeNode(id=0, kind="eml", left=left, right=right)
    return EMLTree(root=root, node_count=5, source_text="1+(1+1)")


def test_text_tree_uses_one_node_per_line_with_exact_indentation():
    assert render_text(sample_tree()) == "\n".join([
        "eml(",
        "  1",
        "  eml(",
        "    1",
        "    1",
        "  )",
        ")",
    ])


def test_text_tree_node_tokens_match_tree_node_count_and_preorder():
    tree = sample_tree()
    lines = render_text(tree).splitlines()
    node_lines = [line for line in lines if line.strip() in {"eml(", "1"}]
    assert len(node_lines) == tree.node_count
    assert [line.strip() for line in node_lines] == ["eml(", "1", "eml(", "1", "1"]


def test_text_tree_is_deterministic():
    tree = sample_tree()
    assert render_text(tree) == render_text(tree)
