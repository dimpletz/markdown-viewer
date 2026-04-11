"""
Content translator using the MyMemory translation API directly.
"""

# pylint: disable=broad-exception-caught

import json
import re
import logging
import socket
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 0  # seconds — don't sleep between retries; fail fast
TRANSLATE_CHUNK_TIMEOUT = 10  # seconds per individual chunk call

# MyMemory free tier: maximum characters per API request
_MYMEMORY_MAX_CHARS = 500


def _mymemory_request(text: str, source_locale: str, target_locale: str) -> str:
    """Send a single request to the MyMemory free translation API.

    Args:
        text: Text to translate (≤ 500 chars for the free tier).
        source_locale: MyMemory locale string, e.g. ``en-GB`` or ``autodetect``.
        target_locale: MyMemory locale string, e.g. ``es-ES``.

    Returns:
        Translated text, or *text* unchanged on API error.

    Raises:
        TimeoutError: If the HTTP request exceeds TRANSLATE_CHUNK_TIMEOUT seconds.
    """
    params = urllib.parse.urlencode({"q": text, "langpair": f"{source_locale}|{target_locale}"})
    url = f"https://api.mymemory.translated.net/get?{params}"  # nosec — host is a constant
    try:
        with urllib.request.urlopen(url, timeout=TRANSLATE_CHUNK_TIMEOUT) as resp:  # nosec
            data = json.loads(resp.read())
    except socket.timeout as exc:
        raise TimeoutError(
            f"MyMemory API timed out after {TRANSLATE_CHUNK_TIMEOUT}s"
        ) from exc
    if data.get("responseStatus") == 200:
        return data["responseData"].get("translatedText") or text
    return text


def _mymemory_translate(text: str, source_locale: str, target_locale: str) -> str:
    """Translate *text* via the MyMemory API, respecting the 500-char free-tier limit.

    Longer text is split at sentence/line boundaries; each piece is translated
    separately and the results are rejoined with a single space.
    """
    if not text.strip():
        return text
    if len(text) <= _MYMEMORY_MAX_CHARS:
        return _mymemory_request(text, source_locale, target_locale)

    # Split at sentence/newline boundaries and merge into ≤ 500-char batches
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    parts: List[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + (1 if current else 0) <= _MYMEMORY_MAX_CHARS:
            current = (current + " " + sentence).strip() if current else sentence
        else:
            if current:
                parts.append(current)
            # A single sentence longer than the limit: hard-split it
            if len(sentence) > _MYMEMORY_MAX_CHARS:
                for k in range(0, len(sentence), _MYMEMORY_MAX_CHARS):
                    parts.append(sentence[k : k + _MYMEMORY_MAX_CHARS])
                current = ""
            else:
                current = sentence
    if current:
        parts.append(current)
    return " ".join(_mymemory_request(p, source_locale, target_locale) for p in parts)


class ContentTranslator:
    """Translate markdown content while preserving formatting."""

    # Maps short user-facing codes → MyMemory locale codes
    _LANG_MAP: Dict[str, str] = {
        "auto": "autodetect",
        "en": "en-GB",
        "es": "es-ES",
        "fr": "fr-FR",
        "de": "de-DE",
        "it": "it-IT",
        "pt": "pt-PT",
        "ru": "ru-RU",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "zh-CN": "zh-CN",
        "zh-TW": "zh-TW",
        "ar": "ar-SA",
        "hi": "hi-IN",
        "nl": "nl-NL",
        "pl": "pl-PL",
        "tr": "tr-TR",
    }

    def __init__(self):
        """Initialize translator."""

    def _to_locale(self, code: str) -> str:
        """Convert a short language code to a MyMemory locale code."""
        return self._LANG_MAP.get(code, code)

    def translate(  # pylint: disable=too-many-locals
        self, content: str, source_lang: str = "auto", target_lang: str = "en"
    ) -> str:
        """
        Translate markdown content.

        Args:
            content: Markdown content to translate
            source_lang: Source language code (default: 'auto')
            target_lang: Target language code (default: 'en')

        Returns:
            Translated content with preserved markdown formatting

        Raises:
            ValueError: If target language is not supported
        """
        # Validate target language
        supported = self.get_supported_languages()
        if target_lang not in supported and target_lang != "auto":
            raise ValueError(
                f"Unsupported target language: {target_lang}. "
                f"Supported languages: {', '.join(list(supported.keys())[:10])}..."
            )

        # Split content into translatable chunks
        chunks = self._split_content(content)

        def translate_chunk(index_chunk):
            i, chunk = index_chunk
            if not chunk["translatable"]:
                return i, chunk["text"]
            for attempt in range(MAX_RETRIES):
                try:
                    result = _mymemory_translate(
                        chunk["text"],
                        self._to_locale(source_lang),
                        self._to_locale(target_lang),
                    )
                    return i, result
                except TimeoutError as exc:
                    logger.error(
                        "Translation chunk %s timed out after %ss", i + 1, TRANSLATE_CHUNK_TIMEOUT
                    )
                    if attempt == MAX_RETRIES - 1:
                        raise TimeoutError(
                            "Translation timed out. The document may be too large or the "
                            "translation service is unavailable."
                        ) from exc
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(
                            "Translation attempt %s failed for chunk %s: %s. Retrying...",
                            attempt + 1,
                            i + 1,
                            e,
                        )
                    else:
                        logger.error(
                            "Translation failed for chunk %s after %s attempts: %s",
                            i + 1,
                            MAX_RETRIES,
                            e,
                        )
                        return i, chunk["text"]

            return i, chunk["text"]  # fallback (all retries exhausted)

        # Translate all chunks in parallel (up to max_parallel workers)
        max_parallel = 5
        results = [None] * len(chunks)
        with ThreadPoolExecutor(max_workers=max_parallel) as pool:
            futures = {pool.submit(translate_chunk, (i, c)): i for i, c in enumerate(chunks)}
            for future in futures:
                idx, text = future.result()  # re-raises TimeoutError if any chunk timed out
                results[idx] = text

        return "".join(results)

    def _split_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Split content into translatable and non-translatable chunks.

        Returns:
            List of dicts with 'text' and 'translatable' keys
        """
        chunks = []

        # Split by code blocks first
        parts = re.split(r"(```[\s\S]*?```)", content)

        for part in parts:
            if part.startswith("```"):
                # Code block - don't translate
                chunks.append({"text": part, "translatable": False})
            elif part.strip():
                # Regular content - translate
                # But preserve inline code
                subparts = re.split(r"(`[^`]+`)", part)
                for subpart in subparts:
                    if subpart.startswith("`"):
                        chunks.append({"text": subpart, "translatable": False})
                    elif subpart.strip():
                        chunks.append({"text": subpart, "translatable": True})

        return chunks

    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported language codes."""
        return {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh-CN": "Chinese (Simplified)",
            "zh-TW": "Chinese (Traditional)",
            "ar": "Arabic",
            "hi": "Hindi",
            "nl": "Dutch",
            "pl": "Polish",
            "tr": "Turkish",
        }
