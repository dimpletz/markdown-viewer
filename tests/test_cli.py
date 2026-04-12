"""Tests for CLI functions (cli.py)."""

# pylint: disable=import-outside-toplevel
from pathlib import Path
from unittest.mock import patch

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

    def fake_export(_html, path):
        Path(path).write_bytes(b"%PDF-1.4")

    with (
        patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.export", side_effect=fake_export),
        patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.close"),
    ):
        from markdown_viewer.cli import export_to_pdf

        result = export_to_pdf(md_file, output=out_path)

    assert result == out_path
    assert out_path.exists()


def test_export_to_pdf_default_output(tmp_path):
    """export_to_pdf() defaults to <filepath>.pdf when no output given."""
    md_file = tmp_path / "report.md"
    md_file.write_text("# Report", encoding="utf-8")

    def fake_export(_html, path):
        Path(path).write_bytes(b"%PDF-1.4")

    with (
        patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.export", side_effect=fake_export),
        patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.close"),
    ):
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

    with (
        patch("sys.argv", ["mdview", str(md_file), "--no-browser"]),
        patch("markdown_viewer.cli.render_markdown_file", return_value=html_file) as mock_r,
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_r.assert_called_once()


def test_main_keep_output(tmp_path):
    """main() with --keep passes keep_output=True to render_markdown_file."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    html_file = tmp_path / "test.html"

    with (
        patch("sys.argv", ["mdview", str(md_file), "--keep", "--no-browser"]),
        patch("markdown_viewer.cli.render_markdown_file", return_value=html_file) as mock_r,
    ):
        from markdown_viewer.cli import main

        main()

    _, kwargs = mock_r.call_args
    assert kwargs.get("keep_output") is True


def test_main_export_word(tmp_path):
    """main() with --export-word calls export_to_word."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    docx_file = tmp_path / "test.docx"

    with (
        patch("sys.argv", ["mdview", str(md_file), "--export-word"]),
        patch("markdown_viewer.cli.export_to_word", return_value=docx_file) as mock_e,
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_e.assert_called_once()


def test_main_export_pdf(tmp_path):
    """main() with --export-pdf calls export_to_pdf."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    pdf_file = tmp_path / "test.pdf"

    with (
        patch("sys.argv", ["mdview", str(md_file), "--export-pdf"]),
        patch("markdown_viewer.cli.export_to_pdf", return_value=pdf_file) as mock_e,
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_e.assert_called_once()


def test_main_share_pdf(tmp_path):
    """main() with --share-pdf exports PDF then opens email client."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    pdf_file = tmp_path / "test.pdf"

    with (
        patch("sys.argv", ["mdview", str(md_file), "--share-pdf"]),
        patch("markdown_viewer.cli.export_to_pdf", return_value=pdf_file),
        patch("markdown_viewer.cli.share_via_email") as mock_share,
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_share.assert_called_once()


def test_main_share_word(tmp_path):
    """main() with --share-word exports Word doc then opens email client."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    docx_file = tmp_path / "test.docx"

    with (
        patch("sys.argv", ["mdview", str(md_file), "--share-word"]),
        patch("markdown_viewer.cli.export_to_word", return_value=docx_file),
        patch("markdown_viewer.cli.share_via_email") as mock_share,
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_share.assert_called_once()


def test_main_file_not_found(tmp_path):
    """main() prompts for another file when target doesn't exist; returns 0 when user cancels."""
    nonexistent = tmp_path / "ghost.md"

    with (
        patch("sys.argv", ["mdview", str(nonexistent), "--no-browser"]),
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", side_effect=EOFError),
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0


def test_main_unexpected_error_returns_2(tmp_path):
    """main() returns 2 on an unexpected exception."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", str(md_file), "--no-browser"]),
        patch("markdown_viewer.cli.render_markdown_file", side_effect=RuntimeError("boom")),
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 2


def test_main_opens_browser_by_default(tmp_path):
    """main() without --no-browser/--output/--keep opens file via Flask app."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", str(md_file)]),
        patch("markdown_viewer.cli._open_in_flask_app") as mock_flask,
        patch("sys.stdout.isatty", return_value=True),
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 0
    mock_flask.assert_called_once_with(md_file, port=5000, browser=None)


# ---------------------------------------------------------------------------
# _embed_local_images
# ---------------------------------------------------------------------------


def test_embed_local_images_png(tmp_path):
    """_embed_local_images embeds a relative PNG path as a base64 data URI."""
    img = tmp_path / "photo.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)

    from markdown_viewer.cli import _embed_local_images

    html = f'<img src="photo.png" alt="photo">'
    result = _embed_local_images(html, tmp_path)
    assert result.startswith('<img src="data:image/png;base64,')


def test_embed_local_images_absolute_path(tmp_path):
    """_embed_local_images handles absolute file paths."""
    img = tmp_path / "logo.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 5)

    from markdown_viewer.cli import _embed_local_images

    html = f'<img src="{img}" alt="logo">'
    result = _embed_local_images(html, tmp_path)
    assert "data:image/jpeg;base64," in result


def test_embed_local_images_url_encoded_spaces(tmp_path):
    """_embed_local_images URL-decodes %20 in paths before reading."""
    subdir = tmp_path / "My Images"
    subdir.mkdir()
    img = subdir / "pic.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)

    from markdown_viewer.cli import _embed_local_images

    # Markdown might produce a %20-encoded path
    html = '<img src="My%20Images/pic.png" alt="pic">'
    result = _embed_local_images(html, tmp_path)
    assert "data:image/png;base64," in result


def test_embed_local_images_skips_http(tmp_path):
    """_embed_local_images leaves remote http:// URLs unchanged."""
    from markdown_viewer.cli import _embed_local_images

    html = '<img src="https://example.com/img.png" alt="remote">'
    result = _embed_local_images(html, tmp_path)
    assert result == html


def test_embed_local_images_skips_data_uri(tmp_path):
    """_embed_local_images leaves existing data: URIs unchanged."""
    from markdown_viewer.cli import _embed_local_images

    html = '<img src="data:image/png;base64,abc" alt="data">'
    result = _embed_local_images(html, tmp_path)
    assert result == html


def test_embed_local_images_missing_file(tmp_path):
    """_embed_local_images leaves the src unchanged when file is missing."""
    from markdown_viewer.cli import _embed_local_images

    html = '<img src="missing.png" alt="missing">'
    result = _embed_local_images(html, tmp_path)
    assert result == html


def test_embed_local_images_unsupported_extension(tmp_path):
    """_embed_local_images leaves non-image extensions unchanged."""
    txt = tmp_path / "file.txt"
    txt.write_text("hello", encoding="utf-8")

    from markdown_viewer.cli import _embed_local_images

    html = '<img src="file.txt" alt="txt">'
    result = _embed_local_images(html, tmp_path)
    assert result == html


def test_render_markdown_file_embeds_images(tmp_path):
    """render_markdown_file embeds local images as data URIs in the output HTML."""
    img = tmp_path / "banner.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Doc\n\n![banner](banner.png)", encoding="utf-8")

    from markdown_viewer.cli import render_markdown_file

    result = render_markdown_file(md_file, open_browser=False, keep_output=True)
    try:
        html = result.read_text(encoding="utf-8")
        assert "data:image/png;base64," in html
    finally:
        result.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# URL rejection in _resolve_file
# ---------------------------------------------------------------------------


def test_main_http_url_rejected_noninteractive(tmp_path):
    """main() with an http:// URL prints an error and exits 1 in non-interactive mode."""
    with (
        patch("sys.argv", ["mdview", "http://example.com/doc.md"]),
        patch("sys.stdin.isatty", return_value=False),
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 1


def test_main_https_url_rejected_noninteractive(tmp_path):
    """main() with an https:// URL prints an error and exits 1 in non-interactive mode."""
    with (
        patch("sys.argv", ["mdview", "https://example.com/doc.md"]),
        patch("sys.stdin.isatty", return_value=False),
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 1


def test_main_ftp_url_rejected_noninteractive(tmp_path):
    """main() with an ftp:// URL prints an error and exits 1 in non-interactive mode."""
    with (
        patch("sys.argv", ["mdview", "ftp://files.example.com/doc.md"]),
        patch("sys.stdin.isatty", return_value=False),
    ):
        from markdown_viewer.cli import main

        result = main()

    assert result == 1


def test_main_url_rejected_then_prompted(tmp_path, capsys):
    """main() with a URL in interactive mode shows message then re-prompts."""
    md_file = tmp_path / "good.md"
    md_file.write_text("# Good", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", "https://example.com/doc.md"]),
        patch("sys.stdin.isatty", return_value=True),
        # First prompt returns a valid local file; second call should not happen
        patch("builtins.input", side_effect=[str(md_file), EOFError]),
        patch("markdown_viewer.cli._open_in_flask_app"),
    ):
        from markdown_viewer.cli import main

        result = main()

    captured = capsys.readouterr()
    assert "Only local markdown files are supported" in captured.out
    assert result == 0


# ---------------------------------------------------------------------------
# _stop_server
# ---------------------------------------------------------------------------


def test_stop_server_success_via_http():
    """_stop_server() returns 0 when the HTTP shutdown endpoint responds."""
    from unittest.mock import MagicMock, patch

    from markdown_viewer.cli import _stop_server

    mock_conn = MagicMock()
    with patch("http.client.HTTPConnection", return_value=mock_conn):
        result = _stop_server(port=5000)

    assert result == 0
    mock_conn.request.assert_called_once_with("GET", "/api/shutdown")


def test_stop_server_no_pid_file(tmp_path):
    """_stop_server() returns 0 with a message when no PID file exists."""
    from unittest.mock import patch

    from markdown_viewer.cli import _stop_server

    # HTTP call fails, no PID file
    with (
        patch("http.client.HTTPConnection", side_effect=Exception("refused")),
        patch("markdown_viewer.server.pid_file_path", return_value=tmp_path / "no_pid.pid"),
    ):
        result = _stop_server(port=9999)

    assert result == 0


def test_stop_server_via_pid_file(tmp_path):
    """_stop_server() kills the process using a PID file when HTTP returns no response."""
    import os
    from unittest.mock import patch

    from markdown_viewer.cli import _stop_server

    pid_file = tmp_path / "mdview_9999.pid"
    pid_file.write_text(str(os.getpid()), encoding="utf-8")

    with (
        patch("http.client.HTTPConnection", side_effect=Exception("refused")),
        patch("markdown_viewer.server.pid_file_path", return_value=pid_file),
        patch("os.kill"),  # don't actually send a signal to ourselves
    ):
        result = _stop_server(port=9999)

    assert result == 0


def test_stop_server_stale_pid_file(tmp_path):
    """_stop_server() removes a stale PID file and returns 0."""
    from unittest.mock import patch

    from markdown_viewer.cli import _stop_server

    pid_file = tmp_path / "mdview_9999.pid"
    pid_file.write_text("99999999", encoding="utf-8")  # PID doesn't exist

    with (
        patch("http.client.HTTPConnection", side_effect=Exception("refused")),
        patch("markdown_viewer.server.pid_file_path", return_value=pid_file),
        # Simulate the OS reporting the PID doesn't exist (cross-platform)
        patch("os.kill", side_effect=ProcessLookupError("no such process")),
    ):
        result = _stop_server(port=9999)

    assert result == 0
    assert not pid_file.exists()


def test_main_stop_flag(tmp_path):
    """main() with --stop calls _stop_server and returns its exit code."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    with (
        patch("sys.argv", ["mdview", "--stop"]),
        patch("markdown_viewer.cli._stop_server", return_value=0) as mock_stop,
    ):
        result = main()

    assert result == 0
    mock_stop.assert_called_once()


# ---------------------------------------------------------------------------
# _resolve_file branching
# ---------------------------------------------------------------------------


def test_main_directory_path_noninteractive(tmp_path):
    """main() with a directory path exits 1 in non-interactive mode."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    with (
        patch("sys.argv", ["mdview", str(tmp_path)]),
        patch("sys.stdin.isatty", return_value=False),
    ):
        result = main()

    assert result == 1


def test_main_no_extension_noninteractive(tmp_path):
    """main() with a file with no extension exits 1 in non-interactive mode."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    bare = tmp_path / "README"
    bare.write_text("hello", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", str(bare)]),
        patch("sys.stdin.isatty", return_value=False),
    ):
        result = main()

    assert result == 1


def test_main_unsupported_extension_noninteractive(tmp_path):
    """main() with an unsupported extension exits 1 in non-interactive mode."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    txt = tmp_path / "notes.txt"
    txt.write_text("hello", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", str(txt)]),
        patch("sys.stdin.isatty", return_value=False),
    ):
        result = main()

    assert result == 1


def test_main_no_file_noninteractive():
    """main() with no file argument exits 1 in non-interactive mode."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    with (
        patch("sys.argv", ["mdview"]),
        patch("sys.stdin.isatty", return_value=False),
    ):
        result = main()

    assert result == 1


# ---------------------------------------------------------------------------
# main() exception handlers
# ---------------------------------------------------------------------------


def test_main_import_error_returns_1(tmp_path):
    """main() returns 1 when an ImportError is raised during processing."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", str(md_file), "--no-browser"]),
        patch(
            "markdown_viewer.cli.render_markdown_file",
            side_effect=ImportError("missing dep"),
        ),
    ):
        result = main()

    assert result == 1


