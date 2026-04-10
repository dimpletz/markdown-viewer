"""
Word document exporter using python-docx.
"""

# pylint: disable=broad-exception-caught

import logging
from typing import Optional, Dict, Any

from docx import Document
from docx.shared import Pt, Inches
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WordExporter:  # pylint: disable=too-few-public-methods
    """Export content to Word document."""

    def __init__(self):
        """Initialize Word exporter."""

    def export(
        self,
        html_content: str,
        markdown_content: str,  # pylint: disable=unused-argument
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Export content to Word document.

        Args:
            html_content: HTML string (for parsing structure)
            markdown_content: Original markdown content
            output_path: Path to save Word document
            options: Optional dictionary of export options
        """
        if options is None:
            options = {}

        # Create a new Document
        doc = Document()

        # Parse HTML to extract structure
        soup = BeautifulSoup(html_content, "html.parser")

        # Process content
        self._process_element(doc, soup, is_root=True)

        # Save the document
        doc.save(output_path)

    def _process_element(self, doc, element, is_root=False):  # pylint: disable=too-many-branches
        """
        Recursively process HTML element tree and add to Word document.

        Args:
            doc: python-docx Document object
            element: BeautifulSoup element to process
            is_root: True if processing root container (processes children only)

        Handles: headings, paragraphs, lists, code blocks, tables, images.
        """
        if is_root:
            # Process all children
            for child in element.children:
                if hasattr(child, "name"):
                    self._process_element(doc, child)
            return

        if element.name == "h1":
            p = doc.add_heading(element.get_text(), level=1)
        elif element.name == "h2":
            p = doc.add_heading(element.get_text(), level=2)
        elif element.name == "h3":
            p = doc.add_heading(element.get_text(), level=3)
        elif element.name == "h4":
            p = doc.add_heading(element.get_text(), level=4)
        elif element.name == "p":
            text = element.get_text()
            if text.strip():
                p = doc.add_paragraph(text)
        elif element.name == "ul":
            for li in element.find_all("li", recursive=False):
                doc.add_paragraph(li.get_text(), style="List Bullet")
        elif element.name == "ol":
            for li in element.find_all("li", recursive=False):
                doc.add_paragraph(li.get_text(), style="List Number")
        elif element.name == "pre":
            code_text = element.get_text()
            p = doc.add_paragraph(code_text)
            p.style = "No Spacing"
            # Set monospace font
            for run in p.runs:
                run.font.name = "Courier New"
                run.font.size = Pt(10)
        elif element.name == "blockquote":
            text = element.get_text()
            p = doc.add_paragraph(text)
            p.style = "Quote"
        elif element.name == "table":
            self._process_table(doc, element)
        elif element.name == "img":
            # Try to add image if local file
            src = element.get("src", "")
            if src and not src.startswith("http"):
                try:
                    doc.add_picture(src, width=Inches(6))
                except (FileNotFoundError, IOError) as e:
                    logger.warning("Could not load image %s: %s", src, e)
                    doc.add_paragraph(f"[Image: {src}]")
                except Exception as e:
                    logger.error("Unexpected error loading image %s: %s", src, e)
                    doc.add_paragraph(f"[Image: {src}]")
        else:
            # Process children for other elements (div, article, etc.)
            if hasattr(element, "children"):
                for child in element.children:
                    if hasattr(child, "name") and child.name:
                        self._process_element(doc, child)

    def _process_table(self, doc, table_element):
        """Process HTML table and add to document."""
        rows = table_element.find_all("tr")
        if not rows:
            return

        # Count columns
        max_cols = max(len(row.find_all(["th", "td"])) for row in rows)

        # Create table
        table = doc.add_table(rows=len(rows), cols=max_cols)
        table.style = "Light Grid Accent 1"

        # Fill table
        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            for j, cell in enumerate(cells):
                table.rows[i].cells[j].text = cell.get_text().strip()

                # Bold header cells
                if cell.name == "th":
                    for paragraph in table.rows[i].cells[j].paragraphs:
                        for run in paragraph.runs:
                            run.font.bold = True
