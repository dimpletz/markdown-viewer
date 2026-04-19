"""
SQLite database bootstrapping and connection management for favourites.

Connection lifecycle: one connection per Flask request stored in Flask g.
WAL mode + synchronous=NORMAL for performance; foreign_keys=ON for integrity.
Schema migrations tracked in schema_version table.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

from flask import g, current_app

logger = logging.getLogger(__name__)

# Module-level flag set once during init_db()
FTS5_ENABLED: bool = False


def get_db_path() -> Path:
    """Return the path to the favourites database.

    Uses ~/.markdown-viewer/favourites.db so it works regardless of how the
    package is installed (pip, pipx, editable, Electron bundle, etc.).
    """
    db_dir = Path.home() / ".markdown-viewer"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "favourites.db"


def get_db() -> sqlite3.Connection:
    """Return the per-request SQLite connection, creating it on first access.

    The connection is stored in Flask g and closed automatically at the end
    of each request via the teardown registered by init_db().
    """
    if "favourites_db" not in g:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        g.favourites_db = conn
    return g.favourites_db


def _close_db(error: Optional[Exception] = None) -> None:  # pylint: disable=unused-argument
    """Close the per-request database connection."""
    conn: Optional[sqlite3.Connection] = g.pop("favourites_db", None)
    if conn is not None:
        conn.close()


# ---------------------------------------------------------------------------
# FTS5 probe
# ---------------------------------------------------------------------------


def _fts5_available(conn: sqlite3.Connection) -> bool:
    """Return True if the linked SQLite was compiled with FTS5 support."""
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe " "USING fts5(x)")
        conn.execute("DROP TABLE IF EXISTS _fts5_probe")
        conn.commit()
        return True
    except sqlite3.OperationalError:
        return False


# ---------------------------------------------------------------------------
# Schema migrations
# ---------------------------------------------------------------------------


def _migration_0(conn: sqlite3.Connection) -> None:
    """Baseline schema: favourites, tags, junction table, all indexes."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS favourites (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            path        TEXT    NOT NULL UNIQUE,
            filename    TEXT    NOT NULL,
            tags_text   TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_favourites_path       ON favourites(path);
        CREATE INDEX IF NOT EXISTS idx_favourites_name       ON favourites(name);
        CREATE INDEX IF NOT EXISTS idx_favourites_filename   ON favourites(filename);
        CREATE INDEX IF NOT EXISTS idx_favourites_updated_at ON favourites(updated_at);

        CREATE TABLE IF NOT EXISTS tags (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE COLLATE NOCASE
        );

        CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

        CREATE TABLE IF NOT EXISTS favourite_tags (
            favourite_id INTEGER NOT NULL REFERENCES favourites(id) ON DELETE CASCADE,
            tag_id       INTEGER NOT NULL REFERENCES tags(id),
            PRIMARY KEY (favourite_id, tag_id)
        );

        CREATE INDEX IF NOT EXISTS idx_fav_tags_favourite_id ON favourite_tags(favourite_id);
        CREATE INDEX IF NOT EXISTS idx_fav_tags_tag_id       ON favourite_tags(tag_id);
        """)


def _migration_1(conn: sqlite3.Connection) -> None:
    """Add content column to favourites for full-text search of file contents."""
    conn.executescript("""
        ALTER TABLE favourites ADD COLUMN content TEXT NOT NULL DEFAULT '';
        """)


def _migration_0_fts(conn: sqlite3.Connection) -> None:
    """FTS5 virtual table + AI/AU/AD triggers including content column."""
    conn.executescript("""
        CREATE VIRTUAL TABLE IF NOT EXISTS favourites_fts
        USING fts5(
            name,
            filename,
            path,
            tags_text,
            content,
            content='favourites',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        );

        -- After Insert: add new row to FTS index
        CREATE TRIGGER IF NOT EXISTS fav_fts_ai
        AFTER INSERT ON favourites BEGIN
            INSERT INTO favourites_fts(rowid, name, filename, path, tags_text, content)
            VALUES (new.id, new.name, new.filename, new.path, new.tags_text, new.content);
        END;

        -- After Update: refresh FTS index
        CREATE TRIGGER IF NOT EXISTS fav_fts_au
        AFTER UPDATE ON favourites BEGIN
            INSERT INTO favourites_fts(favourites_fts, rowid, name, filename, path, tags_text, content)
            VALUES ('delete', old.id, old.name, old.filename, old.path, old.tags_text, old.content);
            INSERT INTO favourites_fts(rowid, name, filename, path, tags_text, content)
            VALUES (new.id, new.name, new.filename, new.path, new.tags_text, new.content);
        END;

        -- After Delete: remove from FTS index
        CREATE TRIGGER IF NOT EXISTS fav_fts_ad
        AFTER DELETE ON favourites BEGIN
            INSERT INTO favourites_fts(favourites_fts, rowid, name, filename, path, tags_text, content)
            VALUES ('delete', old.id, old.name, old.filename, old.path, old.tags_text, old.content);
        END;
        """)


def _migration_1_fts(conn: sqlite3.Connection) -> None:
    """Rebuild FTS5 index to include the content column (upgrade for existing DBs)."""
    conn.executescript("""
        -- Drop old triggers and table before recreating with content column
        DROP TRIGGER IF EXISTS fav_fts_ai;
        DROP TRIGGER IF EXISTS fav_fts_au;
        DROP TRIGGER IF EXISTS fav_fts_ad;
        DROP TABLE IF EXISTS favourites_fts;

        CREATE VIRTUAL TABLE IF NOT EXISTS favourites_fts
        USING fts5(
            name,
            filename,
            path,
            tags_text,
            content,
            content='favourites',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        );

        -- Repopulate index from existing rows
        INSERT INTO favourites_fts(rowid, name, filename, path, tags_text, content)
        SELECT id, name, filename, path, tags_text, content FROM favourites;

        CREATE TRIGGER IF NOT EXISTS fav_fts_ai
        AFTER INSERT ON favourites BEGIN
            INSERT INTO favourites_fts(rowid, name, filename, path, tags_text, content)
            VALUES (new.id, new.name, new.filename, new.path, new.tags_text, new.content);
        END;

        CREATE TRIGGER IF NOT EXISTS fav_fts_au
        AFTER UPDATE ON favourites BEGIN
            INSERT INTO favourites_fts(favourites_fts, rowid, name, filename, path, tags_text, content)
            VALUES ('delete', old.id, old.name, old.filename, old.path, old.tags_text, old.content);
            INSERT INTO favourites_fts(rowid, name, filename, path, tags_text, content)
            VALUES (new.id, new.name, new.filename, new.path, new.tags_text, new.content);
        END;

        CREATE TRIGGER IF NOT EXISTS fav_fts_ad
        AFTER DELETE ON favourites BEGIN
            INSERT INTO favourites_fts(favourites_fts, rowid, name, filename, path, tags_text, content)
            VALUES ('delete', old.id, old.name, old.filename, old.path, old.tags_text, old.content);
        END;
        """)


# Ordered list of (schema_version_number, migration_function) tuples.
# Append new entries here when the schema changes; never edit existing ones.
_MIGRATIONS = [
    (0, _migration_0),
    (1, _migration_1),
]

# FTS migrations: each tracked by a dedicated row in schema_version.
# When migration 100 is applied fresh it already includes content, so 101 is
# immediately marked done. Existing DBs that already have 100 get 101 applied.
_FTS_MIGRATION_100 = 100
_FTS_MIGRATION_101 = 101


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Apply pending migrations sequentially using schema_version table."""
    # Bootstrap: schema_version doesn't exist on a brand-new database
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if exists:
        row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        current_version = row["version"] if row else -1
    else:
        current_version = -1

    for version, migration_fn in _MIGRATIONS:
        if version > current_version:
            migration_fn(conn)
            if current_version == -1:
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            else:
                conn.execute("UPDATE schema_version SET version = ?", (version,))
            conn.commit()
            current_version = version
            logger.info("Applied DB migration %d", version)

    # FTS migrations: tracked via dedicated sentinel rows in schema_version.
    # Migration 100 is the baseline (now includes content column).
    # Migration 101 rebuilds the index for existing DBs that had 100 without content.
    if FTS5_ENABLED:
        has_100 = conn.execute(
            "SELECT version FROM schema_version WHERE version = ?", (_FTS_MIGRATION_100,)
        ).fetchone()
        has_101 = conn.execute(
            "SELECT version FROM schema_version WHERE version = ?", (_FTS_MIGRATION_101,)
        ).fetchone()

        if not has_100:
            # Fresh FTS install: baseline already includes content, mark both done
            _migration_0_fts(conn)
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (_FTS_MIGRATION_100,))
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (_FTS_MIGRATION_101,))
            conn.commit()
            logger.info("Applied FTS5 migration 100 (with content index)")
        elif not has_101:
            # Existing DB: rebuild FTS to add content column
            _migration_1_fts(conn)
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (_FTS_MIGRATION_101,))
            conn.commit()
            logger.info("Applied FTS5 migration 101 (content added to index)")