def test_main_file_not_found_error_returns_1(tmp_path):
    """main() returns 1 when FileNotFoundError is raised during processing."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", str(md_file), "--no-browser"]),
        patch(
            "markdown_viewer.cli.render_markdown_file",
            side_effect=FileNotFoundError("gone"),
        ),
    ):
        result = main()

    assert result == 1


def test_main_non_interactive_stdout_not_tty(tmp_path):
    """main() in non-interactive stdout renders HTML without browser."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    html_file = tmp_path / "test.html"

    with (
        patch("sys.argv", ["mdview", str(md_file)]),
        patch("sys.stdout.isatty", return_value=False),
        patch("markdown_viewer.cli.render_markdown_file", return_value=html_file) as mock_r,
    ):
        result = main()

    assert result == 0
    _, kwargs = mock_r.call_args
    assert kwargs.get("open_browser") is False
    assert kwargs.get("keep_output") is True


# ---------------------------------------------------------------------------
# render_markdown_file with explicit output path
# ---------------------------------------------------------------------------


def test_render_markdown_file_explicit_output(tmp_path):
    """render_markdown_file writes to the given output path."""
    from markdown_viewer.cli import render_markdown_file

    md_file = tmp_path / "doc.md"
    md_file.write_text("# Title\n\nHello", encoding="utf-8")
    out_file = tmp_path / "output.html"

    result = render_markdown_file(md_file, output=out_file, open_browser=False)
    assert result == out_file.resolve()
    assert out_file.exists()


