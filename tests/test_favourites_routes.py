"""Tests for the favourites Flask blueprint (/api/favourites endpoints)."""

import pytest


def test_list_empty(app_client):
    """GET /api/favourites returns empty list initially."""
    resp = app_client.get("/api/favourites")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"] == []


def test_add_and_list(app_client, tmp_path):
    """POST then GET returns the new favourite."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test")

    resp = app_client.post("/api/favourites", json={"path": str(md_file)})
    assert resp.status_code == 201
    d = resp.get_json()
    assert d["success"] is True
    assert d["data"]["filename"] == "test.md"

    list_resp = app_client.get("/api/favourites")
    assert list_resp.status_code == 200
    items = list_resp.get_json()["data"]
    assert len(items) == 1
    assert items[0]["filename"] == "test.md"


def test_add_missing_path(app_client):
    """POST without path returns 400."""
    resp = app_client.post("/api/favourites", json={})
    assert resp.status_code == 400


def test_add_nonexistent_file(app_client, tmp_path):
    """POST with non-existent file returns 400."""
    resp = app_client.post("/api/favourites", json={"path": str(tmp_path / "ghost.md")})
    assert resp.status_code == 400


def test_add_duplicate(app_client, tmp_path):
    """POST the same path twice returns 409 on the second request."""
    md_file = tmp_path / "dup.md"
    md_file.write_text("Dup")

    app_client.post("/api/favourites", json={"path": str(md_file)})
    resp = app_client.post("/api/favourites", json={"path": str(md_file)})
    assert resp.status_code == 409


def test_check_not_favourite(app_client):
    """GET /api/favourites/check returns is_favourite=false for unknown."""
    resp = app_client.get("/api/favourites/check", query_string={"path": "/some/unknown.md"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"]["is_favourite"] is False


def test_check_is_favourite(app_client, tmp_path):
    """GET /api/favourites/check returns is_favourite=true after add."""
    md_file = tmp_path / "fav.md"
    md_file.write_text("Fav")
    add_resp = app_client.post("/api/favourites", json={"path": str(md_file)})
    fav_id = add_resp.get_json()["data"]["id"]

    resp = app_client.get("/api/favourites/check", query_string={"path": str(md_file)})
    data = resp.get_json()
    assert data["data"]["is_favourite"] is True
    assert data["data"]["id"] == fav_id


def test_check_missing_path(app_client):
    """GET /api/favourites/check without path returns 400."""
    resp = app_client.get("/api/favourites/check")
    assert resp.status_code == 400


def test_update_name(app_client, tmp_path):
    """PUT updates the name."""
    md_file = tmp_path / "upd.md"
    md_file.write_text("Upd")
    fav_id = app_client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
        "id"
    ]

    resp = app_client.put(f"/api/favourites/{fav_id}", json={"name": "Custom"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Custom"


def test_update_tags(app_client, tmp_path):
    """PUT updates tags."""
    md_file = tmp_path / "tags.md"
    md_file.write_text("Tags")
    fav_id = app_client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
        "id"
    ]

    resp = app_client.put(f"/api/favourites/{fav_id}", json={"tags": ["alpha", "beta"]})
    assert resp.status_code == 200
    tags = resp.get_json()["data"]["tags"]
    assert set(tags) == {"alpha", "beta"}


def test_update_too_many_tags(app_client, tmp_path):
    """PUT rejects more than 20 tags (SC2)."""
    md_file = tmp_path / "manytags.md"
    md_file.write_text("Many")
    fav_id = app_client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
        "id"
    ]

    many_tags = [f"tag{i}" for i in range(21)]
    resp = app_client.put(f"/api/favourites/{fav_id}", json={"tags": many_tags})
    assert resp.status_code == 400


def test_update_not_found(app_client):
    """PUT on unknown id returns 404."""
    resp = app_client.put("/api/favourites/9999", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_happy(app_client, tmp_path):
    """DELETE removes the favourite."""
    md_file = tmp_path / "del.md"
    md_file.write_text("Del")
    fav_id = app_client.post("/api/favourites", json={"path": str(md_file)}).get_json()["data"][
        "id"
    ]

    resp = app_client.delete(f"/api/favourites/{fav_id}")
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

    # Confirm it's gone
    assert app_client.get("/api/favourites").get_json()["data"] == []


def test_delete_not_found(app_client):
    """DELETE on unknown id returns 404."""
    resp = app_client.delete("/api/favourites/9999")
    assert resp.status_code == 404


def test_search_returns_results(app_client, tmp_path):
    """GET /api/favourites/search returns matching items."""
    md_file = tmp_path / "findme.md"
    md_file.write_text("Find me")
    app_client.post("/api/favourites", json={"path": str(md_file)})

    resp = app_client.get("/api/favourites/search", query_string={"q": "findme"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert any(item["filename"] == "findme.md" for item in data["data"])


def test_search_missing_q(app_client):
    """GET /api/favourites/search without q returns 400."""
    resp = app_client.get("/api/favourites/search")
    assert resp.status_code == 400
