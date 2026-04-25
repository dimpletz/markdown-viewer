"""Tests for ContentTranslator."""

# pylint: disable=redefined-outer-name,protected-access
from unittest.mock import patch

import pytest

from markdown_viewer.translators.content_translator import (
    ContentTranslator,
    _mymemory_translate,
)


@pytest.fixture
def translator():
    """Return a fresh ContentTranslator instance."""
    return ContentTranslator()


# ---------------------------------------------------------------------------
# _split_content
# ---------------------------------------------------------------------------


def test_split_content_code_block_not_translatable(translator):
    """Fenced code blocks are marked non-translatable."""
    content = "```python\nprint('hello')\n```"
    chunks = translator._split_content(content)
    code_chunks = [c for c in chunks if c["text"].startswith("```")]
    assert code_chunks, "Expected at least one code chunk"
    assert all(not c["translatable"] for c in code_chunks)


def test_split_content_plain_text_is_translatable(translator):
    """Plain text paragraph is marked translatable."""
    content = "Hello world, this is a test."
    chunks = translator._split_content(content)
    assert chunks, "Expected at least one chunk"
    assert any(c["translatable"] for c in chunks)


def test_split_content_inline_code_not_translatable(translator):
    """Inline code spans are marked non-translatable."""
    content = "Use `print()` to output text."
    chunks = translator._split_content(content)
    inline_chunks = [c for c in chunks if c["text"].startswith("`")]
    assert inline_chunks, "Expected inline code chunk"
    assert all(not c["translatable"] for c in inline_chunks)


def test_split_content_mixed_preserves_structure(translator):
    """Mixed content produces both translatable and non-translatable chunks."""
    content = "Some text.\n\n```\ncode block\n```\n\nMore text."
    chunks = translator._split_content(content)
    translatable = [c for c in chunks if c["translatable"]]
    non_translatable = [c for c in chunks if not c["translatable"]]
    assert translatable
    assert non_translatable


# ---------------------------------------------------------------------------
# translate
# ---------------------------------------------------------------------------


