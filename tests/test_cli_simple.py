"""
Focused cli.py tests to boost coverage to 90%+.
Simple, effective tests without complex mocking.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from markdown_viewer.cli import _embed_local_images, _stop_server, _resolve_file


class TestEmbedLocalImages:
    """Test image embedding for file:// URLs."""

    def test_embed_absolute_path(self, tmp_path):
        """Test embedding image with absolute Windows path."""
        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")  # PNG header

        html = f'<img src="{img_file}">'
        result = _embed_local_images(html, tmp_path)

        assert "data:image/png;base64," in result
        assert str(img_file) not in result

    def test_embed_svg_mime_type(self, tmp_path):
        """Test SVG gets correct mime type."""
        svg_file = tmp_path / "icon.svg"
        svg_file.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")

        html = f'<img src="{svg_file.name}">'
        result = _embed_local_images(html, tmp_path)

        assert "data:image/svg+xml;base64," in result

    def test_embed_url_decoded_spaces(self, tmp_path):
        """Test URL-encoded spaces in image paths."""
        img_file = tmp_path / "my image.jpg"
        img_file.write_bytes(b"\xff\xd8\xff\xe0")  # JPEG header

        html = '<img src="my%20image.jpg">'
        result = _embed_local_images(html, tmp_path)

        assert "data:image/jpeg;base64," in result

    def test_embed_backslash_paths(self, tmp_path):
        """Test Windows backslash paths are handled."""
        subdir = tmp_path / "imgs"
        subdir.mkdir()
        img_file = subdir / "photo.gif"
        img_file.write_bytes(b"GIF89a")  # GIF header

        html = r'<img src="imgs\photo.gif">'
        result = _embed_local_images(html, tmp_path)

        assert "data:image/gif;base64," in result

    def test_leave_http_urls_unchanged(self, tmp_path):
        """Test remote HTTP URLs are not modified."""
        html = '<img src="https://example.com/image.png">'
        result = _embed_local_images(html, tmp_path)

        assert result == html  # Unchanged

    def test_leave_data_uris_unchanged(self, tmp_path):
        """Test existing data URIs are not modified."""
        html = '<img src="data:image/png;base64,iVBORw0KGgo=">'
        result = _embed_local_images(html, tmp_path)

        assert result == html  # Unchanged

    def test_ignore_nonexistent_files(self, tmp_path):
        """Test missing files are left unchanged."""
        html = '<img src="nonexistent.png">'
        result = _embed_local_images(html, tmp_path)

        assert result == html  # Unchanged

    def test_ignore_unsupported_extensions(self, tmp_path):
        """Test non-image files are ignored."""
        txt_file = tmp_path / "doc.txt"
        txt_file.write_text("Not an image", encoding="utf-8")

        html = f'<img src="{txt_file.name}">'
        result = _embed_local_images(html, tmp_path)

        assert result == html  # Unchanged


class TestStopServer:
    """Test server shutdown functionality."""

    @patch("http.client.HTTPConnection")
    def test_stop_via_http_success(self, mock_http):
        """Test successful shutdown via HTTP endpoint."""
        mock_conn = MagicMock()
        mock_http.return_value = mock_conn

        result = _stop_server(port=5000)

        assert result == 0
        mock_conn.request.assert_called_with("GET", "/api/shutdown")
        mock_conn.close.assert_called_once()

    @patch("http.client.HTTPConnection")
    @patch("markdown_viewer.server.pid_file_path")
    @patch("os.kill")
    def test_stop_via_pid_file(self, mock_kill, mock_pid_path, mock_http):
        """Test shutdown via PID file when HTTP fails."""
        mock_http.side_effect = Exception("Connection refused")

        mock_pid_file = MagicMock()
        mock_pid_file.exists.return_value = True
        mock_pid_file.read_text.return_value = "12345"
        mock_pid_path.return_value = mock_pid_file

        result = _stop_server(port=5001)

        assert result == 0
        mock_kill.assert_called_with(12345, 15)
        mock_pid_file.unlink.assert_called_once()

    @patch("http.client.HTTPConnection")
    @patch("markdown_viewer.server.pid_file_path")
    @patch("os.kill")
    def test_stop_stale_pid(self, mock_kill, mock_pid_path, mock_http):
        """Test handling of stale PID file."""
        mock_http.side_effect = Exception("Connection refused")
        mock_kill.side_effect = ProcessLookupError

        mock_pid_file = MagicMock()
        mock_pid_file.exists.return_value = True
        mock_pid_file.read_text.return_value = "99999"
        mock_pid_path.return_value = mock_pid_file

        result = _stop_server(port=5002)

        assert result == 0
        mock_pid_file.unlink.assert_called_once()

    @patch("http.client.HTTPConnection")
    @patch("markdown_viewer.server.pid_file_path")
    def test_stop_no_server(self, mock_pid_path, mock_http):
        """Test when no server is running."""
        mock_http.side_effect = Exception("Connection refused")

        mock_pid_file = MagicMock()
        mock_pid_file.exists.return_value = False
        mock_pid_path.return_value = mock_pid_file

        result = _stop_server(port=5003)

        assert result == 0


