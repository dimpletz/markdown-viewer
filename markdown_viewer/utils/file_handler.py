"""
File handler for reading and managing markdown files.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chardet

logger = logging.getLogger(__name__)

# Constants
MAX_DETECTION_BYTES = 10000  # Limit bytes read for encoding detection
MIN_CONFIDENCE = 0.7  # Minimum confidence for encoding detection


class FileHandler:
    """Handle file operations for markdown files."""

    def __init__(self):
        """Initialize file handler."""
        self.supported_extensions = [".md", ".markdown", ".mdown", ".mkd", ".mkdn"]

    def read_file(self, file_path: str) -> str:
        """
        Read a markdown file with automatic encoding detection.

        Args:
            file_path: Path to the markdown file

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a markdown file
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.is_markdown_file(file_path):
            raise ValueError(f"Not a markdown file: {file_path}")

        # Always try UTF-8 first — it's the overwhelmingly common encoding for
        # markdown files, and chardet frequently misidentifies UTF-8 files that
        # contain emojis or other multibyte characters as Latin-1/Windows-1252.
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            pass

        # UTF-8 failed: detect encoding from raw bytes and retry
        with open(file_path, "rb") as f:
            raw_data = f.read(MAX_DETECTION_BYTES)
        result = chardet.detect(raw_data)

        if result["confidence"] >= MIN_CONFIDENCE and result["encoding"]:
            encoding = result["encoding"]
            logger.debug("Detected encoding %s with confidence %s", encoding, result["confidence"])
        else:
            encoding = "utf-8"
            logger.debug("Low confidence (%s), using UTF-8", result["confidence"])

        try:
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                return f.read()
        except (UnicodeDecodeError, LookupError) as e:
            logger.warning("Failed to read with %s, falling back to UTF-8: %s", encoding, e)
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()

    def is_markdown_file(self, file_path: Path) -> bool:
        """Check if file is a markdown file."""
        return Path(file_path).suffix.lower() in self.supported_extensions

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file."""
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        stat = file_path.stat()

        return {
            "name": file_path.name,
            "path": str(file_path.absolute()),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_markdown": self.is_markdown_file(file_path),
        }

    def list_markdown_files(self, directory: str, recursive: bool = False) -> List[str]:
        """
        List all markdown files in a directory.

        Args:
            directory: Directory path
            recursive: Whether to search recursively

        Returns:
            List of markdown file paths

        Raises:
            ValueError: If path is not a directory
        """
        directory = Path(directory)

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        markdown_files = []

        if recursive:
            for ext in self.supported_extensions:
                markdown_files.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in self.supported_extensions:
                markdown_files.extend(directory.glob(f"*{ext}"))

        return [str(f.absolute()) for f in markdown_files]
