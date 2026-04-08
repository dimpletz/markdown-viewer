"""Tests for the first-time setup module (markdown_viewer/setup.py)."""

import subprocess
import sys
import pytest
from unittest.mock import patch, MagicMock


def test_print_step(capsys):
    """print_step() outputs a formatted step header."""
    from markdown_viewer.setup import print_step

    print_step(2, 5, "Checking dependencies")

    captured = capsys.readouterr()
    assert "[2/5]" in captured.out
    assert "Checking dependencies" in captured.out


def test_run_command_success():
    """run_command() returns True when subprocess succeeds."""
    from markdown_viewer.setup import run_command

    with patch("subprocess.run") as mock_run:
        result = run_command(["echo", "hello"], description="echo")

    assert result is True
    mock_run.assert_called_once()


def test_run_command_called_process_error():
    """run_command() returns False on CalledProcessError."""
    from markdown_viewer.setup import run_command

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")):
        result = run_command(["fail"], description="fail cmd")

    assert result is False


def test_run_command_file_not_found():
    """run_command() returns False when the executable is not found."""
    from markdown_viewer.setup import run_command

    with patch("subprocess.run", side_effect=FileNotFoundError()):
        result = run_command(["nonexistent_binary"])

    assert result is False


def test_run_command_uses_cwd():
    """run_command() passes cwd to subprocess.run."""
    from markdown_viewer.setup import run_command

    with patch("subprocess.run") as mock_run:
        run_command(["echo"], cwd="/some/path")

    _, kwargs = mock_run.call_args
    assert kwargs.get("cwd") == "/some/path"


def test_main_all_succeed(capsys):
    """setup.main() returns 0 and prints SETUP COMPLETE when all steps succeed."""
    from markdown_viewer.setup import main

    with patch("markdown_viewer.setup.run_command", return_value=True):
        result = main()

    captured = capsys.readouterr()
    assert "SETUP COMPLETE" in captured.out
    assert result == 0


def test_main_playwright_failure(capsys):
    """setup.main() continues (with warning) when Playwright install fails."""
    from markdown_viewer.setup import main

    # run_command returns False for all subprocess calls (optional failures)
    with patch("markdown_viewer.setup.run_command", return_value=False):
        result = main()

    # Optional failures still allow overall success (return 0)
    captured = capsys.readouterr()
    assert "SETUP COMPLETE" in captured.out
    assert isinstance(result, int)


def test_main_prints_next_steps(capsys):
    """setup.main() always prints NEXT STEPS instructions."""
    from markdown_viewer.setup import main

    with patch("markdown_viewer.setup.run_command", return_value=True):
        main()

    captured = capsys.readouterr()
    assert "NEXT STEPS" in captured.out


def test_main_python_version_check(capsys):
    """setup.main() shows current Python version info."""
    from markdown_viewer.setup import main

    with patch("markdown_viewer.setup.run_command", return_value=True):
        main()

    captured = capsys.readouterr()
    assert "Python version:" in captured.out


def test_main_python_too_old(capsys):
    """setup.main() prints an error when Python < 3.8."""
    from markdown_viewer.setup import main

    fake_version = MagicMock()
    fake_version.major = 2
    fake_version.minor = 7
    fake_version.micro = 18
    with patch("markdown_viewer.setup.run_command", return_value=True), \
         patch("markdown_viewer.setup.sys.version_info", fake_version):
        result = main()

    captured = capsys.readouterr()
    assert "Python 3.8 or higher is required" in captured.out
    assert isinstance(result, int)  # function still completes


def test_main_electron_dir_found_npm_succeeds(capsys, tmp_path):
    """setup.main() reports Electron installed when electron dir exists and npm works."""
    import markdown_viewer.setup as setup_module
    from markdown_viewer.setup import main

    # Create the electron directory structure that setup.main() looks for
    electron_dir = tmp_path / "markdown_viewer" / "electron"
    electron_dir.mkdir(parents=True)

    # Point setup module's __file__ to tmp_path so the path resolves correctly
    with patch.object(setup_module, "__file__", str(tmp_path / "setup.py")), \
         patch("markdown_viewer.setup.run_command", return_value=True):
        result = main()

    captured = capsys.readouterr()
    assert "Electron dependencies installed" in captured.out
    assert result == 0


def test_main_import_error(capsys):
    """setup.main() records error when markdown_viewer cannot be imported."""
    import builtins
    from markdown_viewer.setup import main

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "markdown_viewer":
            raise ImportError("mocked import failure")
        return original_import(name, *args, **kwargs)

    with patch("markdown_viewer.setup.run_command", return_value=True), \
         patch("builtins.__import__", side_effect=mock_import):
        result = main()

    captured = capsys.readouterr()
    assert "Could not import markdown_viewer" in captured.out
    assert result == 1
