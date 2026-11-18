"""HTML-tree rendering tests (T019, T025, T029, T032, T033, T038)."""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from eml_calculator.evaluate import EvaluationResult, FailureSummary, format_complex
from eml_calculator.render_html import render_html
from eml_calculator.rewrite import EMLTree, TreeNode

CONFIG = {
    "paper_title": "the paper",
    "paper_url": "https://arxiv.org/abs/2603.21852",
    "video_title": "the video",
    "video_url": "https://www.youtube.com/watch?v=LxVW3b8jVdE",
}


def ok_result(node_id: int, value: complex = 2 + 0j) -> EvaluationResult:
    display = format_complex(value)
    return EvaluationResult(
        status="ok",
        value=value,
        display_value=display,
        value_display=display,
        display_as_real=abs(value.imag) == 0,
        attributed_node=node_id,
    )


def failed_result(node_id: int, reason: str, message: str) -> EvaluationResult:
    return EvaluationResult(
        status="failed",
        display_value=message,
        value_display=message,
        failure_reason=reason,
        attributed_node=node_id,
        message=message,
        visible_failure_marker=reason,
    )


def sample_tree() -> EMLTree:
    left = TreeNode(id=1, kind="leaf_one", display_label="1")
    right_left = TreeNode(id=3, kind="leaf_one", display_label="1")
    right_right = TreeNode(id=4, kind="leaf_one", display_label="1")
    right = TreeNode(id=2, kind="eml", left=right_left, right=right_right)
    root = TreeNode(id=0, kind="eml", left=left, right=right)
    return EMLTree(root=root, node_count=5, source_text="1+(1+1)")


def deep_tree(depth: int = 5) -> EMLTree:
    ids = iter(range(100))

    def build(level: int, node_id: int) -> TreeNode:
        leaf_id = next(ids)
        leaf = TreeNode(id=leaf_id, kind="leaf_one", display_label="1")
        if level == 0:
            return leaf
        right_id = next(ids)
        right = build(level - 1, right_id)
        return TreeNode(id=node_id, kind="eml", left=leaf, right=right, display_label="eml")

    root = build(depth, next(ids))
    count = sum(1 for _ in iter_nodes(root))
    return EMLTree(root=root, node_count=count, source_text="deep")


def iter_nodes(node):
    yield node
    if node.left is not None:
        yield from iter_nodes(node.left)
    if node.right is not None:
        yield from iter_nodes(node.right)


def node_labels(html: str) -> list[str]:
    return re.findall(r'<span class="node"[^>]*>(eml|1)</span>', html)


def test_html_tree_has_exactly_one_element_per_node_in_preorder():
    tree = sample_tree()
    html = render_html(tree, CONFIG)
    assert node_labels(html) == ["eml", "1", "eml", "1", "1"]
    assert html.count('class="node"') == tree.node_count


def test_deep_subtrees_use_details_without_eliding_any_node():
    tree = deep_tree()
    html = render_html(tree, CONFIG)
    assert "<details" in html
    assert html.count('class="node"') == tree.node_count
    assert node_labels(html) == [
        node.display_label for node in iter_nodes(tree.root)
    ]


def test_every_node_has_native_title_and_css_only_focus_reveal():
    tree = sample_tree()
    tree.evaluations[1] = ok_result(1, complex(2, 3))
    html = render_html(tree, CONFIG)
    assert html.count('tabindex="0"') == tree.node_count
    assert html.count("title=") >= tree.node_count
    assert "data-value=" in html
    assert ":focus::after" in html
    assert "<script" not in html.lower()


def test_failed_node_is_visible_marked_and_summarized_with_exact_reason():
    message = "undefined: right child evaluates to zero"
    tree = replace(
        sample_tree(),
        evaluations={
            0: failed_result(0, "undefined", message),
            1: ok_result(1),
            2: ok_result(2),
            3: ok_result(3),
            4: ok_result(4),
        },
    )
    summary = FailureSummary(entries=((0, "undefined", message),))
    html = render_html(tree, CONFIG, failure_summary=summary)
    assert html.count('class="failure"') == 1
    assert "undefined" in re.search(r'<span class="failure">([^<]+)</span>', html).group(1)
    assert f'title="{message}"' in html
    assert f"<li>node 0: undefined — {message}</li>" in html


def test_root_failure_replaces_displayed_value_with_failure_summary():
    message = "overflow: root value is not finite"
    tree = replace(sample_tree(), evaluations={0: failed_result(0, "overflow", message)})
    summary = FailureSummary(entries=((0, "overflow", message),))
    source_value = ok_result(-1)
    html = render_html(tree, CONFIG, failure_summary=summary, source_value=source_value)
    value_start = html.index("Value:")
    tree_start = html.index('<section class="tree">')
    assert "Value: unavailable" in html
    assert message in html[value_start:tree_start]
    assert "Value: <code>2</code>" not in html


def test_fixed_header_and_conditional_video_anchor_are_rendered_in_order():
    tree = sample_tree()
    html = render_html(tree, CONFIG)
    anchors = re.findall(r'<a href="([^"]+)">([^<]+)</a>', html)
    assert anchors == [
        (CONFIG["paper_url"], CONFIG["paper_title"]),
        (CONFIG["video_url"], CONFIG["video_title"]),
    ]
    assert html.count("<a ") == 2
    assert html.index("Odrzywołek") < html.index("<a ")
    assert html.index("<a ") < html.index("This tree is")
    assert html.index("This tree is") < html.index("Source expression:")
    assert html.index("Source expression:") < html.index('<section class="tree">')


def test_omitted_video_config_renders_no_video_anchor_or_placeholder():
    config = dict(CONFIG)
    config.pop("video_title")
    config.pop("video_url")
    html = render_html(sample_tree(), config)
    assert html.count("<a ") == 1
    assert CONFIG["video_title"] not in html
    assert 'href=""' not in html


def test_dynamic_strings_are_escaped_and_no_script_is_present():
    config = dict(CONFIG)
    config["paper_title"] = "<b>bad & title"
    message = "<b>undefined</b>"
    tree = replace(
        sample_tree(),
        source_text="<x> & y",
        evaluations={0: failed_result(0, "undefined", message)},
    )
    summary = FailureSummary(entries=((0, "undefined", message),))
    html = render_html(tree, config, failure_summary=summary)
    assert "&lt;b&gt;bad &amp; title" in html
    assert "&lt;x&gt; &amp; y" in html
    assert "&lt;b&gt;undefined&lt;/b&gt;" in html
    assert "<b>" not in html
    assert "<script" not in html.lower()


def test_html_output_is_byte_identical_for_repeated_renders():
    tree = sample_tree()
    assert render_html(tree, CONFIG) == render_html(tree, CONFIG)


@pytest.mark.parametrize("value", [complex(1, 1e-13), complex(1, 1e-3)])
def test_node_titles_follow_the_shared_real_display_rule(value):
    tree = sample_tree()
    tree.evaluations[1] = ok_result(1, value)
    html = render_html(tree, CONFIG)
    expected = format_complex(value)
    assert f'title="{expected}"' in html
