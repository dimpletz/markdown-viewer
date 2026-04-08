"""
Main entry point for the markdown-viewer application.
"""

import sys
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
        except FileNotFoundError:
            raise RuntimeError(
                "npm not found. Please install Node.js from https://nodejs.org/ and ensure it is on your PATH."
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"npm install failed with exit code {e.returncode}.") from e
    
    # Start Electron
    print("Starting Markdown Viewer...")
    try:
        subprocess.Popen(["npm", "start"], cwd=electron_path)
    except FileNotFoundError:
        raise RuntimeError(
            "npm not found. Please install Node.js from https://nodejs.org/ and ensure it is on your PATH."
        )


def main():
    """Main entry point."""
    import argparse
    
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
    
    # Start the Flask backend server
    print(f"Starting backend server on port {args.port}...")
    server_process = start_server(port=args.port, debug=False)
    
    # Wait for server to be ready with a health-check poll instead of fixed sleep
    backend_url = f"http://localhost:{args.port}/api/health"
    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen(backend_url, timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    
    if args.no_gui:
        print(f"Server running at http://localhost:{args.port}")
        print("Press Ctrl+C to stop")
        try:
            server_process.wait()
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
        # Start Electron GUI
        if check_electron():
            try:
                # Set environment variable for backend port
                os.environ["BACKEND_PORT"] = str(args.port)
                if args.file:
                    os.environ["MARKDOWN_FILE"] = args.file
                start_electron()
                
                # Keep server running
                try:
                    server_process.join()
                except KeyboardInterrupt:
                    print("\nShutting down...")
                    server_process.terminate()
            except Exception as e:
                print(f"Error starting Electron: {e}")
                print("Falling back to browser mode...")
                webbrowser.open(f"http://localhost:{args.port}")
                try:
                    server_process.join()
                except KeyboardInterrupt:
                    print("\nShutting down...")
                    server_process.terminate()
        else:
            print("Electron not found. Opening in browser...")
            webbrowser.open(f"http://localhost:{args.port}")
            try:
                server_process.join()
            except KeyboardInterrupt:
                print("\nShutting down...")
                server_process.terminate()


if __name__ == "__main__":
    main()
