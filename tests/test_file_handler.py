"""Tests for file handler."""

# pylint: disable=redefined-outer-name
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from markdown_viewer.utils.file_handler import FileHandler


@pytest.fixture
def file_handler():
    """Create a file handler instance."""
    return FileHandler()


@pytest.fixture
def temp_markdown_file():
    """Create a temporary markdown file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nThis is a test.")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_read_file(file_handler, temp_markdown_file):
    """Test reading a markdown file."""
    content = file_handler.read_file(temp_markdown_file)
    assert "# Test" in content
    assert "This is a test" in content


def test_is_markdown_file(file_handler):
    """Test markdown file detection."""
    assert file_handler.is_markdown_file("test.md")
    assert file_handler.is_markdown_file("test.markdown")
    assert not file_handler.is_markdown_file("test.txt")
    assert not file_handler.is_markdown_file("test.pdf")


def test_get_file_info(file_handler, temp_markdown_file):
    """Test getting file information."""
    info = file_handler.get_file_info(temp_markdown_file)

    assert info is not None
    assert info["name"] == os.path.basename(temp_markdown_file)
    assert info["is_markdown"] is True
    assert info["size"] > 0


def test_file_not_found(file_handler):
    """Test handling non-existent files."""
    with pytest.raises(FileNotFoundError):
        file_handler.read_file("nonexistent.md")


def test_read_file_non_markdown_raises(file_handler, tmp_path):
    """read_file() raises ValueError for non-.md extensions."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")

    with pytest.raises(ValueError, match="Not a markdown"):
        file_handler.read_file(str(txt_file))


def test_get_file_info_returns_none_for_missing(file_handler, tmp_path):
    """get_file_info() returns None for a nonexistent path."""
    result = file_handler.get_file_info(str(tmp_path / "ghost.md"))
    assert result is None


def test_list_markdown_files_non_recursive(file_handler, tmp_path):
    """list_markdown_files() returns only top-level markdown files."""
    (tmp_path / "a.md").write_text("# A")
    (tmp_path / "b.txt").write_text("plain")
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "c.md").write_text("# C")

    result = file_handler.list_markdown_files(str(tmp_path), recursive=False)
    names = {Path(p).name for p in result}

    assert "a.md" in names
    assert "c.md" not in names


def test_list_markdown_files_recursive(file_handler, tmp_path):
    """list_markdown_files(recursive=True) finds nested markdown files."""
    (tmp_path / "a.md").write_text("# A")
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "b.md").write_text("# B")

    result = file_handler.list_markdown_files(str(tmp_path), recursive=True)
    names = {Path(p).name for p in result}

    assert "a.md" in names
    assert "b.md" in names


def test_list_markdown_files_not_a_dir_raises(file_handler, tmp_path):
    """list_markdown_files() raises ValueError when given a file path."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test")

    with pytest.raises(ValueError, match="Not a directory"):
        file_handler.list_markdown_files(str(md_file))


def test_read_file_latin1_fallback(file_handler, tmp_path):
    """read_file() falls back to encoding detection when UTF-8 decoding fails."""
    # Write bytes that are valid Latin-1 but not valid UTF-8
    # 0x80-0xBF alone (without UTF-8 continuation) cause UnicodeDecodeError in 'strict' mode
    latin1_bytes = "Caf\xe9 au lait\n".encode("latin-1")
    md_file = tmp_path / "latin1.md"
    md_file.write_bytes(latin1_bytes)

    # Should not raise; chardet or fallback reads the file
    content = file_handler.read_file(str(md_file))
    assert "Caf" in content


def test_read_file_low_confidence_detection_falls_back_to_utf8(file_handler, tmp_path):
    """read_file() uses UTF-8 with errors='replace' when chardet confidence is low."""
    latin1_bytes = "Hello \xcf world\n".encode("latin-1")
    md_file = tmp_path / "ambiguous.md"
    md_file.write_bytes(latin1_bytes)

    with patch(
        "markdown_viewer.utils.file_handler.chardet.detect",
        return_value={"encoding": None, "confidence": 0.3},
    ):
        content = file_handler.read_file(str(md_file))

    assert "Hello" in content


def test_read_file_detected_encoding_lu_error_falls_back(file_handler, tmp_path):
    """read_file() falls back to UTF-8 replace when detected encoding is invalid."""
    latin1_bytes = "Caf\xe9\n".encode("latin-1")
    md_file = tmp_path / "badenc.md"
    md_file.write_bytes(latin1_bytes)

    with patch(
        "markdown_viewer.utils.file_handler.chardet.detect",
        return_value={"encoding": "nonexistent-encoding", "confidence": 0.99},
    ):
        content = file_handler.read_file(str(md_file))

    assert content is not None
