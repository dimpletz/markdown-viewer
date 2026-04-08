"""Tests for server.py (Flask server management)."""

import pytest
from unittest.mock import patch, MagicMock


def test_start_server_returns_process():
    """start_server() returns a started multiprocessing.Process."""
    import multiprocessing

    mock_process = MagicMock(spec=multiprocessing.Process)

    with patch("markdown_viewer.server.multiprocessing.Process", return_value=mock_process):
        from markdown_viewer.server import start_server
        result = start_server(port=5099)

    mock_process.start.assert_called_once()
    assert result is mock_process


def test_start_server_passes_port_to_process():
    """start_server() passes port and debug args to the Process target."""
    import multiprocessing

    mock_process = MagicMock(spec=multiprocessing.Process)

    with patch("markdown_viewer.server.multiprocessing.Process", return_value=mock_process) as mock_cls:
        from markdown_viewer.server import start_server
        start_server(port=5099, debug=False)

    _, kwargs = mock_cls.call_args
    assert kwargs["args"] == (5099, False)


def test_run_flask_app_calls_app_run(monkeypatch, tmp_path):
    """run_flask_app() creates the Flask app and calls app.run()."""
    (tmp_path / "temp").mkdir()
    (tmp_path / "uploads").mkdir()
    monkeypatch.setenv("SECRET_KEY", "test-server-secret")

    mock_app = MagicMock()

    with patch("markdown_viewer.app.create_app", return_value=mock_app):
        from markdown_viewer.server import run_flask_app
        run_flask_app(port=5099, debug=False)

    mock_app.run.assert_called_once_with(
        host="127.0.0.1", port=5099, debug=False, use_reloader=False
    )


def test_run_flask_app_disables_debug_in_production(monkeypatch):
    """run_flask_app() forces debug=False when NODE_ENV=production."""
    monkeypatch.setenv("SECRET_KEY", "test-server-secret")
    monkeypatch.setenv("NODE_ENV", "production")

    mock_app = MagicMock()

    with patch("markdown_viewer.app.create_app", return_value=mock_app):
        from markdown_viewer.server import run_flask_app
        run_flask_app(debug=True)

    _, kwargs = mock_app.run.call_args
    assert kwargs["debug"] is False


def test_signal_handler_terminates_live_process():
    """The signal_handler registered by start_server terminates a live process."""
    import multiprocessing
    import signal as signal_module

    mock_process = MagicMock(spec=multiprocessing.Process)
    mock_process.is_alive.return_value = True

    captured_handler = {}

    def fake_signal(sig, handler):
        captured_handler[sig] = handler

    with patch("markdown_viewer.server.multiprocessing.Process", return_value=mock_process), \
         patch("markdown_viewer.server.signal.signal", side_effect=fake_signal):
        from markdown_viewer.server import start_server
        start_server(port=5099)

    handler = captured_handler[signal_module.SIGINT]
    with pytest.raises(SystemExit):
        handler(signal_module.SIGINT, None)

    mock_process.terminate.assert_called_once()
    mock_process.join.assert_called_once()
    mock_process.kill.assert_called_once()  # called because is_alive() stays True


def test_signal_handler_skips_dead_process():
    """The signal_handler does not terminate a process that is already dead."""
    import multiprocessing
    import signal as signal_module

    mock_process = MagicMock(spec=multiprocessing.Process)
    mock_process.is_alive.return_value = False

    captured_handler = {}

    def fake_signal(sig, handler):
        captured_handler[sig] = handler

    with patch("markdown_viewer.server.multiprocessing.Process", return_value=mock_process), \
         patch("markdown_viewer.server.signal.signal", side_effect=fake_signal):
        from markdown_viewer.server import start_server
        start_server(port=5099)

    handler = captured_handler[signal_module.SIGTERM]
    with pytest.raises(SystemExit):
        handler(signal_module.SIGTERM, None)

    mock_process.terminate.assert_not_called()
