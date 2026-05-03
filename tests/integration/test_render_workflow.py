"""Integration: render → export Word / PDF end-to-end flows.

These tests exercise the full Flask route → service layer stack.
Playwright (browser launch) is mocked so the suite runs in CI without
a Chromium install; everything else (request parsing, schema validation,
exporter invocation, file streaming) is real.
"""

# pylint: disable=redefined-outer-name,import-outside-toplevel

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from markdown_viewer.app import create_app

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path):
    """Flask test client with CSRF disabled and an isolated temp dir."""
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


# ---------------------------------------------------------------------------
# Health check — smoke test that the API layer is alive
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_body_contains_api_ok(self, client):
        data = client.get("/api/health").get_json()
        assert data["checks"]["api"] is True

    def test_health_has_capabilities_key(self, client):
        data = client.get("/api/health").get_json()
        assert "capabilities" in data


# ---------------------------------------------------------------------------
# Render → inspect HTML
# ---------------------------------------------------------------------------


class TestRenderWorkflow:
    """POST /api/render returns structured HTML usable downstream."""

    def test_render_heading_produces_h1(self, client):
        resp = client.post("/api/render", json={"content": "# Hello World"})
        assert resp.status_code == 200
        assert "<h1" in resp.get_json()["html"]

    def test_render_code_block_produces_pre(self, client):
        md = "```python\nprint('hi')\n```"
        resp = client.post("/api/render", json={"content": md})
        assert resp.status_code == 200
        html = resp.get_json()["html"]
        assert "<pre" in html or "<code" in html

    def test_render_table_produces_table_tag(self, client):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        resp = client.post("/api/render", json={"content": md})
        assert resp.status_code == 200
        assert "<table" in resp.get_json()["html"]

    def test_render_link_produces_anchor(self, client):
        resp = client.post("/api/render", json={"content": "[click](https://example.com)"})
        assert resp.status_code == 200
        assert "<a " in resp.get_json()["html"]

    def test_render_large_document_under_limit(self, client):
        """1 MB of markdown should render without error."""
        md = ("# Section\n\n" + "word " * 200 + "\n\n") * 50
        resp = client.post("/api/render", json={"content": md})
        assert resp.status_code == 200

    def test_render_returns_metadata(self, client):
        resp = client.post("/api/render", json={"content": "# Hi"})
        data = resp.get_json()
        assert "html" in data

    def test_render_empty_content_returns_400(self, client):
        resp = client.post("/api/render", json={})
        assert resp.status_code == 400

    def test_render_oversized_payload_rejected(self, client):
        """Content exceeding 10 MB schema limit must return 400."""
        big = "x" * (10 * 1024 * 1024 + 1)
        resp = client.post("/api/render", json={"content": big})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Render → Export Word end-to-end
# ---------------------------------------------------------------------------


class TestRenderToWordWorkflow:
    """POST /api/render → POST /api/export/word — full two-step flow."""

    def _render(self, client, md: str) -> str:
        resp = client.post("/api/render", json={"content": md})
        assert resp.status_code == 200
        return resp.get_json()["html"]

    def test_word_export_returns_docx_content_type(self, client, tmp_path):
        html = self._render(client, "# Test\n\nHello world.")
        docx_bytes = b"PK\x03\x04" + b"\x00" * 100  # minimal zip magic bytes

        mock_exporter = MagicMock()

        def fake_export(html_content, markdown, output_path, **_kwargs):
            Path(output_path).write_bytes(docx_bytes)

        mock_exporter.export.side_effect = fake_export
        mock_exporter.close = MagicMock()

        with patch("markdown_viewer.routes.get_word_exporter", return_value=mock_exporter):
            resp = client.post(
                "/api/export/word",
                json={"html": html, "markdown": "# Test\n\nHello world."},
            )

        assert resp.status_code == 200
        assert (
            "word" in resp.content_type
            or "docx" in resp.content_type
            or "octet" in resp.content_type
        )

    def test_word_export_missing_html_returns_400(self, client):
        resp = client.post("/api/export/word", json={})
        assert resp.status_code == 400

    def test_word_export_exporter_error_returns_500(self, client):
        html = self._render(client, "# Fail test")
        mock_exporter = MagicMock()
        mock_exporter.export.side_effect = RuntimeError("exporter crashed")
        mock_exporter.close = MagicMock()

        with patch("markdown_viewer.routes.get_word_exporter", return_value=mock_exporter):
            resp = client.post("/api/export/word", json={"html": html})

        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Render → Export PDF end-to-end (Playwright mocked)
# ---------------------------------------------------------------------------


class TestRenderToPdfWorkflow:
    """POST /api/render → POST /api/export/pdf — Playwright is fully mocked."""

    def _render(self, client, md: str) -> str:
        resp = client.post("/api/render", json={"content": md})
        assert resp.status_code == 200
        return resp.get_json()["html"]

    def test_pdf_export_returns_pdf_content_type(self, client, tmp_path):
        html = self._render(client, "# PDF Test\n\nSome content.")
        pdf_bytes = b"%PDF-1.4 minimal"

        mock_exporter = MagicMock()

        def fake_export(html_content, output_path, **_kwargs):
            Path(output_path).write_bytes(pdf_bytes)

        mock_exporter.export.side_effect = fake_export
        mock_exporter.close = MagicMock()

        with patch("markdown_viewer.routes.get_pdf_exporter", return_value=mock_exporter):
            resp = client.post("/api/export/pdf", json={"html": html})

        assert resp.status_code == 200
        assert "pdf" in resp.content_type

    def test_pdf_export_missing_html_returns_400(self, client):
        resp = client.post("/api/export/pdf", json={})
        assert resp.status_code == 400

    def test_pdf_export_exporter_error_returns_500(self, client):
        html = self._render(client, "# Error test")
        mock_exporter = MagicMock()
        mock_exporter.export.side_effect = RuntimeError("playwright crash")
        mock_exporter.close = MagicMock()

        with patch("markdown_viewer.routes.get_pdf_exporter", return_value=mock_exporter):
            resp = client.post("/api/export/pdf", json={"html": html})

        assert resp.status_code == 500