class TestResolveFile:
    """Test file validation logic."""

    def test_resolve_valid_markdown_file(self, tmp_path):
        """Test resolving a valid .md file."""
        md_file = tmp_path / "document.md"
        md_file.write_text("# Test", encoding="utf-8")

        args = MagicMock()
        args.file = str(md_file)

        result = _resolve_file(args)

        assert result is None  # Success
        assert args.file == Path(md_file)

    def test_resolve_valid_markdown_extension(self, tmp_path):
        """Test .markdown extension is accepted."""
        md_file = tmp_path / "README.markdown"
        md_file.write_text("# README", encoding="utf-8")

        args = MagicMock()
        args.file = str(md_file)

        result = _resolve_file(args)

        assert result is None

    def test_reject_http_url(self):
        """Test HTTP URLs are rejected."""
        args = MagicMock()
        args.file = "http://example.com/README.md"

        with patch("sys.stdin.isatty", return_value=False):
            result = _resolve_file(args)

        assert result == 1  # Error

    def test_reject_https_url(self):
        """Test HTTPS URLs are rejected."""
        args = MagicMock()
        args.file = "https://github.com/user/repo/README.md"

        with patch("sys.stdin.isatty", return_value=False):
            result = _resolve_file(args)

        assert result == 1

    def test_reject_directory(self, tmp_path):
        """Test directories are rejected."""
        args = MagicMock()
        args.file = str(tmp_path)

        with patch("sys.stdin.isatty", return_value=False):
            result = _resolve_file(args)

        assert result == 1

    def test_reject_no_extension(self, tmp_path):
        """Test files without extension are rejected."""
        no_ext = tmp_path / "README"
        args = MagicMock()
        args.file = str(no_ext)

        with patch("sys.stdin.isatty", return_value=False):
            result = _resolve_file(args)

        assert result == 1

    def test_reject_wrong_extension(self, tmp_path):
        """Test non-markdown extensions are rejected."""
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("Not markdown", encoding="utf-8")

        args = MagicMock()
        args.file = str(txt_file)

        with patch("sys.stdin.isatty", return_value=False):
            result = _resolve_file(args)

        assert result == 1

    def test_reject_nonexistent_file(self):
        """Test nonexistent files are rejected."""
        args = MagicMock()
        args.file = "/path/to/nonexistent.md"

        with patch("sys.stdin.isatty", return_value=False):
            result = _resolve_file(args)

        assert result == 1

    def test_user_cancels_with_ctrl_c(self):
        """Test user can cancel with Ctrl+C."""
        args = MagicMock()
        args.file = None

        with patch("sys.stdin.isatty", return_value=True):
            with patch("builtins.input", side_effect=KeyboardInterrupt):
                result = _resolve_file(args)

        assert result == 0  # Clean exit

    def test_user_cancels_with_eof(self):
        """Test user can cancel with EOF (Ctrl+D/Ctrl+Z)."""
        args = MagicMock()
        args.file = None

        with patch("sys.stdin.isatty", return_value=True):
            with patch("builtins.input", side_effect=EOFError):
                result = _resolve_file(args)

        assert result == 0
