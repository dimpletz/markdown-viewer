"""Tests for markdown_viewer.db.favourites_repo."""

import sqlite3

import pytest

import markdown_viewer.db.database as db_module
from markdown_viewer.db import favourites_repo as repo
from markdown_viewer.app import create_app


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    """App context with isolated DB, yields (app, db_conn)."""
    test_db = tmp_path / "repo_test.db"
    monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)
    db_module.FTS5_ENABLED = False

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with app.app_context():
        db_module.init_db()
        yield app, db_module.get_db()


def test_add_happy_path(ctx, tmp_path):
    """add() inserts a favourite and returns the new row."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Hello")

    item = repo.add(str(md_file))
    assert item["path"] == str(md_file)
    assert item["filename"] == "test.md"
    assert item["name"] == "test"
    assert item["tags"] == []


def test_add_nonexistent_file_raises(ctx, tmp_path):
    """add() raises ValueError when file does not exist."""
    with pytest.raises(ValueError, match="does not exist"):
        repo.add(str(tmp_path / "ghost.md"))


def test_add_duplicate_raises(ctx, tmp_path):
    """add() raises IntegrityError on duplicate path."""
    md_file = tmp_path / "dup.md"
    md_file.write_text("# Dup")
    repo.add(str(md_file))

    with pytest.raises(sqlite3.IntegrityError):
        repo.add(str(md_file))


def test_list_all_empty(ctx):
    """list_all() returns empty list when no favourites."""
    assert repo.list_all() == []


def test_list_all_returns_added(ctx, tmp_path):
    """list_all() returns rows in updated_at descending order."""
    f1 = tmp_path / "a.md"
    f1.write_text("A")
    f2 = tmp_path / "b.md"
    f2.write_text("B")

    repo.add(str(f1))
    repo.add(str(f2))

    items = repo.list_all()
    assert len(items) == 2
    # Most recent first
    assert items[0]["filename"] == "b.md"


def test_check_by_path_not_favourite(ctx):
    """check_by_path returns is_favourite=False for unknown path."""
    result = repo.check_by_path("/nonexistent/file.md")
    assert result["is_favourite"] is False
    assert result["id"] is None


def test_check_by_path_favourite(ctx, tmp_path):
    """check_by_path returns is_favourite=True after adding."""
    md_file = tmp_path / "c.md"
    md_file.write_text("C")
    added = repo.add(str(md_file))

    result = repo.check_by_path(str(md_file))
    assert result["is_favourite"] is True
    assert result["id"] == added["id"]


def test_update_name(ctx, tmp_path):
    """update() changes the name."""
    md_file = tmp_path / "d.md"
    md_file.write_text("D")
    item = repo.add(str(md_file))

    updated = repo.update(item["id"], name="Custom Name", tags=None)
    assert updated["name"] == "Custom Name"


def test_update_tags(ctx, tmp_path):
    """update() sets tags and rebuilds tags_text."""
    md_file = tmp_path / "e.md"
    md_file.write_text("E")
    item = repo.add(str(md_file))

    updated = repo.update(item["id"], name=None, tags=["python", "docs"])
    assert set(updated["tags"]) == {"python", "docs"}
    assert "python" in updated["tags_text"]
    assert "docs" in updated["tags_text"]


def test_update_orphan_tag_cleanup(ctx, tmp_path):
    """Tags no longer referenced by any favourite are deleted."""
    md_file = tmp_path / "f.md"
    md_file.write_text("F")
    item = repo.add(str(md_file))

    repo.update(item["id"], name=None, tags=["orphan"])
    repo.update(item["id"], name=None, tags=[])

    conn = db_module.get_db()
    orphan = conn.execute("SELECT id FROM tags WHERE name = 'orphan'").fetchone()
    assert orphan is None


def test_update_not_found_raises(ctx):
    """update() raises ValueError for unknown id."""
    with pytest.raises(ValueError, match="not found"):
        repo.update(9999, name="X", tags=None)


def test_delete_happy_path(ctx, tmp_path):
    """delete() removes the favourite and returns True."""
    md_file = tmp_path / "g.md"
    md_file.write_text("G")
    item = repo.add(str(md_file))

    result = repo.delete(item["id"])
    assert result is True
    assert repo.list_all() == []


def test_delete_not_found(ctx):
    """delete() returns False for unknown id."""
    assert repo.delete(9999) is False


def test_delete_cleans_orphan_tags(ctx, tmp_path):
    """delete() removes orphan tags."""
    md_file = tmp_path / "h.md"
    md_file.write_text("H")
    item = repo.add(str(md_file))
    repo.update(item["id"], name=None, tags=["tag1"])

    repo.delete(item["id"])

    conn = db_module.get_db()
    orphan = conn.execute("SELECT id FROM tags WHERE name = 'tag1'").fetchone()
    assert orphan is None


def test_search_like_fallback(ctx, tmp_path):
    """search() returns results via LIKE when FTS5 is disabled."""
    md_file = tmp_path / "search_me.md"
    md_file.write_text("Search")
    repo.add(str(md_file))

    results = repo.search("search_me")
    assert len(results) >= 1
    assert results[0]["filename"] == "search_me.md"


def test_search_empty_query(ctx, tmp_path):
    """search() with empty / whitespace query returns empty list."""
    md_file = tmp_path / "z.md"
    md_file.write_text("Z")
    repo.add(str(md_file))

    results = repo.search("   ")
    assert results == []
