"""Regression tests — one test per confirmed bug fix.

Each test is named after what it catches. Add a new test every time a
bug is fixed; never remove tests from this file.

Index
-----
REG-001  Word exporter: relative /api/image URLs not absolutized → broken images in .docx
REG-002  Word exporter: absolutizing used hard-coded port 5000 regardless of config
REG-003  Electron renderer: CDN script tags triggered blocked sourceMappingURL fetches
         (connect-src CSP violation for .map files from jsdelivr/cdnjs)
REG-004  Electron renderer: stale sourceMappingURL directives in vendored JS/CSS cause
         DevTools noise even when script loads from vendor/
REG-005  Favourites search: raw FTS5 user input could cause query syntax errors /
         injection via special chars (" ' * ( ) : -)
REG-006  /api/image endpoint: no extension allow-list let any file type be served
REG-007  /api/open endpoint: missing path check let directory paths through as 400
         instead of the clearer explicit guard
"""

# pylint: disable=redefined-outer-name,import-outside-toplevel

import os
import tempfile
import urllib.parse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from markdown_viewer.app import create_app

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path):
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "WTF_CSRF_ENABLED": False,
            "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
            "TEMP_FOLDER": str(tmp_path / "temp"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )
    return app.test_client()


# ---------------------------------------------------------------------------
# REG-001 / REG-002  Word exporter port handling
# Regression: relative /api/image src attributes were left as-is, causing
# broken images in Word output; then port was hard-coded to 5000.
# ---------------------------------------------------------------------------


class TestReg001WordExporterRelativeImages:
    """REG-001: /api/image relative URLs must be absolutized before Word export."""

    def test_route_passes_backend_port_to_exporter(self, client):
        """Route must pass backend_port kwarg so the exporter can absolutize /api/image URLs."""
        exporter = MagicMock()
        exporter.export.side_effect = lambda html, md, path, **kw: Path(path).write_bytes(
            b"PK\x03\x04"
        )
        with patch("markdown_viewer.routes.get_word_exporter", return_value=exporter):
            client.post("/api/export/word", json={"html": "<p>test</p>"})
        assert exporter.export.called, "exporter.export was never called"
        call_kwargs = exporter.export.call_args[1]
        assert "backend_port" in call_kwargs, (
            "Route must pass backend_port kwarg to WordExporter.export() "
            "so that relative /api/image URLs can be absolutized."
        )

    def test_word_exporter_absolutizes_relative_api_image_url(self):
        """WordExporter.export() must rewrite /api/image relative URLs to absolute ones."""
        from markdown_viewer.exporters.word_exporter import WordExporter

        html_input = '<img src="/api/image?path=%2Ftmp%2Ftest.png">'
        exporter = WordExporter()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            output_path = tmp.name
        try:
            from unittest.mock import patch as _patch, MagicMock as _MM

            with (
                _patch.object(exporter, "_load_html") as mock_load,
                _patch.object(exporter, "_cleanup"),
            ):
                mock_page = _MM()
                mock_page.content.return_value = html_input
                exporter.page = mock_page
                with _patch("markdown_viewer.exporters.word_exporter.Document"):
                    exporter.export(html_input, "", output_path, backend_port=5000)
                loaded = mock_load.call_args[0][0]
                assert "http://localhost:5000/api/image" in loaded, (
                    "WordExporter did not absolutize /api/image URL. " f"Got: {loaded[:200]}"
                )
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestReg002WordExporterPortFromEnv:
    """REG-002: Backend port must come from BACKEND_PORT env var, not hard-coded 5000."""

    def test_backend_port_env_var_is_used(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BACKEND_PORT", "7777")
        (tmp_path / "temp").mkdir()
        (tmp_path / "uploads").mkdir()
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "WTF_CSRF_ENABLED": False,
                "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
                "TEMP_FOLDER": str(tmp_path / "temp"),
                "UPLOAD_FOLDER": str(tmp_path / "uploads"),
            }
        )
        captured = []

        def fake_export(html, markdown, output_path, **kwargs):
            captured.append(html)
            Path(output_path).write_bytes(b"PK\x03\x04")

        mock_exporter = MagicMock()
        mock_exporter.export.side_effect = lambda html, md, path, **kw: Path(path).write_bytes(
            b"PK\x03\x04"
        )
        mock_exporter.close = MagicMock()

        with app.test_client() as c:
            with patch("markdown_viewer.routes.get_word_exporter", return_value=mock_exporter):
                c.post(
                    "/api/export/word",
                    json={"html": '<img src="/api/image?path=%2Ftmp%2Fx.png">'},
                )

        assert mock_exporter.export.called, "exporter.export was never called"
        call_kwargs = mock_exporter.export.call_args[1]
        assert call_kwargs.get("backend_port") == 7777, (
            "BACKEND_PORT=7777 env var was not forwarded to exporter. "
            f"Got backend_port={call_kwargs.get('backend_port')!r}"
        )


# ---------------------------------------------------------------------------
# REG-003  Electron renderer: no CDN URLs in index.html
# Regression: DOMPurify (and other libs) were loaded from jsdelivr/cdnjs,
# which caused blocked connect-src fetch of .map files under the strict CSP.
# ---------------------------------------------------------------------------


