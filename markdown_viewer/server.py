"""
Server management for the markdown viewer backend.
"""

import os
import atexit
import pathlib
import tempfile
import threading
import logging

logger = logging.getLogger(__name__)


def pid_file_path(port: int) -> pathlib.Path:
    """Return the path to the PID file for the given port."""
    return pathlib.Path(tempfile.gettempdir()) / f"mdview-{port}.pid"


def run_flask_app(  # pylint: disable=unused-argument
    port: int = 5000, debug: bool = False, use_reloader: bool = False
) -> None:
    """Run the Flask application (called in a background thread or detached process)."""
    # Write PID file so `mdview --stop` can kill this process.
    pid_file = pid_file_path(port)
    try:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
        atexit.register(lambda: pid_file.unlink(missing_ok=True))
    except OSError:
        pass

    from .app import create_app  # pylint: disable=import-outside-toplevel

    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=use_reloader)


class _ServerHandle:
    """Thin wrapper around a daemon thread that mimics a Process interface."""

    def __init__(self, thread: threading.Thread):
        self._thread = thread

    def join(self):
        """Wait for the server thread to finish."""
        # On Windows, thread.join() with no timeout blocks KeyboardInterrupt entirely.
        # Poll with a short timeout so Ctrl+C can be delivered between polls.
        while self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def terminate(self):
        """Signal the server to stop (daemon thread exits with the main process)."""
        # Daemon thread dies automatically when the main process exits.
        # Nothing to do explicitly.

    def is_alive(self):
        """Return True if the server thread is still running."""
        return self._thread.is_alive()


def start_server(port: int = 5000, debug: bool = False) -> _ServerHandle:
    """
    Start the Flask server in a background daemon thread.

    Using a thread (instead of multiprocessing.Process) ensures the server
    inherits the current Python environment, which is essential when the app
    is launched via an installed entry-point (e.g. ``mdview``) where a child
    process would start the system Python rather than the virtualenv.

    Returns:
        _ServerHandle with .join() and .terminate() methods.
    """
    thread = threading.Thread(
        target=run_flask_app,
        args=(port, debug),
        daemon=True,  # dies automatically when the main thread exits
    )
    thread.start()
    return _ServerHandle(thread)
