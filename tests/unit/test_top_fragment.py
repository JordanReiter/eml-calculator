"""Top-fragment loader boundary tests (T045).

The loader is an explicit generation-time I/O boundary: it returns the exact
file text on success and a clear, user-facing error naming the path on any
read failure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eml_calculator.cli import ConfigError, load_top_fragment


def test_valid_utf8_fragment_returns_exact_file_text(tmp_path):
    path = tmp_path / "top_fragment.html"
    text = "<h1>Café & tea</h1>\n<style>body { margin: 0; }</style>\n"
    path.write_text(text, encoding="utf-8")

    assert load_top_fragment(path) == text


def test_missing_fragment_raises_clear_error_naming_path(tmp_path):
    path = tmp_path / "missing_fragment.html"

    with pytest.raises(ConfigError) as exc:
        load_top_fragment(path)

    assert str(path) in str(exc.value)


def test_directory_path_raises_clear_error_naming_path(tmp_path):
    path = tmp_path / "fragment_dir"
    path.mkdir()

    with pytest.raises(ConfigError) as exc:
        load_top_fragment(path)

    assert str(path) in str(exc.value)


def test_unreadable_fragment_raises_clear_error_naming_path(tmp_path, monkeypatch):
    path = tmp_path / "unreadable.html"
    path.write_text("<h1>ok</h1>", encoding="utf-8")
    original_read_text = Path.read_text

    def failing_read_text(self, *args, **kwargs):
        if Path(self) == path:
            raise OSError("permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read_text)

    with pytest.raises(ConfigError) as exc:
        load_top_fragment(path)

    assert str(path) in str(exc.value)
    assert "permission denied" in str(exc.value)


def test_invalid_utf8_fragment_raises_clear_error_naming_path(tmp_path):
    path = tmp_path / "invalid.html"
    path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(ConfigError) as exc:
        load_top_fragment(path)

    assert str(path) in str(exc.value)
