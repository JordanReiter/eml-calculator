"""CLI integration tests (T012, T023, T030, T031, T038)."""

from __future__ import annotations

import re

import pytest

from eml_calculator import cli


def configure(tmp_path, monkeypatch, *, video: bool = True, paper_title: str = "the paper"):
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
    output = tmp_path / "out.html"
    if output.exists():
        output.unlink()
    monkeypatch.setattr(cli, "DEFAULT_HTML_PATH", str(output), raising=False)
    monkeypatch.setattr(cli, "DEFAULT_CONFIG_PATH", str(config), raising=False)
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


def test_configured_links_and_source_value_appear_above_tree(tmp_path, monkeypatch, capsys):
    output = configure(tmp_path, monkeypatch, video=True)
    code = cli.main(["1+1"])
    captured = capsys.readouterr()
    html = output.read_text(encoding="utf-8")

    assert code == 0
    anchors = re.findall(r'<a href="([^"]+)">([^<]+)</a>', html)
    assert anchors == [
        ("https://arxiv.org/abs/2603.21852", "the paper"),
        ("https://www.youtube.com/watch?v=LxVW3b8jVdE", "the video"),
    ]
    assert html.count("<a ") == 2
    assert html.index("Odrzywołek") < html.index("<a ")
    assert html.index("<a ") < html.index("This tree is")
    assert html.index("This tree is") < html.index("Source expression:")
    assert html.index("Source expression:") < html.index('<section class="tree">')
    assert "Source expression: <code>1+1</code>" in html
    assert "Value: <code>2</code>" in html
    assert "Source expression: 1+1" in captured.out
    assert "Value: 2" in captured.out


def test_omitted_video_config_renders_only_paper_anchor(tmp_path, monkeypatch, capsys):
    output = configure(tmp_path, monkeypatch, video=False)
    code = cli.main(["1+1"])
    capsys.readouterr()
    html = output.read_text(encoding="utf-8")
    assert code == 0
    assert re.findall(r'<a href="([^"]+)">([^<]+)</a>', html) == [
        ("https://arxiv.org/abs/2603.21852", "the paper")
    ]
    assert "the video" not in html
    assert "placeholder" not in html.lower()


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
