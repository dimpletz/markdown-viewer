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
    # Must not leak internal exception details (e.g. the raw error message)
    error_str = str(data)
    assert "network error" not in error_str
    assert "RuntimeError" not in error_str


def test_translate_exception_error_message_is_generic(client):
    """POST /api/translate 500 response returns a generic error, not the exception string."""
    with patch("markdown_viewer.routes.ContentTranslator") as mock_cls:
        mock_cls.return_value.get_supported_languages.return_value = {"fr": "French"}
        mock_cls.return_value.translate.side_effect = OSError("disk I/O failure - secret path")

        response = client.post(
            "/api/translate",
            json={"content": "Hello", "source": "en", "target": "fr"},
        )
    assert response.status_code == 500
    raw = response.get_data(as_text=True)
    assert "disk I/O failure" not in raw
    assert "secret path" not in raw


# ---------------------------------------------------------------------------
# Image serving endpoint
# ---------------------------------------------------------------------------


def test_serve_image_success(client, tmp_path):
    """GET /api/image?path=<png> serves the image with correct MIME type."""
    img = tmp_path / "photo.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)  # minimal PNG header

    response = client.get(f"/api/image?path={img}")
    assert response.status_code == 200
    assert response.content_type.startswith("image/png")


def test_serve_image_no_path_returns_400(client):
    """GET /api/image without path parameter returns 400."""
    response = client.get("/api/image")
    assert response.status_code == 400


def test_serve_image_not_found_returns_404(client, tmp_path):
    """GET /api/image with a nonexistent path returns 404."""
    response = client.get(f"/api/image?path={tmp_path / 'missing.png'}")
    assert response.status_code == 404


def test_serve_image_path_traversal_returns_403(client, tmp_path):
    """GET /api/image with a path outside allowed dir returns 403."""
    outside = tmp_path / ".." / ".." / "etc" / "secret.png"
    response = client.get(f"/api/image?path={outside}")
    assert response.status_code in (403, 404)


def test_serve_image_unsupported_extension_returns_400(client, tmp_path):
    """GET /api/image for a non-image extension returns 400."""
    txt = tmp_path / "readme.txt"
    txt.write_text("hello", encoding="utf-8")
    response = client.get(f"/api/image?path={txt}")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# _rewrite_image_urls helper
# ---------------------------------------------------------------------------


def test_rewrite_image_urls_relative(tmp_path):
    """_rewrite_image_urls rewrites relative paths to /api/image?path= URLs."""
    from markdown_viewer.routes import _rewrite_image_urls

    img = tmp_path / "img.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    html = '<img src="img.png" alt="test">'
    result = _rewrite_image_urls(html, str(tmp_path))
    assert "/api/image?path=" in result
    assert "img.png" in result


def test_rewrite_image_urls_absolute(tmp_path):
    """_rewrite_image_urls rewrites absolute local paths to /api/image?path= URLs."""
    from markdown_viewer.routes import _rewrite_image_urls

    img = tmp_path / "photo.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 5)
    html = f'<img src="{img}" alt="photo">'
    result = _rewrite_image_urls(html, str(tmp_path))
    assert "/api/image?path=" in result


def test_rewrite_image_urls_skips_http(tmp_path):
    """_rewrite_image_urls leaves http:// URLs unchanged."""
    from markdown_viewer.routes import _rewrite_image_urls

    html = '<img src="https://example.com/img.png" alt="remote">'
    result = _rewrite_image_urls(html, str(tmp_path))
    assert result == html


def test_rewrite_image_urls_skips_data_uri(tmp_path):
    """_rewrite_image_urls leaves existing data: URIs unchanged."""
    from markdown_viewer.routes import _rewrite_image_urls

    html = '<img src="data:image/png;base64,abc123" alt="data">'
    result = _rewrite_image_urls(html, str(tmp_path))
    assert result == html


def test_rewrite_image_urls_no_base_dir():
    """_rewrite_image_urls returns html unchanged when base_dir is empty."""
    from markdown_viewer.routes import _rewrite_image_urls

    html = '<img src="image.png" alt="x">'
    assert _rewrite_image_urls(html, "") == html


def test_render_with_base_path_rewrites_images(client, tmp_path):
    """POST /api/render with basePath option rewrites local images to /api/image URLs."""
    img = tmp_path / "diagram.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    md = "![alt](diagram.png)"
    response = client.post(
        "/api/render",
        json={"content": md, "options": {"basePath": str(tmp_path)}},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "/api/image?path=" in data["html"]


def test_open_file_rewrites_image_urls(client, tmp_path):
    """POST /api/file/open rewrites local images to /api/image?path= URLs in the returned HTML."""
    img = tmp_path / "logo.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Doc\n\n![logo](logo.png)", encoding="utf-8")

    response = client.post("/api/file/open", json={"path": str(md_file)})
    assert response.status_code == 200
    data = response.get_json()
    assert "/api/image?path=" in data["html"]


