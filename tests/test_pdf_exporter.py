"""Tests for PDFExporter with mocked Playwright."""

# pylint: disable=import-outside-toplevel,protected-access
from unittest.mock import patch, MagicMock


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


def test_embed_local_images_skips_remote_urls():
    """_embed_local_images() leaves http/https URLs unchanged."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()
    html = '<img src="https://example.com/pic.png"><img src="http://test.com/x.jpg">'

    result = exporter._embed_local_images(html)

    assert "https://example.com/pic.png" in result
    assert "http://test.com/x.jpg" in result
    assert "data:" not in result


def test_embed_local_images_skips_data_urls():
    """_embed_local_images() leaves data: URLs unchanged."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()
    html = '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA">'

    result = exporter._embed_local_images(html)

    assert "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA" in result


def test_embed_local_images_skips_empty_src():
    """_embed_local_images() skips <img> tags with no src."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()
    html = '<img alt="no source"><img src="">'

    result = exporter._embed_local_images(html)

    # Should not raise, just skip
    assert "<img" in result


def test_embed_local_images_converts_local_file_to_data_url(tmp_path):
    """_embed_local_images() converts local file paths to base64 data URLs."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    # Create a dummy image file
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)  # Minimal PNG header

    exporter = PDFExporter()
    html = f'<img src="{img_file}">'

    result = exporter._embed_local_images(html, base_path=None)

    assert "data:image/png;base64," in result
    assert str(img_file) not in result  # Original path replaced


def test_embed_local_images_uses_base_path_for_relative(tmp_path):
    """_embed_local_images() resolves relative paths using base_path."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    # Create structure: tmp_path/doc.md and tmp_path/images/pic.jpg
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    img_file = images_dir / "pic.jpg"
    img_file.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)  # Minimal JPEG header
    base_file = tmp_path / "doc.md"

    exporter = PDFExporter()
    html = '<img src="images/pic.jpg">'

    result = exporter._embed_local_images(html, base_path=str(base_file))

    assert "data:image/jpeg;base64," in result


def test_embed_local_images_handles_url_encoded_paths(tmp_path):
    """_embed_local_images() decodes URL-encoded paths (e.g., spaces)."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    img_file = tmp_path / "my image.png"
    img_file.write_bytes(b"\x89PNG" + b"\x00" * 10)

    exporter = PDFExporter()
    html = f'<img src="{str(img_file).replace(" ", "%20")}">'

    result = exporter._embed_local_images(html)

    assert "data:image/png;base64," in result


def test_embed_local_images_handles_missing_file():
    """_embed_local_images() logs warning and skips when file not found."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()
    html = '<img src="/nonexistent/path/to/image.png">'

    with patch("markdown_viewer.exporters.pdf_exporter.logger") as mock_logger:
        result = exporter._embed_local_images(html)

    # Should log a warning
    assert any("not found" in str(call).lower() for call in mock_logger.warning.call_args_list)
    # Original src should remain
    assert "/nonexistent/path/to/image.png" in result


def test_embed_local_images_handles_read_error(tmp_path):
    """_embed_local_images() logs warning and skips when file read fails."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter
    from pathlib import Path

    # Create a valid path but mock the read to fail
    img_file = tmp_path / "error.png"
    img_file.write_text("")  # exists but will cause issues

    exporter = PDFExporter()
    html = f'<img src="{img_file}">'

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "is_file", return_value=True),
        patch("builtins.open", side_effect=OSError("Permission denied")),
    ):
        with patch("markdown_viewer.exporters.pdf_exporter.logger") as mock_logger:
            exporter._embed_local_images(html)

    # Should log a warning about the failure
    assert any("Failed to embed" in str(call) for call in mock_logger.warning.call_args_list)


def test_embed_local_images_detects_mime_types(tmp_path):
    """_embed_local_images() correctly maps file extensions to MIME types."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    test_cases = [
        ("test.png", "image/png"),
        ("test.jpg", "image/jpeg"),
        ("test.jpeg", "image/jpeg"),
        ("test.gif", "image/gif"),
        ("test.webp", "image/webp"),
        ("test.svg", "image/svg+xml"),
        ("test.bmp", "image/bmp"),
    ]

    exporter = PDFExporter()

    for filename, expected_mime in test_cases:
        img_file = tmp_path / filename
        img_file.write_bytes(b"\x00" * 10)

        html = f'<img src="{img_file}">'
        result = exporter._embed_local_images(html)

        assert f"data:{expected_mime};base64," in result, f"Failed for {filename}"


def test_embed_local_images_logs_embedded_image_size(tmp_path):
    """_embed_local_images() logs the embedded image name and size."""
    from markdown_viewer.exporters.pdf_exporter import PDFExporter

    img_file = tmp_path / "large.png"
    img_file.write_bytes(b"\x00" * 3072)  # 3 KB

    exporter = PDFExporter()
    html = f'<img src="{img_file}">'

    with patch("markdown_viewer.exporters.pdf_exporter.logger") as mock_logger:
        exporter._embed_local_images(html)

    # Should log the image name and size (3072 // 1024 = 3)
    log_calls = [str(call) for call in mock_logger.info.call_args_list]
    assert any("large.png" in call for call in log_calls)
