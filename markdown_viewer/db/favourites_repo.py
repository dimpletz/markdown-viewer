"""
Repository layer for the favourites feature.

All database access for favourites goes through this module.
tags_text is maintained exclusively here — never written directly elsewhere.
"""

import logging
import sqlite3
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import database as _db

logger = logging.getLogger(__name__)

# Maximum bytes of file content to read and index (10 MB)
_MAX_CONTENT_BYTES = 10 * 1024 * 1024


# ---------------------------------------------------------------------------
# FTS query sanitisation (S2 — prevents FTS5 injection)
# ---------------------------------------------------------------------------

# FTS5 boolean operators must not become prefix tokens (e.g. "OR*" is a syntax error).
_FTS_BOOLEAN_KEYWORDS = frozenset({"or", "and", "not"})


def _sanitize_fts_query(q: str) -> str:
    """Strip FTS5 special characters and build a prefix-search expression.

    Replaces every non-word, non-space character with a space so that FTS5
    operators (AND, OR, NOT), SQL injection fragments (1=1, --, ;), and other
    special chars cannot appear in the generated query.
    FTS5 boolean keywords are also dropped to avoid prefix-search syntax errors.
    Example: 'hello world' → 'hello* world*'
    Example: 'a OR b AND NOT c' → 'a* b* c*'
    Example: "'' OR 1=1 --" → '1*'
    """
    cleaned = re.sub(r"[^\w\s]", " ", q).strip()
    if not cleaned:
        return ""
    tokens = [t + "*" for t in cleaned.split() if t and t.lower() not in _FTS_BOOLEAN_KEYWORDS]
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    # tags_text is a comma-separated string; expose as list for convenience
    raw = d.get("tags_text") or ""
    d["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
    return d


# ---------------------------------------------------------------------------
# Public repository API
# ---------------------------------------------------------------------------


def list_all() -> List[Dict[str, Any]]:
    """Return all favourites ordered by updated_at descending."""
    conn = _db.get_db()
    rows = conn.execute(
        "SELECT id, name, path, filename, tags_text, created_at, updated_at "
        "FROM favourites ORDER BY updated_at DESC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def search(q: str) -> List[Dict[str, Any]]:
    """Search favourites by query string; returns at most 20 results.

    Uses FTS5 MATCH when available, falls back to four LIKE clauses.
    """
    conn = _db.get_db()

    if _db.FTS5_ENABLED:
        fts_q = _sanitize_fts_query(q)
        if not fts_q:
            return []
        rows = conn.execute(
            "SELECT f.id, f.name, f.path, f.filename, f.tags_text, "
            "       f.created_at, f.updated_at "
            "FROM favourites f "
            "JOIN favourites_fts ON favourites_fts.rowid = f.id "
            "WHERE favourites_fts MATCH ? "
            "ORDER BY rank "
            "LIMIT 20",
            (fts_q,),
        ).fetchall()
    else:
        like = f"%{q}%"
        rows = conn.execute(
            "SELECT id, name, path, filename, tags_text, created_at, updated_at "
            "FROM favourites "
            "WHERE name LIKE ? OR filename LIKE ? OR path LIKE ? OR tags_text LIKE ? OR content LIKE ? "
            "LIMIT 20",
            (like, like, like, like, like),
        ).fetchall()

    return [_row_to_dict(r) for r in rows]


def check_by_path(file_path: str) -> Dict[str, Any]:
    """Return {is_favourite: bool, id: int|None} for the given path."""
    conn = _db.get_db()
    row = conn.execute("SELECT id FROM favourites WHERE path = ?", (file_path,)).fetchone()
    if row:
        return {"is_favourite": True, "id": row["id"]}
    return {"is_favourite": False, "id": None}


def add(file_path: str) -> Dict[str, Any]:
    """Insert a new favourite for *file_path*.

    Validates that the file exists on the local filesystem before inserting.
    Raises ValueError for missing files and sqlite3.IntegrityError for
    duplicates (UNIQUE constraint on path).
    """
    p = Path(file_path)
    original_path = file_path

    # If path doesn't exist, try multiple resolution strategies
    if not p.exists():
        resolved = False

        # Strategy 1: Try as absolute path
        if p.is_absolute():
            pass  # Already tried, doesn't exist
        else:
            # Strategy 2: Try resolving relative to current directory
            try:
                abs_path = p.resolve()
                if abs_path.exists():
                    p = abs_path
                    file_path = str(abs_path)
                    resolved = True
            except (OSError, RuntimeError):
                pass

            # Strategy 3: Try in examples/ folder (common for browser-opened files)
            if not resolved:
                # Get the script directory (markdown_viewer package location)
                script_dir = Path(__file__).parent.parent
                examples_path = script_dir / "examples" / Path(file_path).name
                if examples_path.exists():
                    p = examples_path
                    file_path = str(examples_path)
                    resolved = True

            # Strategy 4: Try in examples/ from current working directory
            if not resolved:
                examples_path = Path.cwd() / "examples" / Path(file_path).name
                if examples_path.exists():
                    p = examples_path
                    file_path = str(examples_path)
                    resolved = True

        # If still not found, raise error
        if not p.exists():
            raise ValueError(
                f"File does not exist: {original_path}. "
                f"To favourite files, open them via URL parameter (e.g., ?file=examples/filename.md) "
                f"or use the CLI with a full path (e.g., mdview path/to/file.md)"
            )

    name = p.stem
    filename = p.name
    now = _now_iso()

    # Read file content for full-text indexing; cap at _MAX_CONTENT_BYTES
    try:
        raw = p.read_bytes()
        if len(raw) > _MAX_CONTENT_BYTES:
            raw = raw[:_MAX_CONTENT_BYTES]
        content = raw.decode("utf-8", errors="replace")
    except OSError:
        content = ""

    conn = _db.get_db()
    cursor = conn.execute(
        "INSERT INTO favourites (name, path, filename, content, tags_text, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, '', ?, ?)",
        (name, file_path, filename, content, now, now),
    )
    conn.commit()
    row_id = cursor.lastrowid
    row = conn.execute(
        "SELECT id, name, path, filename, tags_text, created_at, updated_at "
        "FROM favourites WHERE id = ?",
        (row_id,),
    ).fetchone()
    return _row_to_dict(row)


def update(favourite_id: int, name: Optional[str], tags: Optional[List[str]]) -> Dict[str, Any]:
    """Update name and/or tags for the given favourite.

    Wrapped in an explicit transaction. Orphan tags are cleaned up after
    updating the junction table.

    Raises ValueError if the favourite is not found.
    """
    conn = _db.get_db()

    row = conn.execute(
        "SELECT id, name, path, filename, tags_text, created_at, updated_at "
        "FROM favourites WHERE id = ?",
        (favourite_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"Favourite {favourite_id} not found")

    new_name = name if name is not None else row["name"]
    now = _now_iso()

    try:
        conn.execute("BEGIN")

        conn.execute(
            "UPDATE favourites SET name = ?, updated_at = ? WHERE id = ?",
            (new_name, now, favourite_id),
        )

        if tags is not None:
            # Remove all existing tag associations for this favourite
            conn.execute("DELETE FROM favourite_tags WHERE favourite_id = ?", (favourite_id,))

            tag_names = [t.strip() for t in tags if t.strip()]
            for tag_name in tag_names:
                # Upsert tag
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                tag_row = conn.execute(
                    "SELECT id FROM tags WHERE name = ? COLLATE NOCASE", (tag_name,)
                ).fetchone()
                conn.execute(
                    "INSERT OR IGNORE INTO favourite_tags (favourite_id, tag_id) VALUES (?, ?)",
                    (favourite_id, tag_row["id"]),
                )

            # Rebuild denormalized tags_text
            tags_text = ",".join(tag_names)
            conn.execute(
                "UPDATE favourites SET tags_text = ? WHERE id = ?",
                (tags_text, favourite_id),
            )

            # Clean orphan tags (tags with no favourite_tags references)
            conn.execute(
                "DELETE FROM tags WHERE id NOT IN " "(SELECT DISTINCT tag_id FROM favourite_tags)"
            )

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    updated = conn.execute(
        "SELECT id, name, path, filename, tags_text, created_at, updated_at "
        "FROM favourites WHERE id = ?",
        (favourite_id,),
    ).fetchone()
    return _row_to_dict(updated)


def delete(favourite_id: int) -> bool:
    """Delete a favourite and return True, or False if not found.

    The ON DELETE CASCADE on favourite_tags removes the junction rows
    automatically. Orphan tags are cleaned up afterwards.
    """
    conn = _db.get_db()
    cursor = conn.execute("DELETE FROM favourites WHERE id = ?", (favourite_id,))
    if cursor.rowcount == 0:
        return False

    # Clean orphan tags
    conn.execute("DELETE FROM tags WHERE id NOT IN " "(SELECT DISTINCT tag_id FROM favourite_tags)")
    conn.commit()
    return True
