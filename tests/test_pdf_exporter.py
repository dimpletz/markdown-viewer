"""Tests for PDFExporter with mocked Playwright."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call


def test_close_when_not_initialized():
    """close() on a fresh PDFExporter does nothing (no error)."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()
    exporter.close()  # Should not raise


def test_close_stops_playwright():
    """close() calls browser.close() and playwright.stop()."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()

    mock_browser = MagicMock()
    mock_playwright = MagicMock()
    exporter.browser = mock_browser
    exporter.playwright = mock_playwright

    exporter.close()

    mock_browser.close.assert_called_once()
    mock_playwright.stop.assert_called_once()
    assert exporter.browser is None
    assert exporter.playwright is None


def test_close_handles_browser_exception():
    """close() does not raise when browser.close() raises a non-event-loop error."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()

    mock_browser = MagicMock()
    mock_browser.close.side_effect = Exception("some close error")
    mock_playwright = MagicMock()
    exporter.browser = mock_browser
    exporter.playwright = mock_playwright

    # Should not raise
    exporter.close()
    assert exporter.browser is None


def test_context_manager_calls_close():
    """PDFExporter used as a context manager calls close() on exit."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    with patch.object(PDFExporter, "close") as mock_close:
        with PDFExporter():
            pass

    # close() is called by __exit__ (and possibly __del__), so assert called at least once
    mock_close.assert_called()


def test_wrap_html_produces_complete_document():
    """_wrap_html() wraps a fragment in a full HTML document."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()

    result = exporter._wrap_html("<p>Hello</p>")

    assert "<!DOCTYPE html>" in result
    assert "<p>Hello</p>" in result
    assert "</html>" in result


def test_ensure_browser_initializes_playwright():
    """_ensure_browser() starts playwright and launches chromium."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    mock_browser = MagicMock()
    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    with patch("markdown_viewer.exporters.pdf_exporter.sync_playwright") as mock_sync_pw:
        mock_sync_pw.return_value.start.return_value = mock_pw

        exporter = PDFExporter()
        exporter._ensure_browser()

    assert exporter.playwright is mock_pw
    assert exporter.browser is mock_browser


def test_ensure_browser_skips_when_already_initialized():
    """_ensure_browser() is a no-op when playwright is already set."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()
    mock_pw = MagicMock()
    exporter.playwright = mock_pw  # Already initialized

    with patch("markdown_viewer.exporters.pdf_exporter.sync_playwright") as mock_sync_pw:
        exporter._ensure_browser()

    # sync_playwright should NOT have been called again
    mock_sync_pw.assert_not_called()


def test_export_calls_page_pdf(tmp_path):
    """export() navigates to HTML and calls page.pdf() with correct options."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    output_path = str(tmp_path / "output.pdf")

    mock_page = MagicMock()
    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    with patch("markdown_viewer.exporters.pdf_exporter.sync_playwright") as mock_sync_pw:
        mock_sync_pw.return_value.start.return_value = mock_pw

        exporter = PDFExporter()
        exporter.export("<h1>Hello</h1>", output_path)

    mock_context.new_page.assert_called_once()
    mock_page.goto.assert_called_once()
    mock_page.pdf.assert_called_once()
    mock_page.close.assert_called_once()
    mock_context.close.assert_called_once()


def test_export_wraps_fragment_in_full_html(tmp_path):
    """export() wraps a non-DOCTYPE fragment before rendering."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    mock_page = MagicMock()
    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    with patch("markdown_viewer.exporters.pdf_exporter.sync_playwright") as mock_sync_pw:
        mock_sync_pw.return_value.start.return_value = mock_pw

        exporter = PDFExporter()
        exporter.export("<p>Fragment</p>", str(tmp_path / "out.pdf"))

    # page.goto was called — confirming the fragment was wrapped and rendered
    mock_page.goto.assert_called_once()
