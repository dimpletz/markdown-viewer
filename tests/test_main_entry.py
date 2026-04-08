"""Tests for __main__.py (application entry point)."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_check_electron_returns_bool():
    """check_electron() returns a boolean indicating if electron is available."""
    from markdown_viewer.__main__ import check_electron

    result = check_electron()
    assert isinstance(result, bool)


def test_check_electron_false_when_no_package_json(tmp_path):
    """check_electron() returns False when electron/package.json is absent."""
    with patch("markdown_viewer.__main__.__file__", str(tmp_path / "__main__.py")):
        from markdown_viewer.__main__ import check_electron
        result = check_electron()

    assert result is False


def test_check_electron_true_when_package_json_present(tmp_path):
    """check_electron() returns True when electron/package.json exists."""
    electron_dir = tmp_path / "electron"
    electron_dir.mkdir()
    (electron_dir / "package.json").write_text("{}")

    with patch("markdown_viewer.__main__.__file__", str(tmp_path / "__main__.py")):
        from markdown_viewer.__main__ import check_electron
        result = check_electron()

    assert result is True


def test_start_electron_calls_npm_start():
    """start_electron() calls npm start via subprocess.Popen."""
    with patch("subprocess.Popen") as mock_popen, \
         patch("subprocess.run"):
        from markdown_viewer.__main__ import start_electron
        start_electron()

    mock_popen.assert_called_once()
    args, _ = mock_popen.call_args
    assert args[0] == ["npm", "start"]


def test_start_electron_installs_if_no_node_modules(tmp_path):
    """start_electron() runs npm install when node_modules is absent."""
    # Point electron path to a dir without node_modules
    electron_dir = tmp_path / "electron"
    electron_dir.mkdir()

    with patch("markdown_viewer.__main__.__file__", str(tmp_path / "__main__.py")), \
         patch("subprocess.run") as mock_run, \
         patch("subprocess.Popen"):
        from markdown_viewer.__main__ import start_electron
        start_electron()

    # npm install should have been called
    run_calls = [c for c in mock_run.call_args_list if c[0][0] == ["npm", "install"]]
    assert run_calls


def test_main_no_gui_mode():
    """main() with --no-gui starts server and waits for KeyboardInterrupt."""
    mock_process = MagicMock()
    mock_process.wait.side_effect = KeyboardInterrupt

    with patch("sys.argv", ["markdown_viewer"]), \
         patch("markdown_viewer.__main__.start_server", return_value=mock_process), \
         patch("urllib.request.urlopen"), \
         patch("markdown_viewer.__main__.time.sleep"), \
         patch("sys.argv", ["markdown_viewer", "--no-gui"]):

        from markdown_viewer.__main__ import main
        main()

    mock_process.terminate.assert_called_once()


def test_main_browser_mode():
    """main() with --browser opens a browser tab and waits."""
    mock_process = MagicMock()
    mock_process.join.side_effect = KeyboardInterrupt

    with patch("sys.argv", ["markdown_viewer", "--browser"]), \
         patch("markdown_viewer.__main__.start_server", return_value=mock_process), \
         patch("urllib.request.urlopen"), \
         patch("markdown_viewer.__main__.time.sleep"), \
         patch("webbrowser.open") as mock_browser:

        from markdown_viewer.__main__ import main
        main()

    mock_browser.assert_called_once()
    mock_process.terminate.assert_called_once()


def test_main_electron_not_found_falls_back_to_browser():
    """main() without --browser opens browser when Electron is unavailable."""
    mock_process = MagicMock()
    mock_process.join.side_effect = KeyboardInterrupt

    with patch("sys.argv", ["markdown_viewer"]), \
         patch("markdown_viewer.__main__.start_server", return_value=mock_process), \
         patch("urllib.request.urlopen"), \
         patch("markdown_viewer.__main__.time.sleep"), \
         patch("markdown_viewer.__main__.check_electron", return_value=False), \
         patch("webbrowser.open") as mock_browser:

        from markdown_viewer.__main__ import main
        main()

    mock_browser.assert_called_once()


def test_main_electron_start_error_falls_back():
    """main() falls back to browser when start_electron() raises."""
    mock_process = MagicMock()
    mock_process.join.side_effect = [None, KeyboardInterrupt]  # 2nd join = shutdown

    with patch("sys.argv", ["markdown_viewer"]), \
         patch("markdown_viewer.__main__.start_server", return_value=mock_process), \
         patch("urllib.request.urlopen"), \
         patch("markdown_viewer.__main__.time.sleep"), \
         patch("markdown_viewer.__main__.check_electron", return_value=True), \
         patch("markdown_viewer.__main__.start_electron", side_effect=RuntimeError("no npm")), \
         patch("webbrowser.open") as mock_browser:

        from markdown_viewer.__main__ import main
        main()

    mock_browser.assert_called_once()
