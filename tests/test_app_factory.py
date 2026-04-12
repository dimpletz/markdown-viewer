"""Tests for the app factory (create_app) and CLI render function."""

# pylint: disable=import-outside-toplevel
import os

import pytest

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def test_create_app_without_secret_key_auto_generates():
    """create_app() auto-generates an ephemeral SECRET_KEY when absent."""
    # Ensure env var is not set
    os.environ.pop("SECRET_KEY", None)

    from markdown_viewer.app import create_app

    # Should succeed — auto-generates an ephemeral key for local use
    app = create_app()
    assert app.config.get("SECRET_KEY"), "A SECRET_KEY should be auto-generated"


def test_create_app_with_config_succeeds(tmp_path):
    """create_app() with config dict containing SECRET_KEY succeeds."""
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()

    from markdown_viewer.app import create_app

    app = create_app(
        {
            "SECRET_KEY": "test-secret",
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )

    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["SECRET_KEY"] == "test-secret"


def test_create_app_via_env_secret_key(tmp_path, monkeypatch):
    """create_app() succeeds when SECRET_KEY is set in environment."""
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()
    monkeypatch.setenv("SECRET_KEY", "env-secret-key")

    from markdown_viewer.app import create_app

    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )

    assert app is not None


def test_api_blueprint_registered(tmp_path):
    """The /api blueprint is registered and health endpoint responds."""
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()

    from markdown_viewer.app import create_app

    app = create_app(
        {
            "SECRET_KEY": "test-secret",
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )

    with app.test_client() as client:
        response = client.get("/api/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# CLI – render_markdown_file
# ---------------------------------------------------------------------------


def test_render_markdown_file_generates_html(tmp_path):
    """render_markdown_file() creates an HTML file with rendered content."""
    md_file = tmp_path / "sample.md"
    md_file.write_text("# Title\n\nParagraph.", encoding="utf-8")

    from markdown_viewer.cli import render_markdown_file

    html_path = render_markdown_file(md_file, open_browser=False)

    try:
        assert html_path.exists()
        html = html_path.read_text(encoding="utf-8")
        assert "Title" in html
        assert "<h1" in html
    finally:
        html_path.unlink(missing_ok=True)


def test_render_markdown_file_to_specified_output(tmp_path):
    """render_markdown_file() writes output to the provided path."""
    md_file = tmp_path / "input.md"
    md_file.write_text("Hello **world**", encoding="utf-8")
    out_file = tmp_path / "output.html"

    from markdown_viewer.cli import render_markdown_file

    result = render_markdown_file(md_file, output=out_file, open_browser=False)

    assert result == out_file.resolve()
    assert out_file.exists()
    assert "world" in out_file.read_text(encoding="utf-8")


def test_render_markdown_file_not_found_raises(tmp_path):
    """render_markdown_file() raises FileNotFoundError for missing files."""
    from markdown_viewer.cli import render_markdown_file

    with pytest.raises(FileNotFoundError):
        render_markdown_file(tmp_path / "ghost.md", open_browser=False)


def test_export_to_word_generates_docx(tmp_path):
    """export_to_word() produces a .docx file."""
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Word Export\n\nSome content.", encoding="utf-8")
    out_file = tmp_path / "doc.docx"

    from markdown_viewer.cli import export_to_word

    result = export_to_word(md_file, output=out_file)

    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# markdown_viewer.__init__ lazy imports
# ---------------------------------------------------------------------------


def test_init_lazy_create_app():
    """markdown_viewer.create_app is lazily importable."""
    import markdown_viewer

    assert callable(markdown_viewer.create_app)


def test_init_lazy_start_server():
    """markdown_viewer.start_server is lazily importable."""
    import markdown_viewer

    assert callable(markdown_viewer.start_server)


def test_init_lazy_attribute_error():
    """Accessing an unknown attribute raises AttributeError."""
    import markdown_viewer

    with pytest.raises(AttributeError):
        _ = markdown_viewer.nonexistent_attribute_xyz


# ---------------------------------------------------------------------------
# UI routes (index, styles, scripts)
# ---------------------------------------------------------------------------


def _make_test_client(tmp_path):
    """Helper to create a test client with a clean config."""
    from markdown_viewer.app import create_app

    (tmp_path / "temp").mkdir(exist_ok=True)
    (tmp_path / "uploads").mkdir(exist_ok=True)
    app = create_app(
        {
            "SECRET_KEY": "test-secret",
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )
    return app.test_client()


def test_ui_index_route(tmp_path):
    """GET / serves the Electron renderer index.html."""
    client = _make_test_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert b"html" in response.data.lower()


def test_ui_styles_route(tmp_path):
    """GET /styles/main.css serves the renderer CSS with no-store cache header."""
    client = _make_test_client(tmp_path)
    response = client.get("/styles/main.css")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store"


def test_ui_scripts_route(tmp_path):
    """GET /scripts/app.js serves the renderer JS with no-store cache header."""
    client = _make_test_client(tmp_path)
    response = client.get("/scripts/app.js")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store"


def test_http_exception_handler_format(tmp_path):
    """An HTTP 404 from a missing route returns JSON with success=False."""
    client = _make_test_client(tmp_path)
    response = client.get("/api/does_not_exist_xyz")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == 404


def test_generic_exception_handler_format(tmp_path):
    """A route that raises an unhandled exception returns 500 JSON."""
    from unittest.mock import patch

    client = _make_test_client(tmp_path)
    with patch(
        "markdown_viewer.routes.markdown_processor.process",
        side_effect=RuntimeError("unexpected"),
    ):
        response = client.post("/api/render", json={"content": "# Hello"})
    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False


def test_configure_logging_creates_log_dir(tmp_path, monkeypatch):
    """configure_logging() creates the logs/ dir and attaches a file handler when not in debug."""
    import os
    from unittest.mock import patch

    from markdown_viewer.app import create_app

    log_dir = tmp_path / "logs"

    # Patch os.path.exists to return False (logs dir doesn't exist) and os.mkdir to track the call
    real_exists = os.path.exists
    mkdir_calls = []

    def fake_exists(path):
        if str(path).endswith("logs"):
            return False
        return real_exists(path)

    def fake_mkdir(path, mode=0o777):
        mkdir_calls.append(path)
        # don't actually create; RotatingFileHandler will fail without the dir so also patch it
        pass

    (tmp_path / "temp").mkdir(exist_ok=True)
    (tmp_path / "uploads").mkdir(exist_ok=True)

    with (
        patch("os.path.exists", side_effect=fake_exists),
        patch("os.mkdir", side_effect=fake_mkdir),
        patch("logging.handlers.RotatingFileHandler", autospec=True),
    ):
        app = create_app(
            {
                "SECRET_KEY": "test-secret",
                "TESTING": False,  # triggers configure_logging non-debug path
                "DEBUG": False,
                "WTF_CSRF_ENABLED": False,
                "TEMP_FOLDER": str(tmp_path / "temp"),
                "UPLOAD_FOLDER": str(tmp_path / "uploads"),
            }
        )

    # os.mkdir was called for "logs"
    assert any("logs" in str(p) for p in mkdir_calls)
