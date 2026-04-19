"""Tests configuration."""

import pytest


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


# ---------------------------------------------------------------------------
# Favourites test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_conn(tmp_path, monkeypatch):
    """Provide an isolated favourites DB for each test.

    Patches get_db_path to point at a temp file, runs init_db(), then
    tears down after the test by removing the file.
    """
    test_db = tmp_path / "test_favourites.db"

    # Patch before importing database so the path is used from the start
    import markdown_viewer.db.database as db_module  # noqa: PLC0415

    monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)

    # Reset FTS flag so each test can probe afresh
    db_module.FTS5_ENABLED = False

    # Bootstrap schema using a real Flask app context
    from markdown_viewer.app import create_app  # noqa: PLC0415

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with app.app_context():
        db_module.init_db()
        yield db_module.get_db()


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    """Flask test client with an isolated favourites DB."""
    test_db = tmp_path / "test_favourites.db"

    import markdown_viewer.db.database as db_module  # noqa: PLC0415

    monkeypatch.setattr(db_module, "get_db_path", lambda: test_db)
    db_module.FTS5_ENABLED = False

    from markdown_viewer.app import create_app  # noqa: PLC0415

    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with app.test_client() as client:
        with app.app_context():
            yield client
