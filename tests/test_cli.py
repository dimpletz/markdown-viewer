"""Tests for CLI functions (cli.py)."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# render_markdown_file
# ---------------------------------------------------------------------------


def test_render_markdown_file_keep_output(tmp_path):
    """render_markdown_file with keep_output=True saves as <name>.html."""
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Title", encoding="utf-8")

    from markdown_viewer.cli import render_markdown_file

    result = render_markdown_file(md_file, open_browser=False, keep_output=True)
    try:
        assert result.suffix == ".html"
        assert result.exists()
    finally:
        result.unlink(missing_ok=True)


def test_render_markdown_file_opens_browser(tmp_path):
    """render_markdown_file with open_browser=True calls webbrowser.open."""
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Title", encoding="utf-8")

    from markdown_viewer.cli import render_markdown_file

    with patch("webbrowser.open") as mock_open:
        result = render_markdown_file(md_file, open_browser=True)

    try:
        mock_open.assert_called_once()
        assert result.exists()
    finally:
        result.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# export_to_pdf (CLI wrapper)
# ---------------------------------------------------------------------------


def test_export_to_pdf_with_mock(tmp_path):
    """export_to_pdf() creates a PDF at the given output path (mocked exporter)."""
    md_file = tmp_path / "doc.md"
    md_file.write_text("# PDF Test", encoding="utf-8")
    out_path = tmp_path / "doc.pdf"

    def fake_export(html, path):
        Path(path).write_bytes(b"%PDF-1.4")

    with patch(
        "markdown_viewer.exporters.pdf_exporter.PDFExporter.export", side_effect=fake_export
    ), patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.close"):
        from markdown_viewer.cli import export_to_pdf

        result = export_to_pdf(md_file, output=out_path)

    assert result == out_path
    assert out_path.exists()


def test_export_to_pdf_default_output(tmp_path):
    """export_to_pdf() defaults to <filepath>.pdf when no output given."""
    md_file = tmp_path / "report.md"
    md_file.write_text("# Report", encoding="utf-8")

    def fake_export(html, path):
        Path(path).write_bytes(b"%PDF-1.4")

    with patch(
        "markdown_viewer.exporters.pdf_exporter.PDFExporter.export", side_effect=fake_export
    ), patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.close"):
        from markdown_viewer.cli import export_to_pdf

        result = export_to_pdf(md_file)

    try:
        assert result == tmp_path / "report.pdf"
        assert result.exists()
    finally:
        result.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# export_to_word (CLI wrapper)
# ---------------------------------------------------------------------------


def test_export_to_word_default_output(tmp_path):
    """export_to_word() defaults to <filepath>.docx when no output given."""
    md_file = tmp_path / "notes.md"
    md_file.write_text("# Notes", encoding="utf-8")

    from markdown_viewer.cli import export_to_word

    result = export_to_word(md_file)
    try:
        assert result == tmp_path / "notes.docx"
        assert result.exists()
    finally:
        result.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# share_via_email
# ---------------------------------------------------------------------------


def test_share_via_email_opens_mailto(tmp_path):
    """share_via_email() opens a mailto: URL in the browser."""
    md_file = tmp_path / "test.md"
    attachment = tmp_path / "test.pdf"
    attachment.write_bytes(b"%PDF-1.4")

    from markdown_viewer.cli import share_via_email

    with patch("webbrowser.open") as mock_open:
        share_via_email(md_file, attachment, "PDF")

    mock_open.assert_called_once()
    url = mock_open.call_args[0][0]
    assert url.startswith("mailto:")
    assert "subject" in url.lower()


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def test_main_no_browser(tmp_path):
    """main() with --no-browser renders HTML without opening browser."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    html_file = tmp_path / "result.html"

    with patch("sys.argv", ["mdview", str(md_file), "--no-browser"]), patch(
        "markdown_viewer.cli.render_markdown_file", return_value=html_file
    ) as mock_r:
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_r.assert_called_once()


def test_main_keep_output(tmp_path):
    """main() with --keep passes keep_output=True to render_markdown_file."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    html_file = tmp_path / "test.html"

    with patch("sys.argv", ["mdview", str(md_file), "--keep", "--no-browser"]), patch(
        "markdown_viewer.cli.render_markdown_file", return_value=html_file
    ) as mock_r:
        from markdown_viewer.cli import main

        main()

    _, kwargs = mock_r.call_args
    assert kwargs.get("keep_output") is True


def test_main_export_word(tmp_path):
    """main() with --export-word calls export_to_word."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    docx_file = tmp_path / "test.docx"

    with patch("sys.argv", ["mdview", str(md_file), "--export-word"]), patch(
        "markdown_viewer.cli.export_to_word", return_value=docx_file
    ) as mock_e:
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_e.assert_called_once()


def test_main_export_pdf(tmp_path):
    """main() with --export-pdf calls export_to_pdf."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    pdf_file = tmp_path / "test.pdf"

    with patch("sys.argv", ["mdview", str(md_file), "--export-pdf"]), patch(
        "markdown_viewer.cli.export_to_pdf", return_value=pdf_file
    ) as mock_e:
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_e.assert_called_once()


def test_main_share_pdf(tmp_path):
    """main() with --share-pdf exports PDF then opens email client."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    pdf_file = tmp_path / "test.pdf"

    with patch("sys.argv", ["mdview", str(md_file), "--share-pdf"]), patch(
        "markdown_viewer.cli.export_to_pdf", return_value=pdf_file
    ), patch("markdown_viewer.cli.share_via_email") as mock_share:
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_share.assert_called_once()


def test_main_share_word(tmp_path):
    """main() with --share-word exports Word doc then opens email client."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    docx_file = tmp_path / "test.docx"

    with patch("sys.argv", ["mdview", str(md_file), "--share-word"]), patch(
        "markdown_viewer.cli.export_to_word", return_value=docx_file
    ), patch("markdown_viewer.cli.share_via_email") as mock_share:
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_share.assert_called_once()


def test_main_file_not_found(tmp_path):
    """main() prompts for another file when target doesn't exist; returns 0 when user cancels."""
    nonexistent = tmp_path / "ghost.md"

    with patch("sys.argv", ["mdview", str(nonexistent), "--no-browser"]), patch(
        "builtins.input", side_effect=EOFError
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0


def test_main_unexpected_error_returns_2(tmp_path):
    """main() returns 2 on an unexpected exception."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with patch("sys.argv", ["mdview", str(md_file), "--no-browser"]), patch(
        "markdown_viewer.cli.render_markdown_file", side_effect=RuntimeError("boom")
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 2


def test_main_opens_browser_by_default(tmp_path):
    """main() without --no-browser/--output/--keep opens file via Flask app."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with patch("sys.argv", ["mdview", str(md_file)]), patch(
        "markdown_viewer.cli._open_in_flask_app"
    ) as mock_flask:
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_flask.assert_called_once_with(md_file)
