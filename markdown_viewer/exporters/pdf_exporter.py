"""
PDF exporter using playwright for high-quality PDF generation.
"""

# pylint: disable=broad-exception-caught,duplicate-code

import os
import tempfile
import logging
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# Constants
RENDER_WAIT_MS = 1000  # Wait for diagrams to render


class PDFExporter:
    """Export HTML content to PDF."""

    def __init__(self):
        """Initialize PDF exporter."""
        self.playwright = None
        self.browser = None

    def _ensure_browser(self) -> None:
        """Ensure browser is initialized."""
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch()
            logger.info("Playwright browser launched")

    def export(
        self, html_content: str, output_path: str, options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Export HTML content to PDF.

        Args:
            html_content: HTML string to export
            output_path: Path to save PDF file
            options: Optional dictionary of PDF options
        """
        if options is None:
            options = {}

        self._ensure_browser()

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            # Wrap content if it's not a complete HTML document
            if not html_content.strip().startswith("<!DOCTYPE"):
                html_content = self._wrap_html(html_content)

            f.write(html_content)
            temp_html = f.name

        # Create new context for isolation
        context = self.browser.new_context()
        try:
            # Create a new page in the context
            page = context.new_page()

            # Navigate to the HTML file
            page.goto(f"file://{temp_html}")

            # Wait for content to render (especially important for diagrams)
            page.wait_for_timeout(RENDER_WAIT_MS)

            # PDF options
            pdf_options = {
                "path": output_path,
                "format": options.get("format", "A4"),
                "print_background": True,
                "margin": options.get(
                    "margin", {"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"}
                ),
            }

            # Generate PDF
            page.pdf(**pdf_options)

            page.close()
        finally:
            context.close()
            # Clean up temporary file
            if os.path.exists(temp_html):
                try:
                    os.unlink(temp_html)
                except OSError as e:
                    logger.warning("Failed to delete temp HTML file: %s", e)

    def _wrap_html(self, content):
        """Wrap content in a complete HTML document for PDF generation."""
        # pylint: disable=line-too-long
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Document</title>
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
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
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
        .mermaid {{
            text-align: center;
            margin: 20px 0;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.45/dist/katex.min.css">
</head>
<body>
    {content}
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>"""

    def close(self) -> None:
        """Explicitly close browser and playwright."""
        if self.browser:
            try:
                self.browser.close()
                logger.info("Browser closed")
            except Exception as e:
                # Event loop closed errors are expected during cleanup, ignore them
                if "Event loop is closed" not in str(e):
                    logger.warning("Error closing browser: %s", e)
            finally:
                self.browser = None

        if self.playwright:
            try:
                self.playwright.stop()
                logger.info("Playwright stopped")
            except Exception as e:
                # Event loop closed errors are expected during cleanup, ignore them
                if "Event loop is closed" not in str(e):
                    logger.warning("Error stopping playwright: %s", e)
            finally:
                self.playwright = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
        return False

    def __del__(self):
        """Clean up resources on deletion."""
        # Note: __del__ is unreliable, prefer explicit close() or context manager
        self.close()