class TestReg003NoCdnInRendererIndex:
    """REG-003: index.html must not reference any external CDN."""

    def test_no_cdn_urls_in_index_html(self):
        import re

        index = (
            Path(__file__).resolve().parent.parent.parent
            / "markdown_viewer"
            / "electron"
            / "renderer"
            / "index.html"
        )
        assert index.exists(), "index.html not found"
        html = index.read_text(encoding="utf-8")
        cdn_pattern = re.compile(
            r"https?://(?:cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|unpkg\.com"
            r"|ajax\.googleapis\.com|stackpath\.bootstrapcdn\.com)",
            re.IGNORECASE,
        )
        matches = cdn_pattern.findall(html)
        assert not matches, f"CDN URL(s) re-introduced in index.html: {matches}"


# ---------------------------------------------------------------------------
# REG-004  Vendored assets: no sourceMappingURL directives
# Regression: stale sourceMappingURL lines in vendored JS/CSS cause browsers
# to attempt fetching .map files, which are blocked by connect-src CSP.
# ---------------------------------------------------------------------------


class TestReg004NoSourceMapInVendor:
    """REG-004: vendored JS/CSS must not contain sourceMappingURL."""

    def test_no_source_map_url_in_any_vendor_file(self):
        vendor_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "markdown_viewer"
            / "electron"
            / "renderer"
            / "vendor"
        )
        offenders = []
        for f in list(vendor_dir.rglob("*.js")) + list(vendor_dir.rglob("*.css")):
            text = f.read_text(encoding="utf-8", errors="replace")
            if "sourceMappingURL" in text:
                offenders.append(str(f.relative_to(vendor_dir)))
        assert not offenders, (
            "sourceMappingURL found in vendored files "
            f"(run sync_renderer_vendor.py to fix): {offenders}"
        )


# ---------------------------------------------------------------------------
# REG-005  Favourites search: FTS5 injection via special characters
# Regression: unsanitized user input passed directly to FTS5 MATCH queries
# raised sqlite3.OperationalError on inputs like quotes or colons.
# ---------------------------------------------------------------------------


class TestReg005FavouritesFtsInjection:
    """REG-005: FTS5 special chars in search query must not crash the API."""

    @pytest.fixture()
    def fav_client(self, tmp_path, monkeypatch):
        test_db = tmp_path / "fts_reg.db"
        import markdown_viewer.db.database as db_module

        monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)
        db_module.FTS5_ENABLED = False
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "WTF_CSRF_ENABLED": False,
                "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
            }
        )
        with app.app_context():
            db_module.init_db()
        return app.test_client()

    @pytest.mark.parametrize(
        "malicious_q",
        [
            '"unmatched quote',
            "a:b",
            "* wildcard",
            "(unbalanced",
            "col:val*'inject",
            "a OR b AND NOT c",
            "'' OR 1=1 --",
        ],
    )
    def test_fts_injection_does_not_crash(self, fav_client, malicious_q):
        encoded = urllib.parse.quote(malicious_q, safe="")
        resp = fav_client.get(f"/api/favourites/search?q={encoded}")
        # Must return 200 (empty results) or 400, never 500
        assert resp.status_code in (
            200,
            400,
        ), f"FTS injection '{malicious_q}' caused unexpected status {resp.status_code}"


# ---------------------------------------------------------------------------
# REG-006  /api/image: extension allow-list enforced
# Regression: without the extension check, any file type (e.g. .txt, .py)
# inside the allowed directory could be read and served.
# ---------------------------------------------------------------------------


class TestReg006ImageExtensionAllowList:
    """REG-006: /api/image must reject non-image file types."""

    def test_text_file_returns_400(self, client, tmp_path):
        txt = tmp_path / "secret.txt"
        txt.write_text("passwords", encoding="utf-8")
        encoded = urllib.parse.quote(str(txt), safe="")
        resp = client.get(f"/api/image?path={encoded}")
        assert resp.status_code == 400, "Text file must be rejected by /api/image"

    def test_python_file_returns_400(self, client, tmp_path):
        py = tmp_path / "app.py"
        py.write_text("import os", encoding="utf-8")
        encoded = urllib.parse.quote(str(py), safe="")
        resp = client.get(f"/api/image?path={encoded}")
        assert resp.status_code == 400, ".py file must be rejected by /api/image"

    def test_png_file_returns_200(self, client, tmp_path):
        png = tmp_path / "img.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        encoded = urllib.parse.quote(str(png), safe="")
        resp = client.get(f"/api/image?path={encoded}")
        assert resp.status_code == 200, "Valid PNG inside allowed dir must be served"


# ---------------------------------------------------------------------------
# REG-007  /api/open: directory path returns 400 not 500
# Regression: passing a directory path to /api/open raised an unhandled
# IsADirectoryError on Linux instead of a clean 400 response.
# ---------------------------------------------------------------------------


class TestReg007OpenFileDirectory:
    """REG-007: /api/open with a directory path must return 400."""

    def test_directory_path_returns_400(self, client, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        resp = client.post("/api/file/open", json={"path": str(sub)})
        assert resp.status_code == 400, f"Directory path must return 400, got {resp.status_code}"
