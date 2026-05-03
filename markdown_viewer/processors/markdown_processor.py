"""
Markdown processor with support for extensions, code highlighting, and diagrams.
"""

# pylint: disable=duplicate-code

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

import markdown
from pymdownx import emoji
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module

logger = logging.getLogger(__name__)


class MarkdownProcessor:  # pylint: disable=too-few-public-methods
    """Process markdown content with various extensions."""

    def __init__(
        self,
        custom_extensions: Optional[List[str]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the markdown processor with extensions.

        Args:
            custom_extensions: Optional list of markdown extensions
            custom_config: Optional dictionary of extension configurations
        """
        self.extensions = custom_extensions or self._default_extensions()
        self.extension_configs = custom_config or self._default_config()

    def _default_extensions(self) -> List[str]:
        """Get default markdown extensions."""
        return [
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.toc",
            "markdown.extensions.nl2br",
            "markdown.extensions.sane_lists",
            "markdown.extensions.md_in_html",
            "pymdownx.superfences",
            "pymdownx.highlight",
            "pymdownx.emoji",
            "pymdownx.tasklist",
            "pymdownx.arithmatex",
            "pymdownx.mark",
            "pymdownx.tilde",
            "pymdownx.caret",
            "pymdownx.keys",
            "pymdownx.magiclink",
        ]

    def _default_config(self) -> Dict[str, Any]:
        """Get default extension configurations."""
        return {
            "pymdownx.highlight": {
                "use_pygments": True,
                "linenums": True,
                "linenums_style": "pymdownx-inline",
            },
            "pymdownx.superfences": {
                "custom_fences": [
                    {"name": "mermaid", "class": "mermaid", "format": self._mermaid_formatter}
                ]
            },
            "pymdownx.emoji": {
                "emoji_index": emoji.gemoji,
                "emoji_generator": emoji.to_svg,
                "options": {
                    "attributes": {"align": "absmiddle", "height": "20px", "width": "20px"},
                    "image_path": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/",
                    "non_standard_image_path": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/",  # pylint: disable=line-too-long
                },
            },
            "pymdownx.arithmatex": {"generic": True},
            "markdown.extensions.toc": {
                "permalink": False,
                "marker": "[TOC]",
                "toc_depth": "2-6",
                "title": "Table of Contents",
            },
            "codehilite": {"css_class": "highlight", "linenums": False},
        }

    def _mermaid_formatter(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, source, _language, _css_class, _options, _md, **_kwargs
    ):
        """Custom formatter for Mermaid diagrams."""
        return f'<div class="mermaid">\n{source}\n</div>'

    _INCLUDE_PATTERN = re.compile(r"!\[\[([^\]]+)\]\]")
    _MD_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    _ALLOWED_INCLUDE_EXTENSIONS = {".md", ".markdown", ".mdown"}
    _MAX_INCLUDE_DEPTH = 10

    def _absolutize_md_image_paths(self, content: str, file_dir: Path) -> str:
        """Rewrite relative markdown image paths to absolute paths.

        This ensures that when an embedded file's content is inlined into a
        parent document, its images still resolve correctly regardless of the
        parent file's location.
        """

        def replace_img(match: re.Match) -> str:
            alt = match.group(1)
            src = match.group(2)
            # Leave remote URLs, data URIs, and already-absolute paths unchanged
            if src.startswith(
                ("http://", "https://", "data:", "ftp://", "file://", "mailto:")
            ) or os.path.isabs(src):
                return match.group(0)
            abs_path = (file_dir / src).resolve()
            # Use forward slashes so the path is valid in a markdown src attribute
            return f"![{alt}]({abs_path.as_posix()})"

        return self._MD_IMAGE_PATTERN.sub(replace_img, content)

    def _resolve_includes(
        self,
        content: str,
        base_dir: Path,
        allowed_base: Optional[Path] = None,
        visited: Optional[Set[str]] = None,
        depth: int = 0,
    ) -> str:
        """Resolve ![[file.md]] transclusion syntax, recursively.

        Args:
            content: Markdown source text.
            base_dir: Directory used to resolve relative include paths.
            allowed_base: If set, all resolved paths must remain inside this directory tree.
            visited: Set of already-resolved absolute paths (cycle detection).
            depth: Current recursion depth.

        Returns:
            Markdown text with all includes expanded.
        """
        if depth >= self._MAX_INCLUDE_DEPTH:
            return content

        if visited is None:
            visited = set()

        def replace_include(match: re.Match) -> str:
            raw_path = match.group(1).strip()
            resolved = (base_dir / raw_path).resolve()

            # Security: must stay inside the allowed directory tree
            if allowed_base is not None:
                try:
                    resolved.relative_to(allowed_base)
                except ValueError:
                    logger.warning("Include blocked (path traversal): %s", resolved)
                    return f"> ⚠️ Include blocked: `{raw_path}`\n"

            # Only allow markdown file types
            if resolved.suffix.lower() not in self._ALLOWED_INCLUDE_EXTENSIONS:
                return f"> ⚠️ Include ignored (not a markdown file): `{raw_path}`\n"

            if not resolved.exists() or not resolved.is_file():
                return f"> ⚠️ Include not found: `{raw_path}`\n"

            abs_str = str(resolved)
            if abs_str in visited:
                return f"> ⚠️ Circular include skipped: `{raw_path}`\n"

            visited.add(abs_str)
            try:
                included_text = resolved.read_text(encoding="utf-8")
                # Rewrite relative image paths to absolute before inlining so they
                # resolve correctly when rendered in the context of the parent file.
                included_text = self._absolutize_md_image_paths(included_text, resolved.parent)
                included_text = self._resolve_includes(
                    included_text,
                    resolved.parent,
                    allowed_base=allowed_base,
                    visited=visited,
                    depth=depth + 1,
                )
            except OSError as exc:
                logger.warning("Could not read include file %s: %s", resolved, exc)
                return f"> ⚠️ Include unreadable: `{raw_path}`\n"
            finally:
                visited.discard(abs_str)

            return included_text

        return self._INCLUDE_PATTERN.sub(replace_include, content)

    def process(self, content: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Process markdown content to HTML.

        Args:
            content: Markdown content string
            options: Optional dictionary of processing options. Recognised keys:
                base_dir (str): Absolute path used to resolve ![[file.md]] includes.
                allowed_base (str): Root directory that includes may not escape.

        Returns:
            HTML string
        """
        if options is None:
            options = {}

        base_dir_str = options.get("base_dir", "")
        if base_dir_str:
            base_dir = Path(base_dir_str)
            allowed_base_str = options.get("allowed_base", "")
            allowed_base = Path(allowed_base_str) if allowed_base_str else None
            content = self._resolve_includes(content, base_dir, allowed_base=allowed_base)

        # Create markdown instance with extensions
        md = markdown.Markdown(
            extensions=self.extensions,
            extension_configs=self.extension_configs,
            output_format="html5",
        )

        # Process the markdown
        html = md.convert(content)

        # Get CSS for syntax highlighting
        css = self._get_highlight_css()

        # Wrap in a complete HTML document if requested
        if options.get("full_html", False):
            html = self._wrap_html(html, css, options)

        return html

    def _get_highlight_css(self):
        """Get CSS for syntax highlighting."""
        formatter = HtmlFormatter(style="monokai")
        return formatter.get_style_defs(".highlight")

    def _wrap_html(self, content, css, options):
        """Wrap content in a complete HTML document."""
        title = options.get("title", "Markdown Document")

        # pylint: disable=trailing-whitespace,line-too-long
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}

        pre {{
            background-color: #272822;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}

        code {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}

        img {{
            max-width: 100%;
            height: auto;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}

        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}

        blockquote {{
            border-left: 4px solid #ccc;
            margin: 20px 0;
            padding-left: 20px;
            color: #666;
        }}

        {css}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.45/dist/katex.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.45/dist/katex.min.css">
</head>
<body>
    {content}
    <script>
        (async function() {{
            var diagrams = document.querySelectorAll('.mermaid');
            if (!diagrams.length) return;
            function decodeEntities(str) {{
                return str.replace(/&amp;/g, '&').replace(/&lt;/g, '<')
                          .replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
            }}
            mermaid.initialize({{
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose',
                suppressErrors: true
            }});
            for (var i = 0; i < diagrams.length; i++) {{
                var el = diagrams[i];
                var source = decodeEntities((el.textContent || '').trim());
                el.textContent = source;
                try {{
                    var id = 'mermaid-' + Date.now() + '-' + i;
                    var result = await mermaid.render(id, source);
                    el.innerHTML = result.svg;
                }} catch (e) {{
                    var escaped = source.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    el.innerHTML = '<details style="border:1px solid #fca;background:#fff8f5;border-radius:4px;padding:8px">'
                        + '<summary style="cursor:pointer;color:#c60;font-weight:bold">'
                        + '\u26a0 Diagram could not be rendered (click to view source)</summary>'
                        + '<pre style="margin:8px 0 0;overflow:auto;font-size:13px">' + escaped + '</pre></details>';
                    console.warn('Mermaid render failed:', e.message || e);
                }}
            }}
        }})();
    </script>
</body>
</html>"""