def test_translate_invalid_language_raises(translator):
    """Passing an unsupported target language raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported target language"):
        translator.translate("Hello world", target_lang="xx-INVALID")


def test_translate_calls_mymemory(translator):
    """translate() delegates translatable chunks to _mymemory_translate."""
    with patch(
        "markdown_viewer.translators.content_translator._mymemory_translate",
        return_value="Hola mundo",
    ):
        result = translator.translate("Hello world", target_lang="es")

    assert result == "Hola mundo"


def test_translate_code_blocks_unchanged(translator):
    """Code blocks pass through translate() untouched."""
    code_content = "```python\nprint('hello')\n```"

    with patch(
        "markdown_viewer.translators.content_translator._mymemory_translate",
        return_value="should not appear",
    ):
        result = translator.translate(code_content, target_lang="es")

    assert "print('hello')" in result
    assert "should not appear" not in result


def test_translate_multiple_calls_same_language(translator):
    """translate() can be called multiple times for the same language pair."""
    with patch(
        "markdown_viewer.translators.content_translator._mymemory_translate",
        return_value="Bonjour",
    ) as mock_fn:
        translator.translate("Hello", target_lang="fr")
        translator.translate("World", target_lang="fr")

    assert mock_fn.call_count == 2


def test_mymemory_translate_chunks_long_text():
    """_mymemory_translate splits text longer than 500 chars into multiple requests."""
    long_text = "This is a sentence. " * 30  # ~600 chars
    call_sizes = []

    def fake_request(text, _src, _tgt):
        call_sizes.append(len(text))
        return text

    with patch(
        "markdown_viewer.translators.content_translator._mymemory_request",
        side_effect=fake_request,
    ):
        _mymemory_translate(long_text, "en-GB", "es-ES")

    assert len(call_sizes) > 1, "Expected text to be chunked into multiple requests"
    assert all(n <= 500 for n in call_sizes), "A chunk exceeded the 500-char limit"


# ---------------------------------------------------------------------------
# get_supported_languages
# ---------------------------------------------------------------------------


def test_get_supported_languages_returns_dict(translator):
    """get_supported_languages returns a non-empty dict."""
    langs = translator.get_supported_languages()
    assert isinstance(langs, dict)
    assert "en" in langs
    assert "es" in langs


def test_translate_falls_back_to_original_when_all_retries_fail(translator):
    """When all retries fail the original text chunk is kept."""
    with patch(
        "markdown_viewer.translators.content_translator._mymemory_translate",
        side_effect=Exception("network error"),
    ):
        result = translator.translate("Hello world", target_lang="es")

    assert "Hello world" in result


# ---------------------------------------------------------------------------
# _mymemory_request
# ---------------------------------------------------------------------------


def test_mymemory_request_success():
    """_mymemory_request returns translated text on a 200 response."""
    import json
    from unittest.mock import MagicMock, patch

    from markdown_viewer.translators.content_translator import _mymemory_request

    fake_response_data = {"responseStatus": 200, "responseData": {"translatedText": "Hola"}}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _mymemory_request("Hello", "en-GB", "es-ES")

    assert result == "Hola"


def test_mymemory_request_non_200_returns_original():
    """_mymemory_request returns original text when responseStatus != 200."""
    import json
    from unittest.mock import MagicMock, patch

    from markdown_viewer.translators.content_translator import _mymemory_request

    fake_response_data = {"responseStatus": 429, "responseData": {"translatedText": None}}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _mymemory_request("Hello", "en-GB", "es-ES")

    assert result == "Hello"


def test_mymemory_request_timeout_raises():
    """_mymemory_request raises TimeoutError when the socket times out."""
    import socket
    from unittest.mock import patch

    from markdown_viewer.translators.content_translator import _mymemory_request

    with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
        with pytest.raises(TimeoutError):
            _mymemory_request("Hello", "en-GB", "es-ES")


# ---------------------------------------------------------------------------
# _mymemory_translate edge cases
# ---------------------------------------------------------------------------


def test_mymemory_translate_empty_text():
    """_mymemory_translate returns empty text immediately without API call."""
    from unittest.mock import patch

    from markdown_viewer.translators.content_translator import _mymemory_translate

    with patch("markdown_viewer.translators.content_translator._mymemory_request") as mock_req:
        result = _mymemory_translate("   ", "en-GB", "es-ES")

    assert result.strip() == ""
    mock_req.assert_not_called()


def test_mymemory_translate_short_text_single_request():
    """_mymemory_translate calls _mymemory_request once for short text."""
    from unittest.mock import patch

    from markdown_viewer.translators.content_translator import _mymemory_translate

    with patch(
        "markdown_viewer.translators.content_translator._mymemory_request",
        return_value="Hola",
    ) as mock_req:
        result = _mymemory_translate("Hello", "en-GB", "es-ES")

    mock_req.assert_called_once_with("Hello", "en-GB", "es-ES")
    assert result == "Hola"


def test_mymemory_translate_single_long_sentence():
    """_mymemory_translate hard-splits a single sentence exceeding 500 chars."""
    from unittest.mock import patch

    from markdown_viewer.translators.content_translator import _mymemory_translate

    long_sentence = "X" * 600  # one sentence, no split points, longer than 500
    chunks_seen = []

    def fake_request(text, _s, _t):
        chunks_seen.append(len(text))
        return text

    with patch(
        "markdown_viewer.translators.content_translator._mymemory_request",
        side_effect=fake_request,
    ):
        _mymemory_translate(long_sentence, "en-GB", "es-ES")

    assert len(chunks_seen) >= 2
    assert all(n <= 500 for n in chunks_seen)


# ---------------------------------------------------------------------------
# translate() TimeoutError propagation
# ---------------------------------------------------------------------------


def test_translate_timeout_error_propagates(translator):
    """translate() re-raises TimeoutError when a chunk times out on the last retry."""
    with patch(
        "markdown_viewer.translators.content_translator._mymemory_translate",
        side_effect=TimeoutError("too slow"),
    ):
        with pytest.raises(TimeoutError):
            translator.translate("Hello world", target_lang="es")
