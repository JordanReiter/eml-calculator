"""Command-line entry point and explicit I/O boundaries."""

from __future__ import annotations

import argparse
import sys
import tomllib
import webbrowser
from pathlib import Path

from .constants import DEFAULT_CONFIG_PATH, DEFAULT_HTML_PATH
from .evaluate import (
    build_failure_summary,
    evaluate_source,
    evaluate_tree,
    root_value,
)
from .parser import parse
from .render_html import render_html
from .render_text import render_text
from .rewrite import rewrite

__all__ = ["ConfigError", "load_page_config", "main"]


class ConfigError(Exception):
    """A user-facing generation error caused by ``config.toml``."""


def load_page_config(path: str | Path | None = None) -> dict[str, str | None]:
    """Read literal link metadata from ``config.toml`` at generation time.

    Returns ``paper_title``, ``paper_url`` and optional ``video_title`` /
    ``video_url`` (``None`` when the video anchor must be omitted).
    """
    config_path = Path(path) if path is not None else Path(DEFAULT_CONFIG_PATH)
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config file {config_path}: {exc}") from exc
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {config_path}: {exc}") from exc

    paper_title = data.get("paper_title")
    paper_url = data.get("paper_url")
    if not isinstance(paper_title, str) or not paper_title.strip():
        raise ConfigError(f"{config_path}: missing required 'paper_title'")
    if not isinstance(paper_url, str) or not paper_url.strip():
        raise ConfigError(f"{config_path}: missing required 'paper_url'")

    video_title = data.get("video_title")
    video_url = data.get("video_url")
    video_title = video_title if isinstance(video_title, str) and video_title.strip() else None
    video_url = video_url if isinstance(video_url, str) and video_url.strip() else None
    if video_url is not None and video_title is None:
        raise ConfigError(f"{config_path}: 'video_url' requires a 'video_title'")

    return {
        "paper_title": paper_title,
        "paper_url": paper_url,
        "video_title": video_title,
        "video_url": video_url,
    }


def _print_summary(tree, failure_summary) -> None:
    print(f"Source expression: {tree.source_text}")
    result = root_value(tree)
    if result is not None and result.status == "ok":
        print(f"Value: {result.display_value}")
    else:
        print("Value: unavailable")
    print(f"Node count: {tree.node_count} nodes")
    if failure_summary.entries:
        print("Failures:")
        for node_id, reason, message in failure_summary.entries:
            print(f"  node {node_id}: {reason} — {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eml_calculator",
        description="Translate one arithmetic expression into an eml/1 tree.",
    )
    parser.add_argument("expression", help="closed arithmetic expression, e.g. '1+1'")
    args = parser.parse_args(argv)

    try:
        config = load_page_config(DEFAULT_CONFIG_PATH)
    except ConfigError as exc:
        print(f"generation error: {exc}", file=sys.stderr)
        return 2

    try:
        source = parse(args.expression)
    except ValueError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2

    tree = rewrite(source, args.expression)
    evaluated = evaluate_tree(tree)
    source_value = evaluate_source(source)
    failure_summary = build_failure_summary(
        evaluated,
        source_value_available=source_value.status == "ok",
    )

    Path(DEFAULT_HTML_PATH).write_text(
        render_html(
            evaluated,
            config,
            failure_summary=failure_summary,
            source_value=source_value,
        ),
        encoding="utf-8",
    )

    print(render_text(evaluated))
    _print_summary(evaluated, failure_summary)

    try:
        webbrowser.open(str(DEFAULT_HTML_PATH))
    except Exception:  # opening a browser is a best-effort boundary side effect
        pass

    result = root_value(evaluated)
    return 0 if result is not None and result.status == "ok" else 1
