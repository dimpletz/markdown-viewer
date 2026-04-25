"""Tests for markdown_viewer.db.database — schema, migrations, FTS5 probe, WAL."""

import markdown_viewer.db.database as db_module


def test_schema_tables_created(db_conn):
    """All expected tables and views exist after init_db."""
    rows = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    names = {r["name"] for r in rows}
    assert "favourites" in names
    assert "tags" in names
    assert "favourite_tags" in names
    assert "schema_version" in names


def test_schema_version_row_exists(db_conn):
    """schema_version table has at least one row after migration."""
    rows = db_conn.execute("SELECT version FROM schema_version").fetchall()
    assert len(rows) >= 1
    assert all(r["version"] >= 0 for r in rows)


def test_indexes_exist(db_conn):
    """All expected indexes are present."""
    rows = db_conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    index_names = {r["name"] for r in rows}

    expected = {
        "idx_favourites_path",
        "idx_favourites_name",
        "idx_favourites_filename",
        "idx_favourites_updated_at",
        "idx_tags_name",
        "idx_fav_tags_favourite_id",
        "idx_fav_tags_tag_id",
    }
    assert expected.issubset(index_names)


def test_wal_mode(db_conn):
    """Journal mode is WAL."""
    row = db_conn.execute("PRAGMA journal_mode").fetchone()
    assert row[0] == "wal"


def test_foreign_keys_on(db_conn):
    """Foreign keys are enforced."""
    row = db_conn.execute("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1


def test_migration_idempotent(db_conn, monkeypatch, tmp_path):
    """Running init_db twice on the same DB does not raise errors."""
    from markdown_viewer.app import create_app

    test_db = tmp_path / "idempotent.db"
    monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)
    db_module.FTS5_ENABLED = False

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with app.app_context():
        db_module.init_db()
        db_module.init_db()  # second call — must not raise


def test_fts5_probe_returns_bool(db_conn):
    """_fts5_available returns a bool (True or False, not an exception)."""
    result = db_module._fts5_available(db_conn)
    assert isinstance(result, bool)
