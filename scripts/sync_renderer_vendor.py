#!/usr/bin/env python
"""Synchronize Electron renderer vendor assets from local node_modules.

This script copies the minified frontend runtime assets used by the renderer
into markdown_viewer/electron/renderer/vendor and strips source map markers to
avoid blocked .map requests under strict CSP.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ELECTRON_DIR = PROJECT_ROOT / "markdown_viewer" / "electron"
NODE_MODULES_DIR = ELECTRON_DIR / "node_modules"
VENDOR_DIR = ELECTRON_DIR / "renderer" / "vendor"

ASSET_MAP = {
    "marked/marked.min.js": "marked/marked.min.js",
    "mermaid/dist/mermaid.min.js": "mermaid/mermaid.min.js",
    "katex/dist/katex.min.js": "katex/katex.min.js",
    "katex/dist/contrib/auto-render.min.js": "katex/auto-render.min.js",
    "katex/dist/katex.min.css": "katex/katex.min.css",
    "highlight.js/lib/common.min.js": "highlightjs/highlight.min.js",
    "highlight.js/styles/monokai.min.css": "highlightjs/monokai.min.css",
    "axios/dist/axios.min.js": "axios/axios.min.js",
    "dompurify/dist/purify.min.js": "purify.min.js",
}

SOURCE_MAP_LINE = re.compile(r"^.*sourceMappingURL.*$", re.MULTILINE)
KATEX_FONT_URL = re.compile(r"url\((?:\"|')?(fonts/[^)\"']+)(?:\"|')?\)")
CDN_URL = re.compile(
    r"https?://(?:cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|unpkg\.com"
    r"|ajax\.googleapis\.com|stackpath\.bootstrapcdn\.com)",
    re.IGNORECASE,
)
INDEX_HTML = ELECTRON_DIR / "renderer" / "index.html"


def copy_asset(src_rel: str, dst_rel: str) -> None:
    """Copy one asset from node_modules to renderer/vendor."""
    source_path = NODE_MODULES_DIR / src_rel
    dest_path = VENDOR_DIR / dst_rel

    if not source_path.exists():
        raise FileNotFoundError(f"Missing source asset: {source_path}")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest_path)
    print(f"Synced {src_rel} -> {dest_path.relative_to(PROJECT_ROOT)}")


def sync_katex_fonts() -> None:
    """Copy KaTeX font files referenced by the vendored katex.min.css."""
    css_path = VENDOR_DIR / "katex" / "katex.min.css"
    css_text = css_path.read_text(encoding="utf-8")
    font_rel_paths = sorted(set(KATEX_FONT_URL.findall(css_text)))

    for font_rel in font_rel_paths:
        source_path = NODE_MODULES_DIR / "katex" / "dist" / font_rel
        dest_path = VENDOR_DIR / "katex" / font_rel

        if not source_path.exists():
            raise FileNotFoundError(f"Missing KaTeX font asset: {source_path}")

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)

    print(f"Synced {len(font_rel_paths)} KaTeX font files")


def strip_source_map_markers() -> None:
    """Remove sourceMappingURL lines from vendored JS/CSS files."""
    for path in VENDOR_DIR.rglob("*"):
        if path.suffix not in {".js", ".css"}:
            continue

        text = path.read_text(encoding="utf-8")
        cleaned = SOURCE_MAP_LINE.sub("", text)

        # Normalize trailing whitespace/newlines after line removal.
        cleaned = cleaned.rstrip() + "\n"

        if cleaned != text:
            path.write_text(cleaned, encoding="utf-8")


def assert_no_cdn_in_index() -> None:
    """Fail loudly if index.html still references an external CDN."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    matches = CDN_URL.findall(html)
    if matches:
        raise RuntimeError(
            f"index.html still contains CDN URL(s) after sync: {matches}\n"
            "Update the file to use local vendor/ paths."
        )


def main() -> int:
    """Run synchronization end-to-end."""
    if not NODE_MODULES_DIR.exists():
        print(
            "node_modules is missing. Run npm install in markdown_viewer/electron first.",
            file=sys.stderr,
        )
        return 1

    try:
        for source_rel, dest_rel in ASSET_MAP.items():
            copy_asset(source_rel, dest_rel)

        sync_katex_fonts()
        strip_source_map_markers()
        assert_no_cdn_in_index()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Vendor sync failed: {exc}", file=sys.stderr)
        return 1

    print("Renderer vendor sync complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
