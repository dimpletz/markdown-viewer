"""Tests for Flask API routes."""

# pylint: disable=import-outside-toplevel,redefined-outer-name
from unittest.mock import patch, MagicMock

import pytest

from markdown_viewer.app import create_app


@pytest.fixture
def app(tmp_path):
    """Create a test Flask app with CSRF disabled."""
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def test_health_check(client):
    """GET /api/health returns 200 with status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["checks"]["api"] is True


def test_render_markdown(client):
    """POST /api/render with valid content returns rendered HTML."""
    response = client.post(
        "/api/render",
        json={"content": "# Hello\n\nWorld"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "Hello" in data["html"]
    assert "<h1" in data["html"]


def test_render_missing_content_returns_400(client):
    """POST /api/render without 'content' field returns 400."""
    response = client.post("/api/render", json={"options": {}})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "content" in str(data["error"])


def test_render_empty_body_returns_400(client):
    """POST /api/render with no JSON body returns 400."""
    response = client.post("/api/render", content_type="application/json", data="")
    assert response.status_code == 400


def test_open_file_success(client, tmp_path):
    """POST /api/file/open with a valid markdown file returns content and html."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n\nContent.", encoding="utf-8")

    response = client.post("/api/file/open", json={"path": str(md_file)})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "# Test" in data["content"]
    assert "<h1" in data["html"]


