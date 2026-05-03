"""Integration: translate workflow — route → translator layer.

The external MyMemory HTTP call is mocked; routing, schema validation,
and language-lookup logic are exercised for real.
"""

# pylint: disable=redefined-outer-name

from unittest.mock import patch, MagicMock

import pytest

from markdown_viewer.app import create_app

# ---------------------------------------------------------------------------
# Fixture
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


def _mock_translator(translated_text: str = "Bonjour le monde"):
    """Return a mock ContentTranslator that resolves to translated_text."""
    mock = MagicMock()
    mock.translate.return_value = translated_text
    mock.get_supported_languages.return_value = {
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
    }
    mock.close = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Happy-path workflow
# ---------------------------------------------------------------------------


class TestTranslateWorkflow:
    def test_translate_returns_200_with_translated_text(self, client):
        mock = _mock_translator("Bonjour le monde")
        with patch("markdown_viewer.routes.get_translator", return_value=mock):
            resp = client.post(
                "/api/translate",
                json={"content": "Hello world", "target": "fr"},
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["translated"] == "Bonjour le monde"

    def test_translate_preserves_code_blocks(self, client):
        """Translator is called; code-block preservation is tested in the unit suite."""
        md = "# Title\n\n```python\nprint('hi')\n```"
        mock = _mock_translator(md)
        with patch("markdown_viewer.routes.get_translator", return_value=mock):
            resp = client.post(
                "/api/translate",
                json={"content": md, "target": "de"},
            )
        assert resp.status_code == 200

    def test_translate_with_explicit_source_language(self, client):
        mock = _mock_translator("Hola mundo")
        with patch("markdown_viewer.routes.get_translator", return_value=mock):
            resp = client.post(
                "/api/translate",
                json={"content": "Hello world", "source": "en", "target": "es"},
            )
        assert resp.status_code == 200
        assert resp.get_json()["translated"] == "Hola mundo"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestTranslateValidation:
    def test_missing_target_returns_400(self, client):
        resp = client.post("/api/translate", json={"content": "Hello"})
        assert resp.status_code == 400

    def test_missing_content_returns_400(self, client):
        resp = client.post("/api/translate", json={"target": "fr"})
        assert resp.status_code == 400

    def test_empty_body_returns_400(self, client):
        resp = client.post("/api/translate", json={})
        assert resp.status_code == 400

    def test_unsupported_language_returns_400(self, client):
        resp = client.post(
            "/api/translate",
            json={"content": "Hello", "target": "xx"},
        )
        assert resp.status_code == 400

    def test_content_over_1mb_rejected(self, client):
        big = "x" * (1 * 1024 * 1024 + 1)
        resp = client.post("/api/translate", json={"content": big, "target": "fr"})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Translator service error propagation
# ---------------------------------------------------------------------------


class TestTranslateErrorPropagation:
    def test_translator_runtime_error_returns_500(self, client):
        mock = MagicMock()
        mock.translate.side_effect = RuntimeError("network down")
        mock.get_supported_languages.return_value = {
            "fr": "French",
            "de": "German",
            "es": "Spanish",
        }
        mock.close = MagicMock()
        with patch("markdown_viewer.routes.get_translator", return_value=mock):
            resp = client.post(
                "/api/translate",
                json={"content": "Hello", "target": "fr"},
            )
        assert resp.status_code == 500

    def test_error_message_is_generic_not_internal(self, client):
        """Error body must not leak internal exception details."""
        mock = MagicMock()
        mock.translate.side_effect = RuntimeError("secret internal path /etc/passwd")
        mock.get_supported_languages.return_value = {
            "fr": "French",
            "de": "German",
            "es": "Spanish",
        }
        mock.close = MagicMock()
        with patch("markdown_viewer.routes.get_translator", return_value=mock):
            resp = client.post(
                "/api/translate",
                json={"content": "Hello", "target": "fr"},
            )
        body = resp.get_data(as_text=True)
        assert "/etc/passwd" not in body
        assert "secret internal path" not in body
