"""Tests for exporters."""

import pytest
import os
import tempfile
from markdown_viewer.exporters.pdf_exporter import PDFExporter
from markdown_viewer.exporters.word_exporter import WordExporter


@pytest.fixture
def sample_html():
    """Sample HTML content."""
    return """
    <h1>Test Document</h1>
    <p>This is a test paragraph.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    """


@pytest.fixture
def sample_markdown():
    """Sample markdown content."""
    return """
# Test Document

This is a test paragraph.

- Item 1
- Item 2
"""


def test_pdf_export(sample_html):
    """Test PDF export."""
    exporter = PDFExporter()
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        output_path = f.name
    
    try:
        exporter.export(sample_html, output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_word_export(sample_html, sample_markdown):
    """Test Word export."""
    exporter = WordExporter()
    
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        output_path = f.name
    
    try:
        exporter.export(sample_html, sample_markdown, output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_word_export_complex_elements():
    """Word exporter handles h2-h4, ul, ol, pre, blockquote, table, img elements."""
    html = """
    <html><body>
        <h1>Title</h1>
        <h2>Section</h2>
        <h3>Subsection</h3>
        <h4>Details</h4>
        <p>A paragraph with content.</p>
        <ul><li>Bullet one</li><li>Bullet two</li></ul>
        <ol><li>First</li><li>Second</li></ol>
        <pre>def hello():\n    return "world"</pre>
        <blockquote>An inspiring quote.</blockquote>
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>foo</td><td>bar</td></tr>
        </table>
        <img src="nonexistent.png" alt="Missing image">
        <div><p>Nested paragraph inside div.</p></div>
    </body></html>
    """

    exporter = WordExporter()

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        output_path = f.name

    try:
        exporter.export(html, "", output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
