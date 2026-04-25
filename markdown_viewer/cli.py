"""
Command-line interface for markdown viewer.
Render markdown files and open them in browser.
Export to PDF/Word and share via email.
"""

import os
import re
import base64
import mimetypes
import subprocess
import sys
import argparse
import webbrowser
import tempfile
from pathlib import Path
from typing import Optional
import urllib.parse

from markdown_viewer import __version__

from .processors.markdown_processor import MarkdownProcessor

_URL_SCHEMES = ("http://", "https://", "ftp://", "ftps://")


_ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}


def _embed_local_images(html: str, base_dir: Path) -> str:
    """Replace local image src attributes with base64 data URIs.

    Used by the CLI path where the HTML is opened as a file:// URL and there is
    no backend server available to serve /api/image requests.
    Remote URLs and data: URIs are left unchanged.
    """

    def replace_src(match: re.Match) -> str:
        src = match.group(1)
        # Leave remote URLs, data URIs unchanged
        if src.startswith(("http://", "https://", "data:", "ftp://")):
            return match.group(0)

        # URL-decode so %20 → space, etc.
        src_decoded = urllib.parse.unquote(src)

        # Resolve path (handle both absolute Windows paths and relative paths)
        if os.path.isabs(src_decoded):
            img_path = Path(src_decoded)
        else:
            # Normalize path separators (backslashes from Windows paths used as URLs)
            src_normalized = src_decoded.replace("\\", "/")
            img_path = (base_dir / src_normalized).resolve()

        if img_path.suffix.lower() not in _ALLOWED_IMAGE_EXTENSIONS:
            return match.group(0)

        try:
            img_data = img_path.read_bytes()
        except OSError:
            return match.group(0)

        mime_type, _ = mimetypes.guess_type(str(img_path))
        if img_path.suffix.lower() == ".svg":
            mime_type = "image/svg+xml"
        mime_type = mime_type or "application/octet-stream"

        b64 = base64.b64encode(img_data).decode("ascii")
        return f'src="data:{mime_type};base64,{b64}"'

    return re.sub(r'src="([^"]*)"', replace_src, html)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-color-mode="light" data-light-theme="light" data-dark-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.0/github-markdown-light.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github.min.css">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.45/dist/katex.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.45/dist/katex.min.css">
    <style>
        /* Force light mode */
        :root {{
            color-scheme: light;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            padding-top: 80px; /* Make room for toolbar */
            background-color: #f6f8fa !important;
            color: #24292e !important;
        }}

        /* Floating Toolbar */
        .floating-toolbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }}
        .toolbar-left, .toolbar-right {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .toolbar-btn {{
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .toolbar-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .toolbar-btn:active {{
            transform: translateY(0);
        }}
        .toolbar-separator {{
            width: 1px;
            height: 24px;
            background: rgba(255,255,255,0.3);
            margin: 0 4px;
        }}
        .toolbar-title {{
            font-weight: 600;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .container {{
            max-width: 980px;
            margin: 0 auto;
            background-color: #ffffff !important;
            padding: 45px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }}
        .markdown-body {{
            box-sizing: border-box;
            min-width: 200px;
            font-size: 16px;
            line-height: 1.6;
            color: #24292e !important;
            background-color: #ffffff !important;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e4e8;
            color: #586069;
            font-size: 12px;
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
            background-color: #ffffff;
        }}
        /* Emoji sizing - scales dynamically with text */
        .markdown-body img.emoji,
        .markdown-body img.gemoji {{
            height: 1.2em !important;
            width: 1.2em !important;
            margin: 0 .05em 0 .1em;
            vertical-align: -0.2em;
            display: inline-block;
        }}
        /* Emojis in headings scale with heading size */
        .markdown-body h1 img.emoji,
        .markdown-body h1 img.gemoji {{
            height: 1.3em !important;
            width: 1.3em !important;
        }}
        .markdown-body h2 img.emoji,
        .markdown-body h2 img.gemoji {{
            height: 1.25em !important;
            width: 1.25em !important;
        }}
        .markdown-body h3 img.emoji,
        .markdown-body h3 img.gemoji {{
            height: 1.2em !important;
            width: 1.2em !important;
        }}

        /* Table of Contents styling */
        .markdown-body .toc {{
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 6px 10px;
            margin: 10px 0;
            font-size: 14px;
        }}
        .markdown-body .toc .toctitle,
        .markdown-body .toc span.toctitle {{
            display: block;
            font-weight: 900 !important;
            font-size: 18px;
            margin-bottom: 2px !important;
            margin-top: 0 !important;
            color: #24292e;
            line-height: 1.2 !important;
        }}
        .markdown-body .toc ul {{
            list-style: none;
            padding-left: 0;
            margin: 0 !important;
        }}
        .markdown-body .toc > ul {{
            margin: 0 !important;
        }}
        .markdown-body .toc ul ul {{
            padding-left: 16px;
            margin: 0 !important;
        }}
        .markdown-body .toc li {{
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.1 !important;
        }}
        .markdown-body .toc a {{
            color: #0969da;
            text-decoration: none;
            display: inline-block;
            padding: 0 !important;
            margin: 0 !important;
            line-height: 1.1 !important;
        }}
        .markdown-body .toc a:hover {{
            color: #0550ae;
            text-decoration: underline;
        }}

        /* Single line spacing overrides for all elements */
        .markdown-body h1,
        .markdown-body h2,
        .markdown-body h3,
        .markdown-body h4,
        .markdown-body h5,
        .markdown-body h6 {{
            margin-top: 16px !important;
            margin-bottom: 8px !important;
        }}
        .markdown-body h1:first-child,
        .markdown-body h2:first-child,
        .markdown-body h3:first-child {{
            margin-top: 0 !important;
        }}
        .markdown-body p {{
            margin-top: 0 !important;
            margin-bottom: 8px !important;
        }}
        .markdown-body ul,
        .markdown-body ol {{
            margin-top: 0 !important;
            margin-bottom: 8px !important;
            padding-left: 2em !important;
        }}
        .markdown-body li {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
        .markdown-body li > p {{
            margin-bottom: 0 !important;
        }}
        .markdown-body blockquote {{
            margin: 8px 0 !important;
            padding: 0 1em !important;
        }}
        .markdown-body pre {{
            margin-top: 0 !important;
            margin-bottom: 8px !important;
        }}
        .markdown-body code {{
            margin: 0 !important;
        }}
        .markdown-body table {{
            margin-top: 0 !important;
            margin-bottom: 8px !important;
        }}
        .markdown-body hr {{
            margin: 16px 0 !important;
        }}
        .markdown-body .highlight {{
            margin-bottom: 8px !important;
        }}
    </style>
</head>
<body>
    <!-- Floating Toolbar -->
    <div class="floating-toolbar">
        <div class="toolbar-left">
            <div class="toolbar-title">
                <span>📝</span>
                <span>{filename}</span>
            </div>
            <div class="toolbar-separator"></div>
            <button class="toolbar-btn" onclick="printToPDF()" title="Export as PDF (Ctrl+P)">
                <span>📄</span> PDF
            </button>
            <div class="toolbar-separator"></div>
            <button class="toolbar-btn" id="btnCopyAll" onclick="copyAll()" title="Copy All">
                <span>📋</span> Copy All
            </button>
        </div>
    </div>

    <div class="container">
        <article class="markdown-body">
{content}
        </article>
        <div class="footer">
            Generated by <strong>markdown-viewer</strong> | File: <code>{filename}</code>
        </div>
    </div>
    <script>
        // Wait for DOM to be ready
        document.addEventListener('DOMContentLoaded', function() {{
            // Initialize Mermaid for cross-version compatibility (v8/v9/v10/v11 syntax)
            mermaid.initialize({{
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose',
                fontFamily: 'monospace',
                suppressErrors: true
            }});

            // Render KaTeX math
            document.querySelectorAll('.arithmatex').forEach(function(el) {{
                try {{
                    let math = el.textContent.trim();
                    // Strip LaTeX delimiters
                    const isBlock = el.tagName === 'DIV';
                    if (isBlock) {{
                        // Block math: remove delimiters
                        math = math.replace(/^\\\\\\[/, '').replace(/\\\\\\]$/, '').trim();
                    }} else {{
                        // Inline math: remove delimiters
                        math = math.replace(/^\\\\\\(/, '').replace(/\\\\\\)$/, '').trim();
                    }}

                    katex.render(math, el, {{
                        displayMode: isBlock,
                        throwOnError: false,
                        trust: true
                    }});
                }} catch (e) {{
                    console.error('KaTeX render error:', e, el.textContent);
                }}
            }});

            // Render each Mermaid diagram individually for cross-version compatibility
            // Uses mermaid.render() so each diagram is isolated — one failure won't block others
            (async function() {{
                function decodeEntities(str) {{
                    return str.replace(/&amp;/g, '&').replace(/&lt;/g, '<')
                              .replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
                }}
                var diagrams = document.querySelectorAll('.mermaid');
                for (var i = 0; i < diagrams.length; i++) {{
                    var el = diagrams[i];
                    var source = decodeEntities((el.textContent || '').trim());
                    el.textContent = source;
                    try {{
                        var id = 'mermaid-' + Date.now() + '-' + i;
                        var result = await mermaid.render(id, source);
                        el.innerHTML = result.svg;
                    }} catch (e) {{
                        var escaped = source.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        el.innerHTML = '<details style="border:1px solid #fca;background:#fff8f5;border-radius:4px;padding:8px">'
                            + '<summary style="cursor:pointer;color:#c60;font-weight:bold">'
                            + '\u26a0 Diagram could not be rendered (click to view source)</summary>'
                            + '<pre style="margin:8px 0 0;overflow:auto;font-size:13px">' + escaped + '</pre></details>';
                        console.warn('Mermaid render failed:', e.message || e);
                    }}
                }}
            }})();
        }});
    </script>

    <!-- Export PDF Function -->
    <script>
        // Print to PDF using browser's print function
        function printToPDF() {{
            window.print();
        }}

        // Copy all markdown content to clipboard
        function copyAll() {{
            const btn = document.getElementById('btnCopyAll');
            const text = document.querySelector('.markdown-body').innerText;
            navigator.clipboard.writeText(text).then(() => {{
                const orig = btn.innerHTML;
                btn.innerHTML = '<span>✅</span> Copied!';
                setTimeout(() => {{ btn.innerHTML = orig; }}, 1500);
            }}).catch(() => {{
                btn.innerHTML = '<span>❌</span> Failed';
                setTimeout(() => {{ btn.innerHTML = orig; }}, 1500);
            }});
        }}

        // Keyboard shortcut for print
        document.addEventListener('keydown', (e) => {{
            if (e.ctrlKey && e.key === 'p') {{
                e.preventDefault();
                printToPDF();
            }}
        }});

        // Add print styles to hide toolbar when printing
        const printStyles = `
            @media print {{
                .floating-toolbar {{
                    display: none !important;
                }}
                body {{
                    padding-top: 0 !important;
                }}
                .footer {{
                    page-break-before: avoid;
                }}
            }}
        `;
        const styleSheet = document.createElement('style');
        styleSheet.textContent = printStyles;
        document.head.appendChild(styleSheet);
    </script>
</body>
</html>
"""


def _stop_server(port: int = 5000) -> int:
    """Stop the running mdview server. Returns 0 on success, 1 on failure."""
    import http.client  # pylint: disable=import-outside-toplevel

    # Try the HTTP shutdown endpoint first.
    try:
        conn = http.client.HTTPConnection("localhost", port, timeout=3)
        conn.request("GET", "/api/shutdown")
        conn.getresponse()
        conn.close()
        print(f"\u2705 Server on port {port} stopped.")
        return 0
    except Exception:  # pylint: disable=broad-exception-caught
        pass  # Server not running or already stopped — try PID fallback.

    # Fallback: kill by PID file written by server.py.
    from .server import pid_file_path  # pylint: disable=import-outside-toplevel

    pid_file = pid_file_path(port)
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            os.kill(pid, 15)  # SIGTERM (cross-platform int avoids signal import)
            pid_file.unlink(missing_ok=True)
            print(f"\u2705 Server (PID {pid}) stopped.")
            return 0
        except ProcessLookupError:
            pid_file.unlink(missing_ok=True)
            print(f"No running server found on port {port} (stale PID file removed).")
            return 0
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"\u274c Failed to stop server: {exc}", file=sys.stderr)
            return 1

    print(f"No mdview server found running on port {port}.")
    return 0


def _resolve_file(args) -> "Optional[int]":
    """Validate args.file, prompting the user if needed.

    Returns None when a valid file has been resolved into args.file.
    Returns 0 or 1 to signal that main() should exit early with that code.
    """
    valid_extensions = (".md", ".markdown", ".mdown")

    while True:
        if args.file is not None:
            raw = args.file if isinstance(args.file, str) else str(args.file)
            if raw.lower().startswith(_URL_SCHEMES):
                print(
                    f"Only local markdown files are supported — '{raw}' looks like a URL.\n"
                    "Please enter a local file path and try again.\n"
                    "Example: mdview README.md  or  mdview C:\\docs\\report.md"
                )
            else:
                args.file = Path(raw)
                if args.file.is_dir():
                    print(f"Error: '{args.file}' is a directory. Please include the filename.")
                    print(f"Example: mdview {args.file / 'README.md'}")
                elif not args.file.suffix:
                    print(
                        f"Error: '{args.file.name}' has no file extension."
                        " Please enter a valid .md file and try again."
                    )
                elif args.file.suffix.lower() not in valid_extensions:
                    print(
                        f"Error: '{args.file.name}' has an unsupported"
                        f" extension ('{args.file.suffix}')."
                        " Please provide a .md, .markdown, or .mdown file."
                    )
                elif not args.file.exists():
                    print(f"Error: '{args.file}' does not exist. Check the path and try again.")
                else:
                    return None  # valid — proceed
            if not sys.stdin.isatty():
                return 1

        if args.file is None and not sys.stdin.isatty():
            print("Usage: mdview <file.md>")
            print("Example: mdview README.md")
            print("         mdview C:\\docs\\report.md")
            return 1

        try:
            choice = input("Enter filename (or full path if not in current directory): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 0

        if not choice:
            print("No file entered. Please try again.")
            args.file = None
            continue

        if choice.endswith(("/", "\\")):
            print(f"Error: no filename in '{choice}'. Example: {Path(choice) / 'README.md'}")
            args.file = None
            continue

        args.file = choice  # kept as str; URL check + Path() conversion happen at next iteration


def _open_flask_dashboard(port: int = 5000, browser: Optional[str] = None) -> None:
    """Start the Flask backend and open the file-picker dashboard in the browser.

    Starts the server (if not already running) and opens ``http://localhost:<port>/``
    which serves the full browser UI for browsing and opening markdown files.
    """
    import time  # pylint: disable=import-outside-toplevel
    import http.client  # pylint: disable=import-outside-toplevel

    def _server_up(p: int) -> bool:
        try:
            conn = http.client.HTTPConnection("localhost", p, timeout=1)
            conn.request("GET", "/api/health")
            conn.getresponse()
            conn.close()
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    try:
        import flask as _flask  # noqa: F401  # pylint: disable=import-outside-toplevel
    except ImportError:
        print("\u274c Flask is not installed in the current Python environment.")
        print("   Run with:  poetry run mdview")
        print("   Or install: pip install markdown-viewer-app")
        return

    if not _server_up(port):
        env = os.environ.copy()
        env["BACKEND_PORT"] = str(port)  # Set BACKEND_PORT for CORS configuration
        server_cmd = [
            sys.executable,
            "-c",
            (
                "from markdown_viewer.server import run_flask_app;"
                f" run_flask_app(port={port}, use_reloader=False)"
            ),
        ]
        if sys.platform == "win32":
            CREATE_NEW_PROCESS_GROUP = 0x00000200  # pylint: disable=invalid-name
            CREATE_NO_WINDOW = 0x08000000  # pylint: disable=invalid-name
            subprocess.Popen(  # pylint: disable=consider-using-with
                server_cmd,
                creationflags=CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(  # pylint: disable=consider-using-with
                server_cmd,
                start_new_session=True,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        print(f"Starting server on port {port}...")
        for _ in range(40):
            if _server_up(port):
                break
            time.sleep(0.25)
        else:
            print("\u274c Server failed to start. Make sure all dependencies are installed.")
            print("   Try: pip install markdown-viewer-app")
            return

    url = f"http://localhost:{port}/"
    print(f"Opening dashboard: {url}")
    if browser:
        try:
            controller = webbrowser.get(browser)
            controller.open(url)
        except webbrowser.Error:
            subprocess.Popen(  # pylint: disable=consider-using-with
                [browser, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    elif sys.platform == "win32":
        # Use os.startfile (ShellExecute) to open URL with default browser; avoids shell=True.
        os.startfile(url)  # noqa: S606  # nosec B606
    else:
        webbrowser.open(url)


def _open_in_flask_app(filepath: Path, port: int = 5000, browser: Optional[str] = None) -> None:
    """Start the Flask backend and open the file in the browser.

    If a server is already running on *port* it is reused, so the terminal
    returns immediately.  Otherwise a fully-detached background process is
    spawned (the terminal is still free after the browser opens).

    Args:
        browser: Optional executable name or full path of the browser to use
                 (e.g. ``"firefox"``, ``"msedge"``, ``"/usr/bin/brave-browser"``).
                 When *None* the system default browser is used.
    """
    import time  # pylint: disable=import-outside-toplevel
    import http.client  # pylint: disable=import-outside-toplevel

    def _server_up(p: int) -> bool:
        """Return True if the server is accepting connections on *p*.
        Uses http.client directly to avoid urllib creating an SSL context
        (which hangs on some Windows Python 3.14 builds).
        """
        try:
            conn = http.client.HTTPConnection("localhost", p, timeout=1)
            conn.request("GET", "/api/health")
            conn.getresponse()
            conn.close()
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    # Fail fast with a helpful message if Flask is not in the current Python environment.
    # This happens when a user has two Python installs (e.g. system Python + Poetry venv)
    # and runs the bare `mdview` entry point installed in the system Python.
    try:
        import flask as _flask  # noqa: F401  # pylint: disable=import-outside-toplevel
    except ImportError:
        print("❌ Flask is not installed in the current Python environment.")
        print("   Run with:  poetry run mdview <file>")
        print("   Or install: pip install markdown-viewer-app")
        return

    abs_path = filepath.resolve()
    drive_root = Path(abs_path.anchor)  # e.g. C:\ on Windows, / on Unix

    # --- Check if a server is already running on this port ---
    server_already_running = _server_up(port)

    if not server_already_running:
        # Spawn a fully-detached background process so the terminal returns
        # immediately after the browser opens.
        env = os.environ.copy()
        env.setdefault("ALLOWED_DOCUMENTS_DIR", str(drive_root))
        env["BACKEND_PORT"] = str(port)  # Set BACKEND_PORT for CORS configuration

        server_cmd = [
            sys.executable,
            "-c",
            (
                "from markdown_viewer.server import run_flask_app;"
                f" run_flask_app(port={port}, use_reloader=False)"
            ),
        ]

        if sys.platform == "win32":
            CREATE_NEW_PROCESS_GROUP = 0x00000200  # pylint: disable=invalid-name
            CREATE_NO_WINDOW = 0x08000000  # pylint: disable=invalid-name
            subprocess.Popen(  # pylint: disable=consider-using-with
                server_cmd,
                creationflags=CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(  # pylint: disable=consider-using-with
                server_cmd,
                start_new_session=True,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Poll until the detached server is ready
        print(f"Starting server on port {port}...")
        server_ready = False
        for _ in range(40):
            if _server_up(port):
                server_ready = True
                break
            time.sleep(0.25)

        if not server_ready:
            print("❌ Server failed to start. Make sure all dependencies are installed.")
            print("   Try: pip install markdown-viewer-app")
            return

    url = f"http://localhost:{port}?file={urllib.parse.quote(str(abs_path))}"
    print(f"Opening {url}")
    if browser:
        # User specified an explicit browser — launch it directly so the
        # choice is respected regardless of the OS default.  Using
        # webbrowser.get() + register() ensures the path is resolved by
        # the stdlib (which handles quoting, PATH lookup, etc.).
        try:
            controller = webbrowser.get(browser)
            controller.open(url)
        except webbrowser.Error:
            # Fall back: try launching as a subprocess directly so the user
            # can pass a full executable path like '/usr/bin/brave-browser'.
            subprocess.Popen(  # pylint: disable=consider-using-with
                [browser, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    elif sys.platform == "win32":
        # ShellExecute via os.startfile brings the browser window to the foreground;
        # webbrowser.open() only flashes the taskbar when the browser is already running.
        os.startfile(url)  # noqa: S606  # nosec B606
    else:
        webbrowser.open(url)


def render_markdown_file(
    filepath: Path,
    output: Optional[Path] = None,
    open_browser: bool = True,
    keep_output: bool = False,
) -> Path:
    """
    Render a markdown file to HTML and optionally open in browser.

    Args:
        filepath: Path to the markdown file
        output: Optional output path for HTML file
        open_browser: Whether to open the result in browser
        keep_output: Whether to keep the output file (if not specified, uses temp file)

    Returns:
        Path to the generated HTML file
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Markdown file not found: {filepath}")

    # Read markdown content
    markdown_content = filepath.read_text(encoding="utf-8")

    # Process markdown
    processor = MarkdownProcessor()
    html_content = processor.process(markdown_content)

    # Embed local images as base64 data URIs so they load from a file:// URL
    html_content = _embed_local_images(html_content, filepath.parent)

    # Generate HTML
    html = HTML_TEMPLATE.format(
        title=filepath.stem,
        content=html_content,
        filename=filepath.name,
        filename_base=filepath.stem,
    )

    # Determine output file
    if output:
        output_path = output
    elif keep_output:
        output_path = filepath.with_suffix(".html")
    else:
        # Use temp file
        fd, temp_path = tempfile.mkstemp(suffix=".html", prefix="mdview-")
        os.close(fd)
        output_path = Path(temp_path)

    # Ensure absolute path for file URI
    output_path = output_path.resolve()

    # Write HTML file
    output_path.write_text(html, encoding="utf-8")

    # Open in browser
    if open_browser:
        webbrowser.open(output_path.as_uri())

    return output_path


def export_to_pdf(filepath: Path, output: Optional[Path] = None) -> Path:
    """
    Export markdown file to PDF.

    Args:
        filepath: Path to the markdown file
        output: Optional output path for PDF file

    Returns:
        Path to the generated PDF file
    """
    try:
        from .exporters.pdf_exporter import PDFExporter  # pylint: disable=import-outside-toplevel
    except ImportError as e:
        raise ImportError(
            "PDF export requires additional dependencies. "
            "Install with: pip install markdown-viewer[export] or poetry install -E export"
        ) from e

    # First render to HTML
    html_path = render_markdown_file(filepath, open_browser=False, keep_output=False)
    try:
        html_content = html_path.read_text(encoding="utf-8")
    finally:
        html_path.unlink(missing_ok=True)

    # Determine output path
    if output:
        # If the user passed a directory, place the file inside it
        pdf_path = output / filepath.with_suffix(".pdf").name if output.is_dir() else output
    else:
        # Auto-append timestamp to filename
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = filepath.parent / f"{filepath.stem}_{timestamp}.pdf"

    # Export to PDF
    exporter = PDFExporter()
    exporter.export(html_content, str(pdf_path), options={"base_path": str(filepath)})
    exporter.close()  # Properly close browser and playwright

    return pdf_path


def export_to_word(filepath: Path, output: Optional[Path] = None) -> Path:
    """
    Export markdown file to Word document.

    Args:
        filepath: Path to the markdown file
        output: Optional output path for Word file

    Returns:
        Path to the generated Word file
    """
    try:
        from .exporters.word_exporter import WordExporter  # pylint: disable=import-outside-toplevel
    except ImportError as e:
        raise ImportError(
            "Word export requires additional dependencies. "
            "Install with: pip install markdown-viewer[export] or poetry install -E export"
        ) from e

    # Read markdown content
    markdown_content = filepath.read_text(encoding="utf-8")

    # Process markdown to HTML for parsing
    processor = MarkdownProcessor()
    html_content = processor.process(markdown_content)

    # Determine output path
    if output:
        # If the user passed a directory, place the file inside it
        word_path = output / filepath.with_suffix(".docx").name if output.is_dir() else output
    else:
        # Auto-append timestamp to filename
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        word_path = filepath.parent / f"{filepath.stem}_{timestamp}.docx"

    # Export to Word
    exporter = WordExporter()
    exporter.export(html_content, markdown_content, str(word_path), md_file_path=str(filepath))

    return word_path


def share_via_email(filepath: Path, attachment_path: Path, file_type: str) -> None:
    """
    Open email client with attachment.

    Args:
        filepath: Original markdown file path
        attachment_path: Path to the attachment (PDF or Word)
        file_type: Type of file ('PDF' or 'Word')
    """
    # Email parameters
    subject = f"Sharing: {filepath.stem}"
    body = (
        f"Please find attached the {file_type} version of '{filepath.name}'."
        "\n\nGenerated by markdown-viewer."
    )

    # URL encode parameters
    subject_encoded = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body)

    # Construct mailto URL
    # Note: attachment parameter is not universally supported
    # Different email clients handle this differently
    mailto_url = f"mailto:?subject={subject_encoded}&body={body_encoded}"

    # Open email client
    webbrowser.open(mailto_url)

    # Print instructions
    print("\n📧 Email client opened!")
    print(f"📎 Please manually attach: {attachment_path.absolute()}")
    print("\nNote: The attachment couldn't be auto-attached due to email client limitations.")
    print("You can drag and drop the file into your email, or use the attach button.")


def main():  # pylint: disable=too-many-branches,too-many-statements,too-many-return-statements
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Markdown Viewer - Render markdown files beautifully in your browser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Open the file-picker dashboard (no file needed)
  mdview                              # Open dashboard in browser
  mdview --serve                      # Explicitly open the dashboard

  # Basic rendering
  mdview README.md                    # Render and open in browser
  mdview README.md -o output.html     # Save to specific file
  mdview README.md --no-browser       # Just render, don't open
  mdview README.md --keep             # Save as README.html

  # Export to PDF/Word
  mdview README.md --export-pdf       # Export to README.pdf
  mdview README.md --export-pdf report.pdf  # Export to specific file
  mdview README.md --export-word      # Export to README.docx
  mdview README.md --export-word doc.docx   # Export to specific file

  # Share via email
  mdview README.md --share-pdf        # Export and prepare email with PDF
  mdview README.md --share-word       # Export and prepare email with Word doc

  # CI/CD usage
  mdview docs/report.md --no-browser --keep
  mdview docs/report.md --export-pdf --export-word

  # Stop the background server
  mdview --stop                       # Stop the server running on the default port
  mdview --stop -p 5001               # Stop the server on a custom port
  mdview README.md -p 5001            # Open using a custom port

  # Choose a specific browser
  mdview README.md --browser firefox
  mdview README.md --browser chrome
  mdview README.md --browser msedge
  mdview README.md --browser iexplore
  mdview README.md --browser "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
        """,
    )

    parser.add_argument("file", nargs="?", type=str, help="Path to the markdown file to render")

    parser.add_argument(
        "-o", "--output", type=Path, help="Output HTML file path (default: temporary file)"
    )

    parser.add_argument(
        "--no-browser", action="store_true", help="Do not open the result in browser"
    )

    parser.add_argument(
        "--keep", action="store_true", help="Keep the output file (saves as <filename>.html)"
    )

    parser.add_argument(
        "--export-pdf",
        nargs="?",
        const=True,
        type=Path,
        metavar="OUTPUT",
        help="Export to PDF (optionally specify output path)",
    )

    parser.add_argument(
        "--export-word",
        nargs="?",
        const=True,
        type=Path,
        metavar="OUTPUT",
        help="Export to Word document (optionally specify output path)",
    )

    parser.add_argument(
        "--share-pdf", action="store_true", help="Export to PDF and open email client to share"
    )

    parser.add_argument(
        "--share-word", action="store_true", help="Export to Word and open email client to share"
    )

    parser.add_argument("--version", action="version", version=f"markdown-viewer {__version__}")

    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the running mdview background server and release the port",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=5000,
        metavar="PORT",
        help="Port for the background server (default: 5000)",
    )

    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the background server and open the file-picker dashboard in the browser",
    )

    parser.add_argument(
        "--browser",
        type=str,
        default=None,
        metavar="BROWSER",
        help=(
            "Browser to open (e.g. firefox, chrome, msedge, iexplore, safari, opera, brave). "
            "Accepts a browser name recognised by the Python webbrowser module or "
            "a full path to the browser executable. "
            "Defaults to the system default browser."
        ),
    )

    args = parser.parse_args()

    if args.stop:
        return _stop_server(port=args.port)

    # --serve explicitly requests the dashboard; file arg is not applicable with --serve
    if args.serve:
        if args.file is not None:
            print("Note: --serve opens the file-picker dashboard; the file argument is ignored.")
        _open_flask_dashboard(port=args.port, browser=args.browser)
        return 0

    # No file and no export operations: open the file-picker dashboard
    needs_file = args.export_pdf or args.export_word or args.share_pdf or args.share_word
    if args.file is None and not needs_file:
        if sys.stdout.isatty():
            _open_flask_dashboard(port=args.port, browser=args.browser)
            return 0
        # Non-interactive (CI/CD) with no file — print usage and fail
        print("Usage: mdview <file.md>")
        print("Example: mdview README.md")
        print("         mdview C:\\docs\\report.md")
        return 1

    # Resolve and validate — loop until a valid file is given (or user cancels)
    early_exit = _resolve_file(args)
    if early_exit is not None:
        return early_exit

    try:
        # Handle export to PDF
        if args.export_pdf or args.share_pdf:
            output_path = args.export_pdf if isinstance(args.export_pdf, Path) else None
            pdf_path = export_to_pdf(args.file, output=output_path)
            try:
                print(f"✅ Exported to PDF: {pdf_path}")
            except UnicodeEncodeError:
                print(f"Exported to PDF: {pdf_path}")

            if args.share_pdf:
                share_via_email(args.file, pdf_path, "PDF")

        # Handle export to Word
        if args.export_word or args.share_word:
            output_path = args.export_word if isinstance(args.export_word, Path) else None
            word_path = export_to_word(args.file, output=output_path)
            try:
                print(f"✅ Exported to Word: {word_path}")
            except UnicodeEncodeError:
                print(f"Exported to Word: {word_path}")

            if args.share_word:
                share_via_email(args.file, word_path, "Word")

        # Handle HTML rendering (only if not exclusively exporting/sharing)
        if not (args.export_pdf or args.export_word or args.share_pdf or args.share_word):
            if args.no_browser or args.output or args.keep:
                # Explicit offline/file-output mode: generate standalone HTML
                output_path = render_markdown_file(
                    filepath=args.file,
                    output=args.output,
                    open_browser=not args.no_browser,
                    keep_output=args.keep,
                )
                if args.no_browser:
                    print(f"✅ Rendered: {output_path}")
                else:
                    print(f"✅ Rendered and opened: {output_path}")
            elif not sys.stdout.isatty():
                # Non-interactive environment (CI/CD, pipe, redirect) — generate HTML without
                # spawning a background server or trying to open a browser.
                output_path = render_markdown_file(
                    filepath=args.file,
                    open_browser=False,
                    keep_output=True,
                )
                print(f"✅ Rendered: {output_path}")
            else:
                # Default interactive mode: open through the full Flask app
                _open_in_flask_app(args.file, port=args.port, browser=args.browser)

        return 0

    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 0
    except ImportError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback  # pylint: disable=import-outside-toplevel

        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
