"""Integration: security — path traversal, CSRF enforcement, oversized payloads.

These tests verify that the security controls are wired end-to-end,
not just unit-tested in isolation.
"""

# pylint: disable=redefined-outer-name

import os

import pytest

from markdown_viewer.app import create_app

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path):
    """Flask test client restricted to tmp_path as its allowed document root."""
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )
    return app.test_client()


@pytest.fixture()
def md_file(tmp_path):
    """A real markdown file inside the allowed documents directory."""
    p = tmp_path / "sample.md"
    p.write_text("# Hello\n\nWorld", encoding="utf-8")
    return p


@pytest.fixture()
def image_file(tmp_path):
    """A minimal PNG inside the allowed documents directory."""
    p = tmp_path / "pic.png"
    # 1×1 white PNG, binary-safe
    p.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x18\xddN"
        b"\x1f\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return p


# ---------------------------------------------------------------------------
# Path traversal — /api/open
# ---------------------------------------------------------------------------


class TestPathTraversalOpenFile:
    """Requests to escape the allowed documents directory must be blocked."""

    def test_open_file_inside_allowed_dir_succeeds(self, client, md_file):
        resp = client.post("/api/file/open", json={"path": str(md_file)})
        assert resp.status_code == 200

    def test_open_file_with_dotdot_returns_403(self, client, tmp_path):
        outside = tmp_path.parent / "secret.md"
        resp = client.post("/api/file/open", json={"path": str(outside)})
        assert resp.status_code in (403, 404)

    def test_open_file_absolute_path_outside_root_returns_403(self, client):
        if os.name == "nt":
            evil = "C:\\Windows\\system32\\drivers\\etc\\hosts"
        else:
            evil = "/etc/passwd"
        resp = client.post("/api/file/open", json={"path": evil})
        assert resp.status_code in (403, 404)

    def test_open_file_missing_path_returns_400(self, client):
        resp = client.post("/api/file/open", json={})
        assert resp.status_code == 400

    def test_open_directory_returns_400(self, client, tmp_path):
        resp = client.post("/api/file/open", json={"path": str(tmp_path)})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Path traversal — /api/image
# ---------------------------------------------------------------------------


class TestPathTraversalImageEndpoint:
    def test_image_inside_allowed_dir_returns_200(self, client, image_file):
        import urllib.parse  # pylint: disable=import-outside-toplevel

        encoded = urllib.parse.quote(str(image_file), safe="")
        resp = client.get(f"/api/image?path={encoded}")
        assert resp.status_code == 200

    def test_image_outside_allowed_dir_returns_403(self, client, tmp_path):
        import urllib.parse  # pylint: disable=import-outside-toplevel

        if os.name == "nt":
            evil = "C:\\Windows\\system32\\cmd.exe"
        else:
            evil = "/etc/passwd"
        encoded = urllib.parse.quote(evil, safe="")
        resp = client.get(f"/api/image?path={encoded}")
        assert resp.status_code in (403, 404)

    def test_image_no_path_returns_400(self, client):
        resp = client.get("/api/image")
        assert resp.status_code == 400

    def test_image_unsupported_extension_returns_400(self, client, tmp_path):
        import urllib.parse  # pylint: disable=import-outside-toplevel

        txt = tmp_path / "data.txt"
        txt.write_text("sensitive", encoding="utf-8")
        encoded = urllib.parse.quote(str(txt), safe="")
        resp = client.get(f"/api/image?path={encoded}")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Oversized payload rejection
# ---------------------------------------------------------------------------


class TestOversizedPayloads:
    def test_render_over_10mb_rejected(self, client):
        big = "x" * (10 * 1024 * 1024 + 1)
        resp = client.post("/api/render", json={"content": big})
        assert resp.status_code == 400

    def test_export_word_over_50mb_rejected(self, client):
        big = "x" * (50 * 1024 * 1024 + 1)
        resp = client.post("/api/export/word", json={"html": big})
        assert resp.status_code in (400, 413)

    def test_export_pdf_over_50mb_rejected(self, client):
        big = "x" * (50 * 1024 * 1024 + 1)
        resp = client.post("/api/export/pdf", json={"html": big})
        assert resp.status_code in (400, 413)


# ---------------------------------------------------------------------------
# CSRF enforcement (separate app with CSRF enabled)
# ---------------------------------------------------------------------------


@pytest.fixture()
def csrf_client(tmp_path):
    """Flask test client with CSRF protection *enabled*."""
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "csrf-test-key",
            "WTF_CSRF_ENABLED": True,
            "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )
    return app.test_client()


class TestCsrfEnforcement:
    def test_render_without_csrf_token_returns_400(self, csrf_client):
        """State-changing POST without CSRF token must be blocked."""
        resp = csrf_client.post(
            "/api/render",
            json={"content": "# Hi"},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_csrf_token_endpoint_accessible_without_token(self, csrf_client):
        """/api/csrf is a GET and must return a token with no prior auth."""
        resp = csrf_client.get("/api/csrf")
        assert resp.status_code == 200
        assert "csrf_token" in resp.get_json()

    def test_render_with_valid_csrf_token_succeeds(self, csrf_client):
        """Workflow: fetch CSRF token then use it in the POST."""
        token = csrf_client.get("/api/csrf").get_json()["csrf_token"]
        resp = csrf_client.post(
            "/api/render",
            json={"content": "# Hi"},
            headers={
                "Content-Type": "application/json",
                "X-CSRFToken": token,
            },
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Security response headers
# ---------------------------------------------------------------------------


class TestSecurityHeaders:
    def test_api_response_has_x_content_type_options(self, client):
        resp = client.get("/api/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_api_response_has_x_frame_options(self, client):
        resp = client.get("/api/health")
        assert "X-Frame-Options" in resp.headers

    def test_api_response_has_content_security_policy(self, client):
        resp = client.get("/api/health")
        assert "Content-Security-Policy" in resp.headers
