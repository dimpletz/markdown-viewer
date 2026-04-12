"""Tests for markdown processor."""

# pylint: disable=redefined-outer-name
import pytest
from pathlib import Path

from markdown_viewer.processors.markdown_processor import MarkdownProcessor


@pytest.fixture
def processor():
    """Create a markdown processor instance."""
    return MarkdownProcessor()


def test_basic_markdown(processor):
    """Test basic markdown rendering."""
    markdown = "# Hello World\n\nThis is a test."
    html = processor.process(markdown)

    assert "Hello World" in html
    assert "<h1" in html
    assert "<p>This is a test.</p>" in html


def test_code_block(processor):
    """Test code block rendering."""
    markdown = "```python\nprint('hello')\n```"
    html = processor.process(markdown)

    assert "print" in html
    assert "hello" in html


def test_table(processor):
    """Test table rendering."""
    markdown = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
    html = processor.process(markdown)

    assert "<table>" in html
    assert "<th>Header 1</th>" in html
    assert "<td>Cell 1</td>" in html


def test_mermaid_diagram(processor):
    """Test mermaid diagram processing."""
    markdown = """```mermaid
graph TD
    A --> B
```"""
    html = processor.process(markdown)

    assert 'class="mermaid"' in html


def test_math_equation(processor):
    """Test math equation preservation."""
    markdown = "$E = mc^2$"
    html = processor.process(markdown)

    # Math should be preserved for KaTeX to render
    assert "$E = mc^2$" in html or "E = mc^2" in html


def test_process_with_full_html_option(processor):
    """process() with full_html=True wraps content in a complete HTML document."""
    html = processor.process("# Hello", {"full_html": True})

    assert "<!DOCTYPE html>" in html
    assert "Hello" in html
    assert "</html>" in html


def test_process_with_full_html_custom_title(processor):
    """process() with full_html=True and title option uses that title."""
    html = processor.process("content", {"full_html": True, "title": "My Document"})

    assert "My Document" in html


# ---------------------------------------------------------------------------
# _absolutize_md_image_paths
# ---------------------------------------------------------------------------


def test_absolutize_relative_image(processor, tmp_path):
    """Relative image paths are rewritten to absolute file paths."""
    content = "![alt](images/photo.png)"
    result = processor._absolutize_md_image_paths(content, tmp_path)
    expected_abs = (tmp_path / "images/photo.png").resolve().as_posix()
    assert expected_abs in result


def test_absolutize_already_absolute_image(processor, tmp_path):
    """Already-absolute image paths are left unchanged."""
    abs_path = str(tmp_path / "photo.png")
    content = f"![alt]({abs_path})"
    result = processor._absolutize_md_image_paths(content, tmp_path)
    assert abs_path in result


def test_absolutize_remote_url_unchanged(processor, tmp_path):
    """Remote http/https URLs are left unchanged."""
    content = "![alt](https://example.com/img.png)"
    result = processor._absolutize_md_image_paths(content, tmp_path)
    assert result == content


def test_absolutize_data_uri_unchanged(processor, tmp_path):
    """data: URIs are left unchanged."""
    content = "![alt](data:image/png;base64,abc)"
    result = processor._absolutize_md_image_paths(content, tmp_path)
    assert result == content


def test_absolutize_file_uri_unchanged(processor, tmp_path):
    """file:// URIs are left unchanged."""
    content = "![alt](file:///some/path.png)"
    result = processor._absolutize_md_image_paths(content, tmp_path)
    assert result == content


# ---------------------------------------------------------------------------
# _resolve_includes
# ---------------------------------------------------------------------------


def test_resolve_includes_basic(processor, tmp_path):
    """![[file.md]] is replaced with the file's content."""
    child = tmp_path / "child.md"
    child.write_text("## Child Heading\n", encoding="utf-8")
    content = "# Parent\n\n![[child.md]]\n"
    result = processor._resolve_includes(content, tmp_path, allowed_base=tmp_path)
    assert "## Child Heading" in result
    assert "![[" not in result


def test_resolve_includes_nested(processor, tmp_path):
    """Nested ![[]] includes are resolved recursively."""
    grandchild = tmp_path / "grand.md"
    grandchild.write_text("grandchild content", encoding="utf-8")
    child = tmp_path / "child.md"
    child.write_text("![[grand.md]]", encoding="utf-8")
    content = "![[child.md]]"
    result = processor._resolve_includes(content, tmp_path, allowed_base=tmp_path)
    assert "grandchild content" in result


def test_resolve_includes_file_not_found(processor, tmp_path):
    """Missing include file produces a warning callout."""
    content = "![[nonexistent.md]]"
    result = processor._resolve_includes(content, tmp_path, allowed_base=tmp_path)
    assert "Include not found" in result
    assert "nonexistent.md" in result


def test_resolve_includes_wrong_extension(processor, tmp_path):
    """Non-markdown include is ignored with a warning callout."""
    txt = tmp_path / "data.txt"
    txt.write_text("secret", encoding="utf-8")
    content = "![[data.txt]]"
    result = processor._resolve_includes(content, tmp_path, allowed_base=tmp_path)
    assert "secret" not in result
    assert "Include ignored" in result


def test_resolve_includes_circular(processor, tmp_path):
    """Circular includes are detected and produce a warning callout."""
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("![[b.md]]", encoding="utf-8")
    b.write_text("![[a.md]]", encoding="utf-8")
    content = "![[a.md]]"
    result = processor._resolve_includes(content, tmp_path, allowed_base=tmp_path)
    assert "Circular include skipped" in result


def test_resolve_includes_path_traversal_blocked(processor, tmp_path):
    """Includes that escape allowed_base are blocked with a warning callout."""
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("sensitive data", encoding="utf-8")
    content = "![[../outside.md]]"
    result = processor._resolve_includes(content, allowed, allowed_base=allowed)
    assert "sensitive data" not in result
    assert "Include blocked" in result


def test_resolve_includes_depth_limit(processor, tmp_path):
    """Exceeding MAX_INCLUDE_DEPTH returns content unchanged (no infinite recursion)."""
    result = processor._resolve_includes(
        "![[x.md]]", tmp_path, allowed_base=tmp_path, depth=processor._MAX_INCLUDE_DEPTH
    )
    # At max depth the pattern is not replaced at all
    assert "![[x.md]]" in result


def test_resolve_includes_absolute_path(processor, tmp_path):
    """Absolute paths inside allowed_base are resolved correctly."""
    child = tmp_path / "abs_child.md"
    child.write_text("absolute include content", encoding="utf-8")
    content = f"![[{child}]]"
    result = processor._resolve_includes(content, tmp_path, allowed_base=tmp_path)
    assert "absolute include content" in result


def test_process_with_base_dir_resolves_includes(processor, tmp_path):
    """process() resolves ![[]] when base_dir option is provided."""
    child = tmp_path / "note.md"
    child.write_text("## Included Note\n", encoding="utf-8")
    content = "# Doc\n\n![[note.md]]\n"
    html = processor.process(content, {"base_dir": str(tmp_path), "allowed_base": str(tmp_path)})
    assert "Included Note" in html
