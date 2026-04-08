"""Tests for markdown processor."""

import pytest
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