# ---------------------------------------------------------------------------
# export_to_pdf output-is-directory
# ---------------------------------------------------------------------------


def test_export_to_pdf_output_is_directory(tmp_path):
    """export_to_pdf() places the PDF inside a directory when output is a dir."""
    from pathlib import Path as _Path
    from unittest.mock import patch

    from markdown_viewer.cli import export_to_pdf

    md_file = tmp_path / "doc.md"
    md_file.write_text("# Doc", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    def fake_export(_html, path):
        _Path(path).write_bytes(b"%PDF-1.4")

    with (
        patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.export", side_effect=fake_export),
        patch("markdown_viewer.exporters.pdf_exporter.PDFExporter.close"),
    ):
        result = export_to_pdf(md_file, output=out_dir)

    assert result.parent == out_dir
    assert result.suffix == ".pdf"


# ---------------------------------------------------------------------------
# --serve flag and _open_flask_dashboard
# ---------------------------------------------------------------------------


def test_main_serve_flag_calls_dashboard():
    """main() with --serve calls _open_flask_dashboard and returns 0."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    with (
        patch("sys.argv", ["mdview", "--serve"]),
        patch("markdown_viewer.cli._open_flask_dashboard") as mock_dash,
    ):
        result = main()

    assert result == 0
    mock_dash.assert_called_once()


def test_main_serve_flag_with_file_warns_and_opens_dashboard(tmp_path, capsys):
    """main() with --serve and a file arg prints a warning, ignores file, opens dashboard."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with (
        patch("sys.argv", ["mdview", str(md_file), "--serve"]),
        patch("markdown_viewer.cli._open_flask_dashboard") as mock_dash,
    ):
        result = main()

    assert result == 0
    mock_dash.assert_called_once()
    captured = capsys.readouterr()
    assert "--serve" in captured.out or "dashboard" in captured.out.lower()


def test_main_no_args_interactive_opens_dashboard():
    """main() with no file in an interactive terminal calls _open_flask_dashboard."""
    from unittest.mock import patch

    from markdown_viewer.cli import main

    with (
        patch("sys.argv", ["mdview"]),
        patch("sys.stdout.isatty", return_value=True),
        patch("markdown_viewer.cli._open_flask_dashboard") as mock_dash,
    ):
        result = main()

    assert result == 0
    mock_dash.assert_called_once()


def test_open_flask_dashboard_opens_url():
    """_open_flask_dashboard opens the dashboard URL in the browser."""
    from unittest.mock import MagicMock, patch

    from markdown_viewer.cli import _open_flask_dashboard

    # Simulate server already up so no subprocess is spawned
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value.status = 200

    # Force the non-Windows code path so webbrowser.open is called deterministically
    with (
        patch("http.client.HTTPConnection", return_value=mock_conn),
        patch("sys.platform", "linux"),
        patch("webbrowser.open") as mock_browser,
    ):
        _open_flask_dashboard(port=5000, browser=None)

    mock_browser.assert_called_once()
    url = mock_browser.call_args[0][0]
    assert "localhost:5000" in url