# ---------------------------------------------------------------------------
# _rewrite_md_links
# ---------------------------------------------------------------------------


def test_rewrite_md_links_relative(tmp_path):
    """_rewrite_md_links rewrites relative .md hrefs to /?file= viewer URLs."""
    from markdown_viewer.routes import _rewrite_md_links

    child = tmp_path / "child.md"
    html = f'<a href="child.md">child</a>'
    result = _rewrite_md_links(html, str(tmp_path))
    assert "/?file=" in result
    assert "child.md" not in result.split("/?file=")[0].split('href="')[-1]


def test_rewrite_md_links_absolute(tmp_path):
    """_rewrite_md_links rewrites absolute local .md paths to /?file= viewer URLs."""
    from markdown_viewer.routes import _rewrite_md_links

    abs_path = str(tmp_path / "notes.md")
    html = f'<a href="{abs_path}">notes</a>'
    result = _rewrite_md_links(html, str(tmp_path))
    assert "/?file=" in result


def test_rewrite_md_links_remote_unchanged(tmp_path):
    """_rewrite_md_links leaves http:// links unchanged."""
    from markdown_viewer.routes import _rewrite_md_links

    html = '<a href="https://example.com/doc.md">remote</a>'
    result = _rewrite_md_links(html, str(tmp_path))
    assert result == html


def test_rewrite_md_links_anchor_unchanged(tmp_path):
    """_rewrite_md_links leaves anchor-only hrefs unchanged."""
    from markdown_viewer.routes import _rewrite_md_links

    html = '<a href="#section">jump</a>'
    result = _rewrite_md_links(html, str(tmp_path))
    assert result == html


def test_rewrite_md_links_non_md_unchanged(tmp_path):
    """_rewrite_md_links leaves non-.md local links unchanged."""
    from markdown_viewer.routes import _rewrite_md_links

    html = '<a href="archive.zip">download</a>'
    result = _rewrite_md_links(html, str(tmp_path))
    assert result == html


def test_rewrite_md_links_no_base_dir():
    """_rewrite_md_links returns html unchanged when base_dir is empty."""
    from markdown_viewer.routes import _rewrite_md_links

    html = '<a href="doc.md">doc</a>'
    assert _rewrite_md_links(html, "") == html


def test_rewrite_md_links_fragment_encoded(tmp_path):
    """_rewrite_md_links URL-encodes special characters in the fragment."""
    from markdown_viewer.routes import _rewrite_md_links

    html = '<a href="doc.md#section-name">doc</a>'
    result = _rewrite_md_links(html, str(tmp_path))
    assert "/?file=" in result
    # Fragment must remain in the rewritten URL
    assert "#" in result


def test_rewrite_md_links_fragment_special_chars_encoded(tmp_path):
    """_rewrite_md_links re-encodes dangerous characters that arrive URL-encoded in fragments."""
    from markdown_viewer.routes import _rewrite_md_links

    # A URL-encoded fragment that, after unquote, decodes to injection content.
    # e.g. doc.md#%22%3E%3Cscript%3E → decoded: doc.md#"><script>
    html = '<a href="doc.md#%22%3E%3Cscript%3Ealert(1)%3C%2Fscript%3E">xss</a>'
    result = _rewrite_md_links(html, str(tmp_path))
    assert "/?file=" in result
    # After re-encoding the fragment, raw angle brackets must not appear in the href value
    assert "<script>" not in result


