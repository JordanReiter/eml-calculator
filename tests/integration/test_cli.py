"""CLI integration tests (T012, T023, T030, T031, T038)."""

from __future__ import annotations

import re

import pytest

from eml_calculator import cli

FRAGMENT = """<h1 id="heading">Owner heading</h1>
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


def configure(
    tmp_path,
    monkeypatch,
    *,
    video: bool = True,
    paper_title: str = "the paper",
    fragment: str = FRAGMENT,
    with_fragment: bool = True,
):
    config = tmp_path / "config.toml"
    config.write_text(
        f'paper_title = "{paper_title}"\n'
        'paper_url = "https://arxiv.org/abs/2603.21852"\n'
        + (
            'video_title = "the video"\n'
            'video_url = "https://www.youtube.com/watch?v=LxVW3b8jVdE"\n'
            if video
            else ""
        ),
        encoding="utf-8",
    )
    fragment_path = tmp_path / "top_fragment.html"
    if with_fragment:
        fragment_path.write_text(fragment, encoding="utf-8")
    elif fragment_path.exists():
        fragment_path.unlink()
    output = tmp_path / "out.html"
    if output.exists():
        output.unlink()
    monkeypatch.setattr(cli, "DEFAULT_HTML_PATH", str(output), raising=False)
    monkeypatch.setattr(cli, "DEFAULT_CONFIG_PATH", str(config), raising=False)
    monkeypatch.setattr(
        cli, "DEFAULT_TOP_FRAGMENT_PATH", str(fragment_path), raising=False
    )
    monkeypatch.setattr(cli.webbrowser, "open", lambda url: True)
    return output


@pytest.fixture
def isolated_output(tmp_path, monkeypatch):
    return configure(tmp_path, monkeypatch, video=False), []


def html_node_labels(html: str) -> list[str]:
    return re.findall(r'<span class="node"[^>]*>(eml|1)</span>', html)


def test_success_path_prints_tree_summary_writes_html_and_opens_it(isolated_output, capsys):
    output, _ = isolated_output
    opened = []
    original_open = cli.webbrowser.open
    cli.webbrowser.open = lambda url: opened.append(url) or True
    try:
        code = cli.main(["1+1"])
    finally:
        cli.webbrowser.open = original_open

    captured = capsys.readouterr()
    assert code == 0
    assert "eml(" in captured.out
    assert re.search(r"^\s*1\s*$", captured.out, flags=re.MULTILINE)
    assert "Source expression: 1+1" in captured.out
    assert "Value: 2" in captured.out
    assert "Node count: 27" in captured.out
    assert output.exists()
    assert output.read_text(encoding="utf-8").count("eml") > 1
    assert opened == [str(output)]


def test_text_nodes_html_nodes_and_node_count_match(tmp_path, monkeypatch, capsys):
    output = configure(tmp_path, monkeypatch, video=False)
    code = cli.main(["1+1"])
    captured = capsys.readouterr()
    assert code == 0

    tree_section = captured.out.split("Source expression:")[0]
    text_labels = []
    for line in tree_section.splitlines():
        stripped = line.strip()
        if stripped == "eml(":
            text_labels.append("eml")
        elif stripped == "1":
            text_labels.append("1")
    node_count = int(re.search(r"Node count: (\d+)", captured.out).group(1))
    html_labels = html_node_labels(output.read_text(encoding="utf-8"))
    assert text_labels == html_labels
    assert len(text_labels) == node_count == len(html_labels)


def test_fragment_header_links_source_and_value_appear_above_tree(tmp_path, monkeypatch, capsys):
    output = configure(tmp_path, monkeypatch, video=True)
    code = cli.main(["1+1"])
    captured = capsys.readouterr()
    html = output.read_text(encoding="utf-8")

    assert code == 0
    anchors = re.findall(r'<a href="([^"]*)">([^<]*)</a>', html)
    assert anchors == [
        ("https://arxiv.org/abs/2603.21852", "the paper"),
        ("https://www.youtube.com/watch?v=LxVW3b8jVdE", "the video"),
    ]
    assert html.count("<a ") == 2
    positions = [html.index(landmark) for landmark in FRAGMENT_LANDMARKS]
    assert positions == sorted(positions)
    assert positions[-1] < html.index("Source expression:")
    assert html.index("Source expression:") < html.index("Value:")
    assert html.index("Value:") < html.index('<section class="tree">')
    assert "Source expression: <code>1+1</code>" in html
    assert "Value: <code>2</code>" in html
    assert "Source expression: 1+1" in captured.out
    assert "Value: 2" in captured.out
    assert "Odrzywołek" not in html


def test_omitted_video_config_substitutes_empty_strings_without_omission(tmp_path, monkeypatch):
    output = configure(tmp_path, monkeypatch, video=False)
    code = cli.main(["1+1"])
    html = output.read_text(encoding="utf-8")

    assert code == 0
    assert re.findall(r'<a href="([^"]*)">([^<]*)</a>', html) == [
        ("https://arxiv.org/abs/2603.21852", "the paper"),
        ("", ""),
    ]
    assert '<p class="video">Video: <a href="">' in html
    assert "{{" not in html and "}}" not in html
    for landmark in FRAGMENT_LANDMARKS:
        assert landmark in html


def test_repeated_runs_are_byte_identical(tmp_path, monkeypatch, capsys):
    output = configure(tmp_path, monkeypatch, video=True)
    assert cli.main(["1+1"]) == 0
    capsys.readouterr()
    first = output.read_bytes()
    output.unlink()
    assert cli.main(["1+1"]) == 0
    capsys.readouterr()
    assert output.read_bytes() == first


@pytest.mark.parametrize("text, element", [
    ("tau", "tau"),
    ("phi", "phi"),
    ("x", "x"),
    ("0x10", "0x10"),
    ("0b10", "0b10"),
    ("1_000", "1_000"),
    ("2**3", "*"),
    ("floor(1)", "floor"),
])
def test_rejected_input_exits_two_with_clear_error_and_no_artifact(
    tmp_path, monkeypatch, capsys, text, element
):
    output = configure(tmp_path, monkeypatch, video=False)
    code = cli.main([text])
    captured = capsys.readouterr()
    assert code == 2
    assert element in captured.err
    assert captured.out == ""
    assert not output.exists()


def test_invalid_config_exits_two_with_generation_error(tmp_path, monkeypatch, capsys):
    config = tmp_path / "config.toml"
    config.write_text('paper_url = "https://arxiv.org/abs/2603.21852"\n', encoding="utf-8")
    output = tmp_path / "out.html"
    monkeypatch.setattr(cli, "DEFAULT_HTML_PATH", str(output), raising=False)
    monkeypatch.setattr(cli, "DEFAULT_CONFIG_PATH", str(config), raising=False)
    code = cli.main(["1+1"])
    captured = capsys.readouterr()
    assert code == 2
    assert "paper_title" in captured.err
    assert not output.exists()


def test_node_failure_exits_one_and_writes_failure_artifact(tmp_path, monkeypatch, capsys):
    output = configure(tmp_path, monkeypatch, video=False)
    code = cli.main(["1/0"])
    captured = capsys.readouterr()
    html = output.read_text(encoding="utf-8")
    assert code == 1
    assert "eml(" in captured.out
    assert "undefined" in captured.out
    assert "Node count:" in captured.out
    assert 'class="failure"' in html
    assert "node 0: undefined" in html
    assert "nan" not in html.lower()
    assert "inf" not in html.lower()


@pytest.mark.parametrize("video", [True, False])
def test_cli_fragment_header_and_anchors_with_and_without_video(
    tmp_path, monkeypatch, video
):
    output = configure(tmp_path, monkeypatch, video=video)
    code = cli.main(["1+1"])
    html = output.read_text(encoding="utf-8")

    assert code == 0
    positions = [html.index(landmark) for landmark in FRAGMENT_LANDMARKS]
    assert positions == sorted(positions)
    assert positions[-1] < html.index("Source expression:")
    assert html.index("Source expression:") < html.index('<section class="tree">')
    # The fragment owns both rows; omitted video config never removes one.
    assert html.count("<a ") == 2
    assert "{{" not in html and "}}" not in html
    expected_anchors = [("https://arxiv.org/abs/2603.21852", "the paper")]
    if video:
        expected_anchors.append(
            ("https://www.youtube.com/watch?v=LxVW3b8jVdE", "the video")
        )
    else:
        expected_anchors.append(("", ""))
    assert re.findall(r'<a href="([^"]*)">([^<]*)</a>', html) == expected_anchors


def test_missing_fragment_exits_two_with_generation_error_and_no_artifact(
    tmp_path, monkeypatch, capsys
):
    output = configure(tmp_path, monkeypatch, with_fragment=False)
    fragment_path = tmp_path / "top_fragment.html"

    code = cli.main(["1+1"])
    captured = capsys.readouterr()

    assert code == 2
    assert "generation error" in captured.err.lower()
    assert str(fragment_path) in captured.err
    assert not output.exists()


def test_unreadable_fragment_exits_two_with_generation_error_and_no_artifact(
    tmp_path, monkeypatch, capsys
):
    output = configure(tmp_path, monkeypatch)
    fragment_path = tmp_path / "top_fragment.html"
    original_load = cli.load_top_fragment

    def failing_load(path=None):
        raise cli.ConfigError(f"cannot read fragment {fragment_path}: permission denied")

    monkeypatch.setattr(cli, "load_top_fragment", failing_load)
    try:
        code = cli.main(["1+1"])
    finally:
        monkeypatch.setattr(cli, "load_top_fragment", original_load)
    captured = capsys.readouterr()

    assert code == 2
    assert "generation error" in captured.err.lower()
    assert str(fragment_path) in captured.err
    assert not output.exists()


def test_fragment_output_is_byte_identical_across_runs(tmp_path, monkeypatch, capsys):
    fragment = FRAGMENT.replace("<h1", '<h1 data-owner="yes"')
    output = configure(tmp_path, monkeypatch, fragment=fragment)

    assert cli.main(["1+1"]) == 0
    capsys.readouterr()
    first = output.read_bytes()
    assert cli.main(["1+1"]) == 0
    capsys.readouterr()

    assert output.read_bytes() == first
