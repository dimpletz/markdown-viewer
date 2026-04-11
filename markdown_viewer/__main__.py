"""
Main entry point for the markdown-viewer application.
"""

import os
import subprocess
import webbrowser
import time
from pathlib import Path
from .server import start_server


def check_electron():
    """Check if Electron is available."""
    electron_path = Path(__file__).parent / "electron"
    package_json = electron_path / "package.json"
    return package_json.exists()


def start_electron():
    """Start the Electron application."""
    electron_path = Path(__file__).parent / "electron"

    # Check if node_modules exists
    node_modules = electron_path / "node_modules"
    if not node_modules.exists():
        print("Installing Electron dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=electron_path, check=True)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "npm not found. Please install Node.js from https://nodejs.org/"
                " and ensure it is on your PATH."
            ) from exc
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"npm install failed with exit code {e.returncode}.") from e

    # Start Electron
    print("Starting Markdown Viewer...")
    try:
        subprocess.Popen(["npm", "start"], cwd=electron_path)  # pylint: disable=consider-using-with
    except FileNotFoundError as exc:
        raise RuntimeError(
            "npm not found. Please install Node.js from https://nodejs.org/"
            " and ensure it is on your PATH."
        ) from exc


def _wait_for_server(port: int, attempts: int = 20) -> None:
    """Poll the server health endpoint until it responds or attempts are exhausted."""
    import http.client  # pylint: disable=import-outside-toplevel

    for _ in range(attempts):
        try:
            conn = http.client.HTTPConnection("localhost", port, timeout=1)
            conn.request("GET", "/api/health")
            conn.getresponse()
            conn.close()
            return
        except Exception:  # pylint: disable=broad-exception-caught
            time.sleep(0.25)


def main():
    """Main entry point."""
    import argparse  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser(
        description="Markdown Viewer - Advanced markdown viewer with export and translation"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Markdown file to open",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for the backend server (default: 5000)",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Start server only without GUI",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Open in web browser instead of Electron",
    )

    args = parser.parse_args()

    # Allow access to the full filesystem root for local CLI use (server is localhost-only)
    os.environ.setdefault("ALLOWED_DOCUMENTS_DIR", str(Path(Path.home().anchor)))

    # Start the Flask backend server
    print(f"Starting backend server on port {args.port}...")
    server_process = start_server(port=args.port, debug=False)

    # Wait for server to be ready with a health-check poll instead of fixed sleep
    _wait_for_server(args.port)

    if args.no_gui:
        print(f"Server running at http://localhost:{args.port}")
        print("Press Ctrl+C to stop")
        try:
            server_process.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server_process.terminate()
    elif args.browser:
        url = f"http://localhost:{args.port}"
        if args.file:
            url += f"?file={args.file}"
        print(f"Opening {url} in browser...")
        webbrowser.open(url)
        try:
            server_process.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server_process.terminate()
    else:
        # No --browser or --no-gui flag: default to browser mode
        print("Opening in browser... (use --no-gui to run server only)")
        url = f"http://localhost:{args.port}"
        if args.file:
            url += f"?file={args.file}"
        print(f"Opening {url} in browser...")
        webbrowser.open(url)
        try:
            server_process.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server_process.terminate()


if __name__ == "__main__":
    main()
