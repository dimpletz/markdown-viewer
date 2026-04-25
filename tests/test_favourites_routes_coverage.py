"""Additional tests for favourites_routes.py to improve coverage."""

from pathlib import Path
from unittest.mock import patch


def test_check_path_allowed_invalid_path(app_client):
    """_check_path_allowed returns False for invalid paths."""
    from markdown_viewer.favourites_routes import _check_path_allowed

    with app_client.application.test_request_context("/"):
        # Test with path that raises ValueError during resolve()
        with patch("pathlib.Path.resolve", side_effect=ValueError("invalid")):
            result = _check_path_allowed("some/path.md")
            assert result is False


def test_check_path_allowed_oserror(app_client):
    """_check_path_allowed returns False when OSError is raised."""
    from markdown_viewer.favourites_routes import _check_path_allowed

    with app_client.application.test_request_context("/"):
        # Test with path that raises OSError during resolve()
        with patch("pathlib.Path.resolve", side_effect=OSError("permission denied")):
            result = _check_path_allowed("some/path.md")
            assert result is False


def test_check_path_allowed_outside_base(app_client, tmp_path):
    """_check_path_allowed returns False for paths outside allowed directory."""
    from markdown_viewer.favourites_routes import _check_path_allowed
    from unittest.mock import patch

    with app_client.application.test_request_context("/"):
        # Set allowed directory to a specific tmp location
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        # Try to access a path outside the allowed directory
        outside_file = tmp_path / "outside" / "file.md"

        # Patch the config to use our specific allowed directory
        with patch.object(app_client.application.config, "get", return_value=str(allowed_dir)):
            _check_path_allowed(str(outside_file))


def test_list_favourites_exception_handling(app_client):
    """GET /api/favourites returns 500 when repo.list_all raises."""
    from markdown_viewer.db import favourites_repo

    with patch.object(favourites_repo, "list_all", side_effect=RuntimeError("database error")):
        response = app_client.get("/api/favourites")

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "database error" in data["error"]["message"]


def test_search_favourites_exception_handling(app_client):
    """GET /api/favourites/search returns 500 when repo.search raises."""
    from markdown_viewer.db import favourites_repo

    with patch.object(favourites_repo, "search", side_effect=RuntimeError("search failed")):
        response = app_client.get("/api/favourites/search?q=test")

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "search failed" in data["error"]["message"]


def test_check_favourite_exception_handling(app_client):
    """GET /api/favourites/check returns 500 when repo.check_by_path raises."""
    from markdown_viewer.db import favourites_repo

    with patch.object(favourites_repo, "check_by_path", side_effect=RuntimeError("check failed")):
        response = app_client.get("/api/favourites/check?path=/some/path.md")

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "check failed" in data["error"]["message"]


def test_add_favourite_path_traversal_blocked(app_client, tmp_path):
    """POST /api/favourites returns 403 when path is outside allowed directory."""
    # Create a file outside the allowed directory
    outside_file = Path("/etc/passwd")  # Path outside allowed directory

    # Mock _check_path_allowed to return False
    from markdown_viewer import favourites_routes

    with patch.object(favourites_routes, "_check_path_allowed", return_value=False):
        response = app_client.post("/api/favourites", json={"path": str(outside_file)})

    assert response.status_code == 403
    data = response.get_json()
    assert data["success"] is False
    assert "Access denied" in data["error"]["message"]


def test_add_favourite_exception_handling(app_client, tmp_path):
    """POST /api/favourites returns 500 when repo.add raises unexpected exception."""
    from markdown_viewer.db import favourites_repo

    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")

    with patch.object(favourites_repo, "add", side_effect=RuntimeError("add failed")):
        response = app_client.post("/api/favourites", json={"path": str(md_file)})

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "add failed" in data["error"]["message"]


def test_update_favourite_exception_handling(app_client):
    """PUT /api/favourites/<id> returns 500 when repo.update raises."""
    from markdown_viewer.db import favourites_repo

    with patch.object(favourites_repo, "update", side_effect=RuntimeError("update failed")):
        response = app_client.put("/api/favourites/1", json={"name": "New Name"})

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "update failed" in data["error"]["message"]


def test_delete_favourite_exception_handling(app_client):
    """DELETE /api/favourites/<id> returns 500 when repo.delete raises."""
    from markdown_viewer.db import favourites_repo

    with patch.object(favourites_repo, "delete", side_effect=RuntimeError("delete failed")):
        response = app_client.delete("/api/favourites/1")

    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "delete failed" in data["error"]["message"]
