"""Integration: favourites full CRUD + search workflow.

Exercises the full stack — route → repo → SQLite — using real database
operations against a temp file; no mocking of persistence layer.
"""

# pylint: disable=redefined-outer-name,import-outside-toplevel

import pytest

# ---------------------------------------------------------------------------
# Fixture — full app + isolated DB (reuses conftest.app_client pattern)
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Flask test client with an isolated SQLite favourites DB."""
    test_db = tmp_path / "fav_integration.db"

    import markdown_viewer.db.database as db_module

    monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)
    db_module.FTS5_ENABLED = False

    from markdown_viewer.app import create_app

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "WTF_CSRF_ENABLED": False,
            "ALLOWED_DOCUMENTS_DIR": str(tmp_path),
        }
    )
    with app.app_context():
        db_module.init_db()

    return app.test_client()


@pytest.fixture()
def md_file(tmp_path):
    """A real markdown file inside the allowed root."""
    p = tmp_path / "notes.md"
    p.write_text("# Notes\n\nHello!", encoding="utf-8")
    return p


@pytest.fixture()
def md_file2(tmp_path):
    """A second markdown file."""
    p = tmp_path / "todo.md"
    p.write_text("# Todo\n\n- item 1", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# CRUD workflow
# ---------------------------------------------------------------------------


class TestFavouritesCrudWorkflow:
    def test_list_empty_on_fresh_db(self, client):
        resp = client.get("/api/favourites")
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []

    def test_add_favourite(self, client, md_file):
        resp = client.post("/api/favourites", json={"path": str(md_file)})
        assert resp.status_code == 201
        data = resp.get_json()
        assert "data" in data
        assert data["data"]["path"] == str(md_file)

    def test_add_then_list(self, client, md_file):
        client.post("/api/favourites", json={"path": str(md_file)})
        resp = client.get("/api/favourites")
        assert resp.status_code == 200
        items = resp.get_json()["data"]
        assert len(items) == 1
        assert items[0]["path"] == str(md_file)

    def test_add_duplicate_returns_409(self, client, md_file):
        client.post("/api/favourites", json={"path": str(md_file)})
        resp = client.post("/api/favourites", json={"path": str(md_file)})
        assert resp.status_code == 409

    def test_check_is_favourite_after_add(self, client, md_file):
        client.post("/api/favourites", json={"path": str(md_file)})
        resp = client.get(f"/api/favourites/check?path={md_file}")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["is_favourite"] is True

    def test_check_not_favourite_before_add(self, client, md_file):
        resp = client.get(f"/api/favourites/check?path={md_file}")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["is_favourite"] is False

    def test_update_name(self, client, md_file):
        fav_id = client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
            "id"
        ]
        resp = client.put(f"/api/favourites/{fav_id}", json={"name": "My Notes"})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["name"] == "My Notes"

    def test_update_tags(self, client, md_file):
        fav_id = client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
            "id"
        ]
        resp = client.put(f"/api/favourites/{fav_id}", json={"tags": ["work", "docs"]})
        assert resp.status_code == 200
        assert set(resp.get_json()["data"]["tags"]) == {"work", "docs"}

    def test_delete_favourite(self, client, md_file):
        fav_id = client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
            "id"
        ]
        resp = client.delete(f"/api/favourites/{fav_id}")
        assert resp.status_code == 200
        assert client.get("/api/favourites").get_json()["data"] == []

    def test_delete_then_check_not_favourite(self, client, md_file):
        fav_id = client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
            "id"
        ]
        client.delete(f"/api/favourites/{fav_id}")
        resp = client.get(f"/api/favourites/check?path={md_file}")
        assert resp.get_json()["data"]["is_favourite"] is False

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/favourites/99999")
        assert resp.status_code == 404

    def test_update_nonexistent_returns_404(self, client):
        resp = client.put("/api/favourites/99999", json={"name": "Ghost"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Search workflow
# ---------------------------------------------------------------------------


class TestFavouritesSearchWorkflow:
    def test_search_finds_added_favourite_by_name(self, client, md_file):
        add_resp = client.post("/api/favourites", json={"path": str(md_file)})
        fav_id = add_resp.get_json()["data"]["id"]
        client.put(f"/api/favourites/{fav_id}", json={"name": "My Notes"})
        resp = client.get("/api/favourites/search?q=Notes")
        assert resp.status_code == 200
        results = resp.get_json()["data"]
        assert any("notes" in r["path"].lower() or "Notes" in r.get("name", "") for r in results)

    def test_search_missing_q_returns_400(self, client):
        resp = client.get("/api/favourites/search")
        assert resp.status_code == 400

    def test_search_empty_db_returns_empty_list(self, client):
        resp = client.get("/api/favourites/search?q=anything")
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []


# ---------------------------------------------------------------------------
# Multi-file workflow
# ---------------------------------------------------------------------------


class TestFavouritesMultiFileWorkflow:
    def test_add_multiple_and_list_all(self, client, md_file, md_file2):
        client.post("/api/favourites", json={"path": str(md_file)})
        client.post("/api/favourites", json={"path": str(md_file2)})
        items = client.get("/api/favourites").get_json()["data"]
        paths = {i["path"] for i in items}
        assert str(md_file) in paths
        assert str(md_file2) in paths

    def test_delete_one_keeps_other(self, client, md_file, md_file2):
        id1 = client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"]["id"]
        client.post("/api/favourites", json={"path": str(md_file2)})
        client.delete(f"/api/favourites/{id1}")
        items = client.get("/api/favourites").get_json()["data"]
        assert len(items) == 1
        assert items[0]["path"] == str(md_file2)
