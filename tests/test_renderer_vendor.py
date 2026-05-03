"""Automated checks that the Electron renderer uses only local vendor assets.

These tests run in the normal pytest suite (no manual steps required).
They enforce:
1. No CDN URLs appear in index.html — any CDN reference would violate CSP
   connect-src and cause blocked requests.
2. Every vendor asset referenced by index.html exists on disk so the renderer
   cannot silently fall back to a missing file.
3. No sourceMappingURL directives remain in vendored JS/CSS files — stale
   map references trigger blocked fetch requests even when the script itself
   loads fine.
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDERER_DIR = REPO_ROOT / "markdown_viewer" / "electron" / "renderer"
INDEX_HTML = RENDERER_DIR / "index.html"
VENDOR_DIR = RENDERER_DIR / "vendor"

CDN_PATTERN = re.compile(
    r"(https?://(?:cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|unpkg\.com|"
    r"ajax\.googleapis\.com|stackpath\.bootstrapcdn\.com))",
    re.IGNORECASE,
)

SOURCE_MAP_PATTERN = re.compile(r"sourceMappingURL", re.IGNORECASE)

# Vendor assets referenced directly in index.html (relative to renderer/).
EXPECTED_VENDOR_FILES = [
    "vendor/katex/katex.min.css",
    "vendor/highlightjs/monokai.min.css",
    "vendor/marked/marked.min.js",
    "vendor/mermaid/mermaid.min.js",
    "vendor/katex/katex.min.js",
    "vendor/katex/auto-render.min.js",
    "vendor/highlightjs/highlight.min.js",
    "vendor/axios/axios.min.js",
    "vendor/purify.min.js",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _index_html_text() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def _vendor_js_css_files():
    """Return every .js and .css file under vendor/."""
    return list(VENDOR_DIR.rglob("*.js")) + list(VENDOR_DIR.rglob("*.css"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNoCdnInRenderer:
    """index.html must not reference any external CDN."""

    def test_index_html_has_no_cdn_urls(self):
        html = _index_html_text()
        matches = CDN_PATTERN.findall(html)
        assert not matches, (
            "index.html contains CDN URL(s) — these violate the renderer CSP "
            f"connect-src directive: {matches}"
        )

    def test_index_html_has_no_http_script_src(self):
        """No <script src="http..."> or <link href="http..."> allowed."""
        html = _index_html_text()
        remote_refs = re.findall(r'(?:src|href)=["\']https?://', html, re.IGNORECASE)
        assert not remote_refs, "index.html contains remote src/href references: " f"{remote_refs}"


class TestVendorFilesExist:
    """Every vendor asset referenced in index.html must be present on disk."""

    @pytest.mark.parametrize("rel_path", EXPECTED_VENDOR_FILES)
    def test_vendor_file_exists(self, rel_path: str):
        full_path = RENDERER_DIR / rel_path
        assert full_path.exists(), (
            f"Vendored asset is missing: {full_path}\n"
            "Run `python scripts/sync_renderer_vendor.py` after `npm install` "
            "to populate vendor assets from node_modules."
        )


class TestNoSourceMapInVendor:
    """Vendored JS/CSS must not contain sourceMappingURL — those trigger blocked
    .map requests under the strict CSP connect-src policy."""

    @pytest.mark.parametrize("vendor_file", _vendor_js_css_files(), ids=lambda p: p.name)
    def test_no_source_map_url(self, vendor_file: Path):
        text = vendor_file.read_text(encoding="utf-8", errors="replace")
        assert not SOURCE_MAP_PATTERN.search(text), (
            f"sourceMappingURL found in {vendor_file.relative_to(REPO_ROOT)} — "
            "run sync_renderer_vendor.py to strip it."
        )