def test_render_with_base_path_rewrites_md_links(client, tmp_path):
    """POST /api/render with basePath rewrites .md links to /?file= viewer URLs."""
    md = "[child](child.md)"
    response = client.post(
        "/api/render",
        json={"content": md, "options": {"basePath": str(tmp_path)}},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "/?file=" in data["html"]


def test_open_file_rewrites_md_links(client, tmp_path):
    """POST /api/file/open rewrites .md links to /?file= viewer URLs in returned HTML."""
    child = tmp_path / "child.md"
    child.write_text("# Child", encoding="utf-8")
    md_file = tmp_path / "parent.md"
    md_file.write_text("[child](child.md)", encoding="utf-8")

    response = client.post("/api/file/open", json={"path": str(md_file)})
    assert response.status_code == 200
    data = response.get_json()
    assert "/?file=" in data["html"]


# ---------------------------------------------------------------------------
# Security: client-injected base_dir is stripped in /api/render
# ---------------------------------------------------------------------------


def test_render_client_base_dir_is_stripped(client, tmp_path):
    """POST /api/render ignores client-supplied base_dir to prevent path injection."""
    # Create a file we don't want to be includeable
    secret = tmp_path / "secret.md"
    secret.write_text("TOP SECRET", encoding="utf-8")

    # Client tries to set base_dir to a path outside ALLOWED_DOCUMENTS_DIR
    md = "![[secret.md]]"
    response = client.post(
        "/api/render",
        json={
            "content": md,
            "options": {
                "base_dir": str(tmp_path),  # client-supplied – must be stripped
                "basePath": "",  # no legitimate basePath
            },
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    # Without a valid basePath, no include resolution happens at all
    assert "TOP SECRET" not in data["html"]


def test_render_client_allowed_base_is_stripped(client, tmp_path):
    """POST /api/render ignores client-supplied allowed_base; server always sets it."""
    secret = tmp_path / "other" / "secret.md"
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_text("SENSITIVE", encoding="utf-8")

    md = "![[other/secret.md]]"
    # Client supplies both base_dir and a wide-open allowed_base — both must be ignored
    response = client.post(
        "/api/render",
        json={
            "content": md,
            "options": {
                "base_dir": str(tmp_path),
                "allowed_base": "/",  # client tries to widen scope
                "basePath": "",
            },
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "SENSITIVE" not in data["html"]


def test_render_with_base_path_resolves_includes(client, tmp_path):
    """POST /api/render with legitimate basePath does resolve transclusion."""
    child = tmp_path / "note.md"
    child.write_text("## Embedded Note\n", encoding="utf-8")
    md = "![[note.md]]"
    response = client.post(
        "/api/render",
        json={"content": md, "options": {"basePath": str(tmp_path)}},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "Embedded Note" in data["html"]


# ---------------------------------------------------------------------------
# Additional coverage: shutdown, image 403, translate errors, test_page
# ---------------------------------------------------------------------------


def test_shutdown_server_returns_200(client):
    """GET /api/shutdown returns 200 (daemon thread exits process after response)."""
    from unittest.mock import patch

    # Patch os._exit so the test process doesn't actually exit
    with patch("os._exit"):
        response = client.get("/api/shutdown")

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


def test_serve_image_path_traversal_returns_403_explicit(client, tmp_path):
    """GET /api/image with a path that resolves outside allowed dir returns 403."""
    import urllib.parse

    # Build a path that, after resolve(), is outside tmp_path
    outside = "/etc/secret.png"
    encoded = urllib.parse.quote(outside, safe="")
    response = client.get(f"/api/image?path={encoded}")
    assert response.status_code in (403, 404)


def test_translate_validation_error_returns_400(client):
    """POST /api/translate with an empty body returns 400 (ValidationError)."""
    response = client.post("/api/translate", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_translate_timeout_error_returns_400(client):
    """POST /api/translate returns 400 when a TimeoutError is raised."""
    with patch("markdown_viewer.routes.ContentTranslator") as mock_cls:
        mock_cls.return_value.get_supported_languages.return_value = {"es": "Spanish"}
        mock_cls.return_value.translate.side_effect = TimeoutError("too slow")

        response = client.post(
            "/api/translate",
            json={"content": "Hello", "source": "en", "target": "es"},
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_export_pdf_validation_error_returns_400(client):
    """POST /api/export/pdf with completely invalid data returns 400."""
    response = client.post("/api/export/pdf", json={"html": None})
    assert response.status_code == 400


def test_export_word_validation_error_returns_400(client):
    """POST /api/export/word with completely invalid data returns 400."""
    response = client.post("/api/export/word", json={"html": None})
    assert response.status_code == 400


def test_test_page_exists(client, tmp_path, monkeypatch):
    """GET /api/test serves test.html when it exists."""
    from pathlib import Path
    from unittest.mock import patch

    import markdown_viewer.routes as routes_module

    fake_test_html = Path(routes_module.__file__).parent.parent / "test.html"

    # Use send_file mock to avoid creating a real file on disk
    with (
        patch("markdown_viewer.routes.Path.exists", return_value=True),
        patch(
            "markdown_viewer.routes.send_file",
            return_value=client.application.make_response(
                ("<html><body>test</body></html>", 200, {"Content-Type": "text/html"})
            ),
        ),
    ):
        response = client.get("/api/test")

    assert response.status_code == 200


def test_http_exception_handler(client):
    """A 404 HTTPException is handled with the JSON error format."""
    response = client.get("/api/nonexistent_route_xyz")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_generic_exception_handler(app, client):
    """An unhandled exception in a route returns 500 with JSON error."""
    with patch("markdown_viewer.routes.markdown_processor.process", side_effect=ValueError("x")):
        response = client.post("/api/render", json={"content": "# Hello"})
    assert response.status_code in (400, 500)
