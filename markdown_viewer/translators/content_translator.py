"""
Content translator using deep-translator library.
"""

# pylint: disable=broad-exception-caught

import re
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from deep_translator import MyMemoryTranslator

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 0  # seconds — don't sleep between retries; fail fast
TRANSLATE_CHUNK_TIMEOUT = 10  # seconds per individual chunk call


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
        self.translator_cache: dict = {}

    _MAX_CACHE_SIZE = 20  # Prevent unbounded memory growth

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

        # Get or create translator
        translator_key = f"{source_lang}_{target_lang}"

        if translator_key not in self.translator_cache:
            try:
                # Evict oldest entry when cache is full
                if len(self.translator_cache) >= self._MAX_CACHE_SIZE:
                    self.translator_cache.pop(next(iter(self.translator_cache)))
                self.translator_cache[translator_key] = True  # mark as validated
                logger.debug("Validated translator key %s", translator_key)
            except Exception as e:
                logger.error("Failed to validate translator: %s", e)
                raise ValueError(f"Failed to initialize translator: {e}") from e

        # Split content into translatable chunks
        chunks = self._split_content(content)

        def translate_chunk(index_chunk):
            i, chunk = index_chunk
            if not chunk["translatable"]:
                return i, chunk["text"]
            for attempt in range(MAX_RETRIES):
                try:
                    # Each call gets its own short-lived translator instance to avoid
                    # shared-state issues when called from multiple threads simultaneously.
                    t = MyMemoryTranslator(
                        source=self._to_locale(source_lang), target=self._to_locale(target_lang)
                    )
                    with ThreadPoolExecutor(max_workers=1) as ex:
                        future = ex.submit(t.translate, chunk["text"])
                        result = future.result(timeout=TRANSLATE_CHUNK_TIMEOUT)
                    # deep-translator can return None on silent failure; fall back to original
                    return i, result if isinstance(result, str) else chunk["text"]
                except FuturesTimeout as exc:
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