# ---------------------------------------------------------------------------
# Content backfill
# ---------------------------------------------------------------------------


def _backfill_content(conn: sqlite3.Connection) -> None:
    """Read and store file content for any favourites where content is empty.

    Runs on every startup (cheap: only touches rows with content='').  The
    fav_fts_au trigger fires for each UPDATE so the FTS index is kept in sync.
    """
    rows = conn.execute("SELECT id, path FROM favourites WHERE content = ''").fetchall()
    if not rows:
        return

    _MAX = 10 * 1024 * 1024  # 10 MB cap
    updated = 0
    for row in rows:
        try:
            p = Path(row["path"])
            raw = p.read_bytes()
            if len(raw) > _MAX:
                raw = raw[:_MAX]
            content = raw.decode("utf-8", errors="replace")
            conn.execute(
                "UPDATE favourites SET content = ? WHERE id = ?",
                (content, row["id"]),
            )
            updated += 1
        except OSError:
            pass  # File missing or unreadable — leave content empty

    if updated:
        conn.commit()
        logger.info("Backfilled content for %d favourite(s)", updated)


# ---------------------------------------------------------------------------
# Public bootstrap entry point
# ---------------------------------------------------------------------------


def init_db(flask_app=None) -> None:
    """Bootstrap the database and register Flask teardown.

    Called once from create_app() (pass the app object) or manually
    inside an active app context (omit the app argument).  Opens a
    temporary connection to run migrations, then registers _close_db
    for per-request cleanup.
    """
    global FTS5_ENABLED  # pylint: disable=global-statement

    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    FTS5_ENABLED = _fts5_available(conn)
    if FTS5_ENABLED:
        logger.info("FTS5 enabled for favourites search")
    else:
        logger.warning("FTS5 not available; favourites search will use LIKE fallback")

    _run_migrations(conn)
    _backfill_content(conn)
    conn.close()

    # Register per-request teardown
    if flask_app is not None:
        flask_app.teardown_appcontext(_close_db)
    else:
        current_app.teardown_appcontext(_close_db)
