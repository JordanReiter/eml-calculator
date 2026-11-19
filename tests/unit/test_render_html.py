"""HTML-tree rendering tests (T019, T025, T029, T038, T040–T046)."""

from __future__ import annotations

import re
from dataclasses import replace
from html import escape

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

# Synthetic owner-authored fragment: distinctive landmarks in the required
# order, four lowercase double-brace tokens, and literal single-brace CSS.
SAMPLE_FRAGMENT = """<h1 id="heading">Owner heading</h1>
<p class="summary">Owner summary explaining the tree and hovering.</p>
<style>body { margin: 0; }</style>
<h2>References</h2>
<p class="article">Article: <a href="{{paper_url}}">{{paper_title}}</a></p>
<p class="video">Video: <a href="{{video_url}}">{{video_title}}</a></p>
"""

FRAGMENT_LANDMARKS = [
    '<h1 id="heading">Owner heading</h1>',
    '<p class="summary">Owner summary explaining the tree and hovering.</p>',
    "body { margin: 0; }",
    "<h2>References</h2>",
    '<p class="article">Article:',
    '<p class="video">Video:',
]

TOKEN_PATTERN = re.compile(
    r"\{\{(?:paper_title|paper_url|video_title|video_url)\}\}"
)


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


def evaluated_tree() -> EMLTree:
    """A sample tree whose nodes all carry a successful evaluation."""
    tree = sample_tree()
    tree.evaluations.update(
        {node.id: ok_result(node.id) for node in iter_nodes(tree.root)}
    )
    return tree


def render_with_fragment(config=None, fragment=SAMPLE_FRAGMENT):
    return render_html(evaluated_tree(), config or CONFIG, top_fragment=fragment)


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


def test_fragment_markup_appears_verbatim_in_order_above_result_and_tree():
    html = render_with_fragment()

    positions = [html.index(landmark) for landmark in FRAGMENT_LANDMARKS]
    assert positions == sorted(positions)
    assert positions[-1] < html.index("Source expression:")
    assert html.index("Source expression:") < html.index('<section class="tree">')

    # Every non-token fragment byte survives unchanged, including single braces.
    for chunk in TOKEN_PATTERN.split(SAMPLE_FRAGMENT):
        assert chunk in html
    assert "{{" not in html and "}}" not in html


def test_fixed_citation_and_em_wrapped_title_are_absent():
    html = render_with_fragment()

    assert "Odrzywołek" not in html
    assert "arXiv:2603.21852v2" not in html
    assert "This tree is" not in html
    assert "<em>" not in html and "</em>" not in html
    article_text = re.search(r'<a href="[^"]*">([^<]*)</a>', html).group(1)
    assert article_text == CONFIG["paper_title"]
    assert "<" not in article_text


def test_article_and_video_anchors_use_only_config_values():
    config = dict(CONFIG)
    config["paper_title"] = "Odrzywołek, All elementary functions from a single binary operator"
    html = render_with_fragment(config)

    anchors = re.findall(r'<a href="([^"]*)">([^<]*)</a>', html)
    assert anchors == [
        (config["paper_url"], config["paper_title"]),
        (config["video_url"], config["video_title"]),
    ]
    assert html.count("<a ") == 2


def test_absent_video_values_substitute_empty_strings_without_omission():
    config = dict(CONFIG)
    config.pop("video_title")
    config.pop("video_url")
    html = render_with_fragment(config)

    assert re.findall(r'<a href="([^"]*)">([^<]*)</a>', html) == [
        (CONFIG["paper_url"], CONFIG["paper_title"]),
        ("", ""),
    ]
    assert '<p class="video">Video: <a href="">' in html
    assert "{{" not in html and "}}" not in html
    for chunk in TOKEN_PATTERN.split(SAMPLE_FRAGMENT):
        assert chunk in html


def test_config_values_are_escaped_in_text_and_attribute_contexts():
    config = {
        "paper_title": 'A & B <script> "paper"',
        "paper_url": 'https://example.org/?a=1&b="<x>"',
        "video_title": "V & <video> 'quoted'",
        "video_url": 'https://video.example/?q="<&>"',
    }
    html = render_with_fragment(config)

    for value in config.values():
        assert escape(value, quote=True) in html
    assert "<script>" not in html
    assert "<video>" not in html
    assert 'href="https://example.org/?a=1&amp;b=&quot;&lt;x&gt;&quot;"' in html


def test_render_is_deterministic_and_only_fragment_text_changes_header():
    tree = evaluated_tree()
    first = render_html(tree, CONFIG, top_fragment=SAMPLE_FRAGMENT)
    second = render_html(tree, CONFIG, top_fragment=SAMPLE_FRAGMENT)
    assert first == second

    changed_fragment = SAMPLE_FRAGMENT.replace("Owner heading", "Changed heading")
    changed = render_html(tree, CONFIG, top_fragment=changed_fragment)
    assert "Changed heading" in changed
    assert "Owner heading" not in changed
    assert changed.replace("Changed heading", "Owner heading") == first


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
    html = render_html(
        tree, config, failure_summary=summary, top_fragment=SAMPLE_FRAGMENT
    )
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