def test_open_file_not_found_returns_404(client, tmp_path):
    """POST /api/file/open with a nonexistent path returns 404."""
    response = client.post(
        "/api/file/open",
        json={"path": str(tmp_path / "nonexistent.md")},
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_open_file_path_traversal_returns_403(client, tmp_path):
    """POST /api/file/open with a path outside allowed dir returns 403."""
    # Attempt to traverse outside the allowed directory
    response = client.post(
        "/api/file/open",
        json={"path": str(tmp_path / ".." / ".." / "etc" / "passwd")},
    )
    # Could be 403 (denied) or 404 (not found after resolve) — never 200
    assert response.status_code in (403, 404)
    data = response.get_json()
    assert data["success"] is False


def test_open_file_missing_path_returns_400(client):
    """POST /api/file/open without 'path' field returns 400."""
    response = client.post("/api/file/open", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_get_csrf_token(client):
    """GET /api/csrf returns a csrf_token."""
    response = client.get("/api/csrf")
    assert response.status_code == 200
    data = response.get_json()
    assert "csrf_token" in data
    assert data["csrf_token"]


def test_open_file_is_directory_returns_400(client, tmp_path):
    """POST /api/file/open with a directory path returns 400."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    response = client.post("/api/file/open", json={"path": str(subdir)})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_render_markdown_value_error_returns_400(client):
    """POST /api/render returns 400 when processor raises ValueError."""
    with patch("markdown_viewer.routes.markdown_processor.process", side_effect=ValueError("bad")):
        response = client.post("/api/render", json={"content": "# Hello"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_render_markdown_unexpected_error_returns_500(client):
    """POST /api/render returns 500 on unexpected exception."""
    with patch(
        "markdown_viewer.routes.markdown_processor.process", side_effect=RuntimeError("boom")
    ):
        response = client.post("/api/render", json={"content": "# Hello"})
    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False


def test_open_file_unexpected_error_returns_500(client, tmp_path):
    """POST /api/file/open returns 500 on unexpected read error."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with patch(
        "markdown_viewer.routes.file_handler.read_file", side_effect=RuntimeError("disk error")
    ):
        response = client.post("/api/file/open", json={"path": str(md_file)})
    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False


def test_export_pdf_success(client):
    """POST /api/export/pdf returns PDF bytes with mocked exporter."""
    from pathlib import Path as _Path

    def fake_export(_html, path, _options=None):
        _Path(path).write_bytes(b"%PDF-1.4 dummy")

    with patch("markdown_viewer.routes.PDFExporter") as mock_cls:
        mock_cls.return_value.export.side_effect = fake_export
        mock_cls.return_value.close = MagicMock()

        response = client.post(
            "/api/export/pdf",
            json={"html": "<p>Hello world</p>", "filename": "test.pdf"},
        )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"


def test_export_pdf_missing_html_returns_400(client):
    """POST /api/export/pdf without 'html' field returns 400."""
    response = client.post("/api/export/pdf", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_export_pdf_exporter_error_returns_500(client):
    """POST /api/export/pdf returns 500 when exporter raises."""
    with patch("markdown_viewer.routes.PDFExporter") as mock_cls:
        mock_cls.return_value.export.side_effect = RuntimeError("playwright error")
        mock_cls.return_value.close = MagicMock()

        response = client.post("/api/export/pdf", json={"html": "<p>Hello</p>"})

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False


def test_export_word_success(client):
    """POST /api/export/word returns docx bytes with mocked exporter."""
    from pathlib import Path as _Path

    def fake_export(_html, _markdown, path):
        _Path(path).write_bytes(b"PK dummy docx")

    with patch("markdown_viewer.routes.WordExporter") as mock_cls:
        mock_cls.return_value.export.side_effect = fake_export

        response = client.post(
            "/api/export/word",
            json={"html": "<p>Hello world</p>", "filename": "test.docx"},
        )

    assert response.status_code == 200


def test_export_word_missing_html_returns_400(client):
    """POST /api/export/word without 'html' field returns 400."""
    response = client.post("/api/export/word", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_export_word_exporter_error_returns_500(client):
    """POST /api/export/word returns 500 when exporter raises."""
    with patch("markdown_viewer.routes.WordExporter") as mock_cls:
        mock_cls.return_value.export.side_effect = RuntimeError("docx error")

        response = client.post("/api/export/word", json={"html": "<p>Hello</p>"})

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False


def test_translate_success(client):
    """POST /api/translate with mocked translator returns translated text."""
    with patch("markdown_viewer.routes.ContentTranslator") as mock_cls:
        mock_cls.return_value.get_supported_languages.return_value = {
            "es": "Spanish",
            "en": "English",
        }
        mock_cls.return_value.translate.return_value = "Hola mundo"

        response = client.post(
            "/api/translate",
            json={"content": "Hello world", "source": "en", "target": "es"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["translated"] == "Hola mundo"


def test_translate_unsupported_language_returns_400(client):
    """POST /api/translate with an unsupported target language returns 400."""
    with patch("markdown_viewer.routes.ContentTranslator") as mock_cls:
        mock_cls.return_value.get_supported_languages.return_value = {"es": "Spanish"}

        response = client.post(
            "/api/translate",
            json={"content": "Hello", "target": "xx-invalid"},
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_translate_missing_target_returns_400(client):
    """POST /api/translate without 'target' field returns 400."""
    response = client.post("/api/translate", json={"content": "Hello"})
    assert response.status_code == 400


def test_translate_value_error_returns_400(client):
    """POST /api/translate returns 400 when translator raises ValueError."""
    with patch("markdown_viewer.routes.ContentTranslator") as mock_cls:
        mock_cls.return_value.get_supported_languages.return_value = {"es": "Spanish"}
        mock_cls.return_value.translate.side_effect = ValueError("bad lang")

        response = client.post(
            "/api/translate",
            json={"content": "Hello", "source": "en", "target": "es"},
        )

    assert response.status_code == 400


def test_transform_diagram(client):
    """POST /api/transform/diagram returns success."""
    response = client.post(
        "/api/transform/diagram",
        json={"code": "graph TD\nA-->B", "type": "mermaid"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


def test_share_via_email(client):
    """POST /api/email/share returns a mailto link."""
    response = client.post(
        "/api/email/share",
        json={"html": "<p>Hello</p>", "subject": "Test Subject"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["mailto"].startswith("mailto:")


def test_test_page_not_found(client):
    """GET /api/test returns 404 when test.html does not exist."""
    response = client.get("/api/test")
    # test.html won't exist in the test environment
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Test page not found"


def test_check_disk_space_oserror(app):
    """check_disk_space() returns True when shutil.disk_usage raises OSError."""
    with app.app_context():
        with patch("shutil.disk_usage", side_effect=OSError("no space info")):
            from markdown_viewer.routes import check_disk_space

            result = check_disk_space()
    assert result is True


def test_cleanup_pdf_exporter_close_raises(app):
    """cleanup_resources() logs warning when pdf_exporter.close() raises."""
    mock_exporter = MagicMock()
    mock_exporter.close.side_effect = RuntimeError("cleanup error")

    with app.test_request_context("/"):
        from flask import g

        g.pdf_exporter = mock_exporter
        from markdown_viewer.routes import cleanup_resources

        cleanup_resources()  # should not raise


def test_cleanup_word_exporter_close_raises(app):
    """cleanup_resources() logs warning when word_exporter.close() raises."""
    mock_exporter = MagicMock()
    mock_exporter.close.side_effect = RuntimeError("cleanup error")

    with app.test_request_context("/"):
        from flask import g

        g.word_exporter = mock_exporter
        from markdown_viewer.routes import cleanup_resources

        cleanup_resources()  # should not raise


def test_cleanup_translator_close_raises(app):
    """cleanup_resources() logs warning when translator.close() raises."""
    mock_translator = MagicMock()
    mock_translator.close.side_effect = RuntimeError("cleanup error")

    with app.test_request_context("/"):
        from flask import g

        g.translator = mock_translator
        from markdown_viewer.routes import cleanup_resources

        cleanup_resources()  # should not raise


def test_open_file_read_raises_file_not_found(client, tmp_path):
    """POST /api/file/open returns 404 when read_file raises FileNotFoundError."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with patch(
        "markdown_viewer.routes.file_handler.read_file", side_effect=FileNotFoundError("gone")
    ):
        response = client.post("/api/file/open", json={"path": str(md_file)})
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_open_file_read_raises_value_error(client, tmp_path):
    """POST /api/file/open returns 400 when read_file raises ValueError."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with patch("markdown_viewer.routes.file_handler.read_file", side_effect=ValueError("bad file")):
        response = client.post("/api/file/open", json={"path": str(md_file)})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_translate_exception_returns_500(client):
    """POST /api/translate returns 500 on unexpected exception from translator."""
    with patch("markdown_viewer.routes.ContentTranslator") as mock_cls:
        mock_cls.return_value.get_supported_languages.return_value = {"es": "Spanish"}
        mock_cls.return_value.translate.side_effect = RuntimeError("network error")

        response = client.post(
            "/api/translate",
            json={"content": "Hello", "source": "en", "target": "es"},
        )
    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
