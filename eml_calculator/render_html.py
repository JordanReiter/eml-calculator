"""Deterministic, self-contained HTML rendering (FR-007–FR-020).

The renderer computes nothing: every value and failure state is already baked
into the evaluated tree.  There is no JavaScript, no network access, and no
recomputation in the browser.
"""

from __future__ import annotations

from html import escape

from .constants import DETAILS_DEPTH_THRESHOLD, DETAILS_OPEN_LEVELS

__all__ = ["render_html"]

CITATION_HTML = (
    "Odrzywołek, <em>All elementary functions from a single binary operator</em>, "
    "arXiv:2603.21852v2"
)

EXPLANATION = (
    "This tree is the source expression rewritten using only the eml operator "
    "and the constant 1. Each eml node combines two child nodes. Hover a node "
    "to see its precomputed value, or focus it with the keyboard."
)

_STYLE = """
body { font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }
code, .node { font-family: ui-monospace, monospace; }
.tree ul { list-style: none; padding-left: 1.25rem; }
.node { border: 1px solid #888; border-radius: 4px; padding: 0.1rem 0.35rem; }
.node:focus { outline: 2px solid #06c; }
.node:focus::after { content: " → " attr(data-value); color: #06c; }
.failure { color: #b00; font-weight: bold; margin-left: 0.5rem; }
summary { cursor: pointer; }
""".strip()


def _node_html(node, evaluations: dict, depth: int) -> str:
    result = evaluations.get(node.id)
    text = result.value_display if result is not None else ""
    if node.is_leaf:
        label = "1"
        children = ""
    else:
        label = "eml"
        children = "".join(_node_html(child, evaluations, depth + 1) for child in (node.left, node.right))
    failure = ""
    if result is not None and result.status == "failed":
        failure = f'<span class="failure">{escape(result.visible_failure_marker or "undefined")}</span>'

    if children and depth >= DETAILS_DEPTH_THRESHOLD:
        open_attribute = " open" if depth < DETAILS_DEPTH_THRESHOLD + DETAILS_OPEN_LEVELS else ""
        children = (
            f"<details{open_attribute}><summary>subtree</summary>"
            f"<ul>{children}</ul></details>"
        )
    elif children:
        children = f"<ul>{children}</ul>"

    return (
        f'<li><span class="node" tabindex="0" title="{escape(text, quote=True)}" '
        f'data-value="{escape(text, quote=True)}">{label}</span>{failure}{children}</li>'
    )


def render_html(tree, config: dict[str, str | None], *,
                failure_summary=None, source_value=None) -> str:
    """Render the evaluated tree into one deterministic HTML document."""
    paper_title = escape(config["paper_title"] or "")
    paper_url = escape(config["paper_url"] or "", quote=True)
    links = f'<a href="{paper_url}">{paper_title}</a>'
    video_title = config.get("video_title")
    video_url = config.get("video_url")
    if video_title and video_url:
        links += (
            f' <a href="{escape(video_url, quote=True)}">'
            f'{escape(video_title)}</a>'
        )

    source = escape(tree.source_text, quote=True)
    root_result = tree.evaluations.get(tree.root.id)
    if root_result is not None and root_result.status == "ok":
        display_value = root_result.display_value
    elif root_result is None and source_value is not None and source_value.status == "ok":
        # Trees rendered without an evaluation pass may still carry a supplied
        # source value; generated CLI output always has a root result.
        display_value = source_value.display_value
    else:
        display_value = None
    if display_value is not None:
        value_block = (
            f'<p>Value: <code>{escape(display_value, quote=True)}</code></p>'
        )
    else:
        entries = failure_summary.entries if failure_summary is not None else ()
        items = "".join(
            f"<li>node {node_id}: {escape(reason)} — {escape(message)}</li>"
            for node_id, reason, message in entries
        )
        value_block = f"<p>Value: unavailable</p><ul>{items}</ul>"

    tree_html = "".join(_node_html(tree.root, tree.evaluations, 0))

    entries = failure_summary.entries if failure_summary is not None else ()
    failure_section = ""
    if entries:
        items = "".join(
            f"<li>node {node_id}: {escape(reason)} — {escape(message)}</li>"
            for node_id, reason, message in entries
        )
        failure_section = f'<section class="failures"><h2>Failures</h2><ul>{items}</ul></section>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>EML expression tree</title>
<style>
{_STYLE}
</style>
</head>
<body>
<header>
<p>{CITATION_HTML}</p>
<p>{links}</p>
<p>{escape(EXPLANATION, quote=True)}</p>
</header>
<section class="result">
<p>Source expression: <code>{source}</code></p>
{value_block}
<p>Node count: {tree.node_count}</p>
</section>
<section class="tree"><ul>{tree_html}</ul></section>
{failure_section}
</body>
</html>
"""
