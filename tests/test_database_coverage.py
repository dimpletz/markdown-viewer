"""Additional tests for database.py to improve coverage."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import markdown_viewer.db.database as db_module


def test_close_db_no_connection(db_conn):
    """_close_db() gracefully handles missing connection in g."""
    from markdown_viewer.app import create_app
    from flask import g

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with app.test_request_context("/"):
        # Ensure no connection exists
        g.pop("favourites_db", None)
        db_module._close_db()  # Should not raise


def test_close_db_with_connection(db_conn):
    """_close_db() closes and pops the connection from g."""
    from markdown_viewer.app import create_app
    from flask import g

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with app.test_request_context("/"):
        mock_conn = MagicMock()
        g.favourites_db = mock_conn
        db_module._close_db()

        mock_conn.close.assert_called_once()
        assert "favourites_db" not in g


def test_init_db_with_flask_app(tmp_path, monkeypatch):
    """init_db() registers teardown when flask_app is provided."""
    from markdown_viewer.app import create_app

    test_db = tmp_path / "with_app.db"
    monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)
    db_module.FTS5_ENABLED = False

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})

    # Call init_db with the app object
    db_module.init_db(app)

    # Verify teardown was registered
    assert any("_close_db" in str(fn) for fn in app.teardown_appcontext_funcs)


def test_backfill_content_reads_files(tmp_path, monkeypatch, db_conn):
    """_backfill_content reads file content for favourites with empty content."""
    # Create a test markdown file
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test Content\n\nHello world", encoding="utf-8")

    # Insert a favourite with empty content
    db_conn.execute(
        """INSERT INTO favourites 
           (name, path, filename, tags_text, content, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
        ("Test", str(md_file), "test.md", "", ""),
    )
    db_conn.commit()

    # Run backfill
    db_module._backfill_content(db_conn)

    # Verify content was filled
    row = db_conn.execute(
        "SELECT content FROM favourites WHERE path = ?", (str(md_file),)
    ).fetchone()
    assert row is not None
    assert "Test Content" in row["content"]
    assert "Hello world" in row["content"]


def test_backfill_content_handles_missing_files(tmp_path, db_conn):
    """_backfill_content handles missing files gracefully (content stays empty)."""
    missing_file = tmp_path / "nonexistent.md"

    # Insert a favourite for a nonexistent file
    db_conn.execute(
        """INSERT INTO favourites 
           (name, path, filename, tags_text, content, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
        ("Missing", str(missing_file), "nonexistent.md", "", ""),
    )
    db_conn.commit()

    # Run backfill - should not raise
    db_module._backfill_content(db_conn)

    # Verify content remains empty
    row = db_conn.execute(
        "SELECT content FROM favourites WHERE path = ?", (str(missing_file),)
    ).fetchone()
    assert row["content"] == ""


def test_backfill_content_truncates_large_files(tmp_path, db_conn):
    """_backfill_content truncates files larger than 10MB."""
    large_file = tmp_path / "large.md"
    # Create a file with 11 MB of content
    large_content = "x" * (11 * 1024 * 1024)
    large_file.write_text(large_content, encoding="utf-8")

    # Insert favourite
    db_conn.execute(
        """INSERT INTO favourites 
           (name, path, filename, tags_text, content, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
        ("Large", str(large_file), "large.md", "", ""),
    )
    db_conn.commit()

    # Run backfill
    db_module._backfill_content(db_conn)

    # Verify content was truncated to 10MB
    row = db_conn.execute(
        "SELECT content FROM favourites WHERE path = ?", (str(large_file),)
    ).fetchone()
    assert len(row["content"]) == 10 * 1024 * 1024


def test_backfill_content_skips_when_no_empty_rows(db_conn):
    """_backfill_content exits early when all favourites have content."""
    # Insert a favourite with existing content
    db_conn.execute(
        """INSERT INTO favourites 
           (name, path, filename, tags_text, content, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
        ("Test", "/fake/path.md", "path.md", "", "existing content"),
    )
    db_conn.commit()

    # Run backfill - should exit early
    db_module._backfill_content(db_conn)

    # Verify content unchanged
    row = db_conn.execute("SELECT content FROM favourites").fetchone()
    assert row["content"] == "existing content"


def test_run_migrations_with_fts5(tmp_path, monkeypatch):
    """_run_migrations applies FTS5 migrations when FTS5 is enabled."""
    from markdown_viewer.app import create_app

    test_db = tmp_path / "fts5_migration.db"
    monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)

    # Force FTS5 enabled for this test
    monkeypatch.setattr(db_module, "FTS5_ENABLED", True)

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with app.app_context():
        db_module.init_db()

        # Verify FTS table exists if FTS5 was truly available
        conn = db_module.get_db()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {r["name"] for r in tables}

        # Check if FTS5 migration created the virtual table
        if db_module.FTS5_ENABLED:
            assert "favourites_fts" in table_names
