"""Tests for server.py (Flask server management)."""

import threading
import pytest
from unittest.mock import patch, MagicMock

from markdown_viewer.server import _ServerHandle, start_server, run_flask_app


def test_start_server_returns_server_handle():
    """start_server() returns a _ServerHandle wrapping a daemon thread."""
    mock_thread = MagicMock(spec=threading.Thread)

    with patch("markdown_viewer.server.threading.Thread", return_value=mock_thread):
        result = start_server(port=5099)

    mock_thread.start.assert_called_once()
    assert isinstance(result, _ServerHandle)


def test_start_server_passes_port_to_thread():
    """start_server() passes port and debug args to the thread target."""
    mock_thread = MagicMock(spec=threading.Thread)

    with patch("markdown_viewer.server.threading.Thread", return_value=mock_thread) as mock_cls:
        start_server(port=5099, debug=False)

    _, kwargs = mock_cls.call_args
    assert kwargs["args"] == (5099, False)
    assert kwargs["daemon"] is True


def test_run_flask_app_calls_app_run():
    """run_flask_app() creates the Flask app and calls app.run()."""
    mock_app = MagicMock()

    with patch("markdown_viewer.app.create_app", return_value=mock_app):
        run_flask_app(port=5099, debug=False)

    mock_app.run.assert_called_once_with(
        host="127.0.0.1", port=5099, debug=False, use_reloader=False
    )


def test_run_flask_app_always_disables_debug():
    """run_flask_app() always passes debug=False to app.run()."""
    mock_app = MagicMock()

    with patch("markdown_viewer.app.create_app", return_value=mock_app):
        run_flask_app(port=5099, debug=True)

    _, kwargs = mock_app.run.call_args
    assert kwargs["debug"] is False


def test_server_handle_join_calls_thread_join():
    """_ServerHandle.join() delegates to the wrapped thread."""
    mock_thread = MagicMock(spec=threading.Thread)
    # First call returns True (enters loop), second returns False (exits loop)
    mock_thread.is_alive.side_effect = [True, False]
    handle = _ServerHandle(mock_thread)
    handle.join()
    mock_thread.join.assert_called_once()


def test_server_handle_terminate_is_noop():
    """_ServerHandle.terminate() is a no-op (daemon thread exits with main)."""
    mock_thread = MagicMock(spec=threading.Thread)
    handle = _ServerHandle(mock_thread)
    handle.terminate()  # should not raise


def test_server_handle_is_alive_delegates():
    """_ServerHandle.is_alive() delegates to the wrapped thread."""
    mock_thread = MagicMock(spec=threading.Thread)
    mock_thread.is_alive.return_value = True
    handle = _ServerHandle(mock_thread)
    assert handle.is_alive() is True



