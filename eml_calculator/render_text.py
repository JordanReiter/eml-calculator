"""Deterministic indented text rendering of an EML tree (FR-006)."""

from __future__ import annotations

__all__ = ["render_text"]


def render_text(tree) -> str:
    """Render one node per structural line, in the tree's pre-order."""
    lines: list[str] = []

    def visit(node, depth: int) -> None:
        indent = "  " * depth
        if node.is_leaf:
            lines.append(f"{indent}1")
            return
        lines.append(f"{indent}eml(")
        visit(node.left, depth + 1)
        visit(node.right, depth + 1)
        lines.append(f"{indent})")

    visit(tree.root, 0)
    return "\n".join(lines)
