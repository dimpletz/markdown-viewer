"""
Command-line interface for markdown viewer.
Render markdown files and open them in browser.
Export to PDF/Word and share via email.
"""

import sys
import argparse
import webbrowser
import tempfile
from pathlib import Path
from typing import Optional
import os
import urllib.parse

from markdown_viewer import __version__

from .processors.markdown_processor import MarkdownProcessor

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-color-mode="light" data-light-theme="light" data-dark-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.0/github-markdown-light.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github.min.css">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
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
            padding: 16px 20px;
            margin: 20px 0;
            font-size: 14px;
        }}
        .markdown-body .toc .toctitle,
        .markdown-body .toc span.toctitle {{
            display: block;
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 12px;
            color: #24292e;
        }}
        .markdown-body .toc ul {{
            list-style: none;
            padding-left: 0;
            margin: 8px 0;
        }}
        .markdown-body .toc > ul {{
            margin: 0;
        }}
        .markdown-body .toc ul ul {{
            padding-left: 20px;
            margin: 4px 0;
        }}
        .markdown-body .toc li {{
            margin: 4px 0;
            line-height: 1.5;
        }}
        .markdown-body .toc a {{
            color: #0969da;
            text-decoration: none;
            display: inline-block;
            padding: 2px 0;
        }}
        .markdown-body .toc a:hover {{
            color: #0550ae;
            text-decoration: underline;
        }}
        
        /* Permalink anchors */
        .markdown-body .headerlink {{
            color: #d0d7de;
            text-decoration: none;
            margin-left: 8px;
            font-size: 0.9em;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        .markdown-body h1:hover .headerlink,
        .markdown-body h2:hover .headerlink,
        .markdown-body h3:hover .headerlink,
        .markdown-body h4:hover .headerlink,
        .markdown-body h5:hover .headerlink,
        .markdown-body h6:hover .headerlink {{
            opacity: 1;
        }}
        .markdown-body .headerlink:hover {{
            color: #0969da;
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
            // Initialize Mermaid with proper configuration
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'default',
                securityLevel: 'strict',
                fontFamily: 'monospace'
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
            
            // Force Mermaid to render diagrams
            if (typeof mermaid !== 'undefined') {{
                try {{
                    mermaid.contentLoaded();
                }} catch (e) {{
                    console.error('Mermaid render error:', e);
                }}
            }}
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


def _open_in_flask_app(filepath: Path, port: int = 5000) -> None:
    """Start the Flask backend and open the file in the browser.

    If a server is already running on *port* it is reused, so the terminal
    returns immediately.  Otherwise a fully-detached background process is
    spawned (the terminal is still free after the browser opens).
    """
    import subprocess  # pylint: disable=import-outside-toplevel
    import time  # pylint: disable=import-outside-toplevel
    import urllib.request  # pylint: disable=import-outside-toplevel,redefined-outer-name

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
    server_already_running = False
    try:
        urllib.request.urlopen(  # pylint: disable=consider-using-with
            f"http://localhost:{port}/api/health", timeout=1
        )
        server_already_running = True
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    if not server_already_running:
        # Spawn a fully-detached background process so the terminal returns
        # immediately after the browser opens.
        env = os.environ.copy()
        env.setdefault("ALLOWED_DOCUMENTS_DIR", str(drive_root))

        server_cmd = [
            sys.executable,
            "-c",
            (
                "from markdown_viewer.server import run_flask_app;"
                f" run_flask_app(port={port}, use_reloader=True)"
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
            try:
                urllib.request.urlopen(  # pylint: disable=consider-using-with
                    f"http://localhost:{port}/api/health", timeout=1
                )
                server_ready = True
                break
            except Exception:  # pylint: disable=broad-exception-caught
                time.sleep(0.25)

        if not server_ready:
            print("❌ Server failed to start. Make sure all dependencies are installed.")
            print("   Try: pip install markdown-viewer-app")
            return

    url = f"http://localhost:{port}?file={urllib.parse.quote(str(abs_path))}"
    print(f"Opening {url}")
    webbrowser.open(url)
    # Terminal returns immediately — server keeps running in the background.


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
        pdf_path = output
    else:
        pdf_path = filepath.with_suffix(".pdf")

    # Export to PDF
    exporter = PDFExporter()
    exporter.export(html_content, str(pdf_path))
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
        word_path = output
    else:
        word_path = filepath.with_suffix(".docx")

    # Export to Word
    exporter = WordExporter()
    exporter.export(html_content, markdown_content, str(word_path))

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


def main():  # pylint: disable=too-many-branches,too-many-statements
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Markdown Viewer - Render markdown files beautifully in your browser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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
        """,
    )

    parser.add_argument("file", nargs="?", type=Path, help="Path to the markdown file to render")

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

    args = parser.parse_args()

    # If no file provided, show available markdown files and let user pick
    if args.file is None:
        md_files = sorted(
            [
                p
                for p in Path(".").rglob("*.md")
                if not any(part.startswith(".") for part in p.parts)
            ],
            key=lambda p: (len(p.parts), str(p)),
        )[
            :20
        ]  # cap at 20 to avoid flooding

        if md_files:
            print("No file specified. Markdown files found:")
            for i, f in enumerate(md_files, 1):
                print(f"  {i}. {f}")
            print()
        else:
            print("Usage: mdview <file.md>  |  Example: mdview README.md")
            return 1

    valid_extensions = (".md", ".markdown", ".mdown")

    # Resolve and validate — loop until a valid file is given
    while True:
        # If we have a file (from args or previous loop iteration), validate it
        if args.file is not None:
            if args.file.is_dir():
                print(f"'{args.file}' is a directory, not a file. Please enter a .md file.")
            elif not args.file.exists():
                print(f"'{args.file}' does not exist. Please enter another file.")
            elif args.file.suffix.lower() not in valid_extensions:
                ext = args.file.suffix or "(no extension)"
                print(
                    f"'{args.file.name}' has an unsupported extension ({ext})."
                    " Please provide a file with a .md extension."
                )
            else:
                break  # valid file — exit loop

        # Prompt for input (whether first time or after an error)
        try:
            choice = input("Enter a number or filename: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 0

        if not choice:
            print("No file entered. Please try again.")
            args.file = None
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if md_files and 0 <= idx < len(md_files):
                args.file = md_files[idx]
            else:
                bound = len(md_files) if md_files else 0
                print(f"Invalid number. Please enter 1–{bound}.")
                args.file = None
        else:
            args.file = Path(choice)

    try:
        # Handle export to PDF
        if args.export_pdf or args.share_pdf:
            output_path = args.export_pdf if isinstance(args.export_pdf, Path) else None
            pdf_path = export_to_pdf(args.file, output=output_path)
            print(f"✅ Exported to PDF: {pdf_path}")

            if args.share_pdf:
                share_via_email(args.file, pdf_path, "PDF")

        # Handle export to Word
        if args.export_word or args.share_word:
            output_path = args.export_word if isinstance(args.export_word, Path) else None
            word_path = export_to_word(args.file, output=output_path)
            print(f"✅ Exported to Word: {word_path}")

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
            else:
                # Default: open through the full Flask app — all features available
                _open_in_flask_app(args.file)

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
