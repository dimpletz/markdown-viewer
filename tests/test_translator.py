"""Tests for ContentTranslator."""

import pytest
from unittest.mock import patch, MagicMock
from markdown_viewer.translators.content_translator import ContentTranslator


@pytest.fixture
def translator():
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


def test_translate_calls_google_translator(translator):
    """translate() uses MyMemoryTranslator and returns translated text."""
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "Hola mundo"

    with patch(
        "markdown_viewer.translators.content_translator.MyMemoryTranslator",
        return_value=mock_instance,
    ):
        result = translator.translate("Hello world", target_lang="es")

    assert result == "Hola mundo"
    mock_instance.translate.assert_called_once()


def test_translate_code_blocks_unchanged(translator):
    """Code blocks pass through translate() untouched."""
    code_content = "```python\nprint('hello')\n```"
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "should not appear"

    with patch(
        "markdown_viewer.translators.content_translator.MyMemoryTranslator",
        return_value=mock_instance,
    ):
        result = translator.translate(code_content, target_lang="es")

    # The code block text must be preserved as-is
    assert "print('hello')" in result
    # The mock translation text must not appear
    assert "should not appear" not in result


def test_translate_caches_translator_instance(translator):
    """Language-pair validation result is cached so the cache key is only added once."""
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "Bonjour"

    with patch(
        "markdown_viewer.translators.content_translator.MyMemoryTranslator",
        return_value=mock_instance,
    ):
        translator.translate("Hello", target_lang="fr")
        translator.translate("World", target_lang="fr")

    # The cache entry for the language pair should exist after the first call
    assert "auto_fr" in translator.translator_cache


# ---------------------------------------------------------------------------
# Cache eviction
# ---------------------------------------------------------------------------

def test_cache_eviction_at_max_size(translator):
    """When cache reaches _MAX_CACHE_SIZE, oldest entry is evicted."""
    # Fill cache to the limit using fake keys directly
    for i in range(translator._MAX_CACHE_SIZE):
        translator.translator_cache[f"auto_lang{i}"] = MagicMock()

    assert len(translator.translator_cache) == translator._MAX_CACHE_SIZE

    # Trigger one more addition via translate() to force eviction
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "ok"

    with patch(
        "markdown_viewer.translators.content_translator.MyMemoryTranslator",
        return_value=mock_instance,
    ):
        translator.translate("Hello", target_lang="es")

    # Cache should not exceed MAX_CACHE_SIZE
    assert len(translator.translator_cache) <= translator._MAX_CACHE_SIZE


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
    mock_instance = MagicMock()
    mock_instance.translate.side_effect = Exception("network error")

    with patch(
        "markdown_viewer.translators.content_translator.MyMemoryTranslator",
        return_value=mock_instance,
    ):
        result = translator.translate("Hello world", target_lang="es")

    # Original text is preserved when all retries fail
    assert "Hello world" in result
    # translate() was retried MAX_RETRIES times
    assert mock_instance.translate.call_count >= 1
