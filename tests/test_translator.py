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
