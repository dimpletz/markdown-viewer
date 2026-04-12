"""
API routes for markdown processing, export, and translation.
"""

# pylint: disable=broad-exception-caught

import os
import re
import mimetypes
import tempfile
import logging
import threading
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Tuple

from flask import Blueprint, request, jsonify, send_file, current_app, g
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.utils import secure_filename
from .processors.markdown_processor import MarkdownProcessor
from .exporters.pdf_exporter import PDFExporter
from .exporters.word_exporter import WordExporter
from .translators.content_translator import ContentTranslator
from .utils.file_handler import FileHandler

logger = logging.getLogger(__name__)


# Validation schemas
class RenderSchema(Schema):
    """Schema for markdown rendering request."""

    content = fields.Str(required=True, validate=validate.Length(max=10485760))  # 10MB max
    options = fields.Dict(keys=fields.Str(), values=fields.Raw(), required=False)


class FilePathSchema(Schema):
    """Schema for file path request."""

    path = fields.Str(required=True, validate=validate.Length(max=4096))


class ExportSchema(Schema):
    """Schema for export request."""

    html = fields.Str(required=True, validate=validate.Length(max=52428800))  # 50MB max
    markdown = fields.Str(required=False)
    filename = fields.Str(required=False, validate=validate.Length(max=255))


class TranslateSchema(Schema):
    """Schema for translation request."""

    content = fields.Str(required=True, validate=validate.Length(max=1048576))  # 1MB max
    source = fields.Str(required=False, validate=validate.Length(max=10))
    target = fields.Str(required=True, validate=validate.Length(max=10))


class DiagramSchema(Schema):
    """Schema for diagram transform request."""

    code = fields.Str(required=True, validate=validate.Length(max=1048576))
    type = fields.Str(
        required=False, validate=validate.OneOf(["mermaid", "plantuml"]), load_default="mermaid"
    )


class EmailShareSchema(Schema):
    """Schema for email share request."""

    html = fields.Str(required=True, validate=validate.Length(max=52428800))  # 50MB max
    subject = fields.Str(
        required=False, validate=validate.Length(max=200), load_default="Shared Document"
    )


api_bp = Blueprint("api", __name__)

# Initialize services (consider using dependency injection for better testability)
markdown_processor = MarkdownProcessor()
file_handler = FileHandler()

# Allowed image extensions for the /api/image endpoint
_ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}


def _rewrite_image_urls(html: str, base_dir: str) -> str:
    """Rewrite local image src attributes to /api/image?path=<encoded-abs-path> URLs.

    The browser fetches images via the Flask /api/image endpoint, which serves the
    file directly. Relative /api/image URLs pass DOMPurify's default URI allowlist
    without any configuration. Remote URLs and data URIs are left unchanged.
    """
    if not base_dir:
        return html

    base_path = Path(base_dir)

    def replace_src(match: re.Match) -> str:
        src = match.group(1)
        # Leave remote URLs, existing data URIs, and /api/image paths unchanged
        if src.startswith(
            ("http://", "https://", "data:", "ftp://", "file://", "mailto:", "/api/image")
        ):
            return match.group(0)

        # URL-decode first so %20 → space, backslash paths from markdown → real path
        src_decoded = urllib.parse.unquote(src)

        # Resolve to an absolute path; normalise backslashes for Windows paths
        if os.path.isabs(src_decoded):
            img_path = Path(src_decoded)
        else:
            src_normalized = src_decoded.replace("\\", "/")
            img_path = (base_path / src_normalized).resolve()

        if img_path.suffix.lower() not in _ALLOWED_IMAGE_EXTENSIONS:
            return match.group(0)

        # Encode the absolute path for use as a query parameter
        encoded = urllib.parse.quote(str(img_path), safe="")
        return f'src="/api/image?path={encoded}"'

    return re.sub(r'src="([^"]*)"', replace_src, html)


_ALLOWED_MD_EXTENSIONS = {".md", ".markdown", ".mdown"}


def _rewrite_md_links(html: str, base_dir: str) -> str:
    """Rewrite local markdown href links to /?file=<abs-path> viewer URLs.

    This ensures that clicking a relative link like [README](../README.md) opens
    the target file inside the viewer instead of returning a 404.
    Remote URLs and anchor-only links are left unchanged.
    """
    if not base_dir:
        return html

    base_path = Path(base_dir)

    def replace_href(match: re.Match) -> str:
        href = match.group(1)
        # Leave remote URLs, anchors, data URIs, and already-viewer URLs unchanged
        if href.startswith(("http://", "https://", "data:", "ftp://", "#", "/?file=", "/api/")):
            return match.group(0)

        href_decoded = urllib.parse.unquote(href)
        # Strip any fragment from the path before resolving
        fragment = ""
        if "#" in href_decoded:
            href_decoded, fragment = href_decoded.split("#", 1)
            fragment = "#" + fragment

        if os.path.isabs(href_decoded):
            md_path = Path(href_decoded)
        else:
            md_path = (base_path / href_decoded.replace("\\", "/")).resolve()

        if md_path.suffix.lower() not in _ALLOWED_MD_EXTENSIONS:
            return match.group(0)

        encoded = urllib.parse.quote(str(md_path), safe="")
        # Re-encode the fragment so special chars can't break out of the href attribute
        safe_fragment = "#" + urllib.parse.quote(fragment[1:], safe="-_.~") if fragment else ""
        return f'href="/?file={encoded}{safe_fragment}"'

    return re.sub(r'href="([^"]*)"', replace_href, html)


@api_bp.route("/test", methods=["GET"])
def test_page():
    """Serve the test interface page."""
    test_html_path = Path(__file__).parent.parent / "test.html"
    if test_html_path.exists():
        return send_file(test_html_path, mimetype="text/html")
    return jsonify({"error": "Test page not found"}), 404


@api_bp.route("/image", methods=["GET"])
def serve_image() -> Tuple[Any, int]:
    """Serve a local image file referenced by an absolute path.

    Security: path must resolve within ALLOWED_DOCUMENTS_DIR and must have
    a recognised image extension.
    """
    file_path = request.args.get("path", "").strip()
    if not file_path:
        return jsonify({"error": "No path provided"}), 400

    try:
        requested_path = Path(file_path).resolve()
    except (ValueError, OSError):
        return jsonify({"error": "Invalid path"}), 400

    # SECURITY: Restrict access to the allowed base directory
    allowed_base = Path(current_app.config.get("ALLOWED_DOCUMENTS_DIR", Path.home())).resolve()
    try:
        requested_path.relative_to(allowed_base)
    except ValueError:
        logger.warning("[%s] Image path traversal attempt: %s", g.request_id, requested_path)
        return jsonify({"error": "Access denied: path outside allowed directory"}), 403

    if not requested_path.exists() or not requested_path.is_file():
        return jsonify({"error": "Image not found"}), 404

    if requested_path.suffix.lower() not in _ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Unsupported image type"}), 400

    mime_type, _ = mimetypes.guess_type(str(requested_path))
    mime_type = mime_type or "application/octet-stream"

    logger.info("[%s] Serving image: %s", g.request_id, requested_path)
    return send_file(requested_path, mimetype=mime_type)


# Lazy initialization for resource-heavy services
def get_pdf_exporter() -> PDFExporter:
    """Get or create PDF exporter instance."""
    if "pdf_exporter" not in g:
        g.pdf_exporter = PDFExporter()
    return g.pdf_exporter


def get_word_exporter() -> WordExporter:
    """Get or create Word exporter instance."""
    if "word_exporter" not in g:
        g.word_exporter = WordExporter()
    return g.word_exporter


def get_translator() -> ContentTranslator:
    """Get or create translator instance."""
    if "translator" not in g:
        g.translator = ContentTranslator()
    return g.translator


@api_bp.teardown_app_request
def cleanup_resources(error=None):  # pylint: disable=unused-argument
    """Clean up resources after request."""
    # Clean up PDF exporter
    pdf_exporter = g.pop("pdf_exporter", None)
    if pdf_exporter is not None:
        try:
            if hasattr(pdf_exporter, "close"):
                pdf_exporter.close()
        except Exception as e:
            logger.warning("Error cleaning up PDF exporter: %s", e)

    # Clean up Word exporter
    word_exporter = g.pop("word_exporter", None)
    if word_exporter is not None:
        try:
            if hasattr(word_exporter, "close"):
                word_exporter.close()
        except Exception as e:
            logger.warning("Error cleaning up Word exporter: %s", e)

    # Clean up translator
    translator = g.pop("translator", None)
    if translator is not None:
        try:
            if hasattr(translator, "close"):
                translator.close()
        except Exception as e:
            logger.warning("Error cleaning up translator: %s", e)


@api_bp.route("/health", methods=["GET"])
def health_check() -> Tuple[Dict[str, Any], int]:
    """Health check endpoint with comprehensive checks."""
    checks = {
        "api": True,
        "disk_space": check_disk_space(),
        "temp_dir": os.path.exists(current_app.config.get("TEMP_FOLDER", "/tmp")),
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return (
        jsonify(
            {
                "status": "ok" if all_healthy else "degraded",
                "message": "Markdown Viewer API is running",
                "checks": checks,
                "capabilities": {"pdf_export": _check_playwright_available()},
            }
        ),
        status_code,
    )


def _check_playwright_available() -> bool:
    """Check if Playwright Chromium browser binary is installed."""
    try:
        from playwright.sync_api import sync_playwright  # pylint: disable=import-outside-toplevel

        with sync_playwright() as p:
            executable = p.chromium.executable_path
            return os.path.exists(executable)
    except Exception:
        return False


@api_bp.route("/shutdown", methods=["GET"])
def shutdown_server() -> Tuple[Dict[str, Any], int]:
    """Shut down the server process. Only reachable from localhost (127.0.0.1 binding)."""

    def _exit_after_response() -> None:
        import time  # pylint: disable=import-outside-toplevel

        time.sleep(0.4)  # Let the HTTP response flush before exiting
        os._exit(0)  # pylint: disable=protected-access

    threading.Thread(target=_exit_after_response, daemon=True).start()
    return jsonify({"success": True, "message": "Server shutting down"}), 200


@api_bp.route("/csrf", methods=["GET"])
def get_csrf_token() -> Tuple[Dict[str, Any], int]:
    """Get CSRF token for JavaScript requests."""
    from flask_wtf.csrf import generate_csrf  # pylint: disable=import-outside-toplevel

    return jsonify({"csrf_token": generate_csrf()}), 200


def check_disk_space() -> bool:
    """Check if sufficient disk space is available (cross-platform)."""
    import shutil  # pylint: disable=import-outside-toplevel

    try:
        temp_folder = current_app.config.get("TEMP_FOLDER", os.path.expanduser("~"))
        usage = shutil.disk_usage(temp_folder)
        return usage.free > 100 * 1024 * 1024  # At least 100MB free
    except OSError:
        return True


@api_bp.route("/render", methods=["POST"])
def render_markdown() -> Tuple[Dict[str, Any], int]:
    """Render markdown content to HTML."""
    try:
        # Validate input
        schema = RenderSchema()
        data = schema.load(request.get_json(silent=True) or {})

        markdown_content = data.get("content", "")
        options = data.get("options", {})
        # Strip any processor-internal keys the client may have supplied to prevent injection
        options.pop("base_dir", None)
        options.pop("allowed_base", None)
        base_path = options.get("basePath", "")
        if base_path:
            options["base_dir"] = base_path
            allowed_base = Path(
                current_app.config.get("ALLOWED_DOCUMENTS_DIR", Path.home())
            ).resolve()
            options["allowed_base"] = str(allowed_base)

        logger.info("[%s] Rendering markdown, size: %s bytes", g.request_id, len(markdown_content))

        html_content = markdown_processor.process(markdown_content, options)

        if base_path:
            html_content = _rewrite_image_urls(html_content, base_path)
            html_content = _rewrite_md_links(html_content, base_path)

        return jsonify({"success": True, "html": html_content}), 200

    except ValidationError as e:
        logger.warning("[%s] Validation error: %s", g.request_id, e.messages)
        return (
            jsonify(
                {"success": False, "error": {"message": "Invalid input", "details": e.messages}}
            ),
            400,
        )
    except ValueError as e:
        logger.warning("[%s] Value error: %s", g.request_id, e)
        return jsonify({"success": False, "error": {"message": str(e)}}), 400
    except Exception as e:
        logger.error("[%s] Error rendering markdown: %s", g.request_id, e, exc_info=True)
        return jsonify({"success": False, "error": {"message": "Internal server error"}}), 500


@api_bp.route("/file/open", methods=["POST"])
def open_file() -> Tuple[Dict[str, Any], int]:  # pylint: disable=too-many-return-statements
    """Open and render a markdown file with path traversal protection."""
    try:
        # Validate input
        schema = FilePathSchema()
        data = schema.load(request.get_json(silent=True) or {})
        file_path = data.get("path", "")

        # Resolve to absolute path and validate
        requested_path = Path(file_path).resolve()

        # SECURITY: Restrict file access to allowed base directory
        allowed_base = Path(current_app.config.get("ALLOWED_DOCUMENTS_DIR", Path.home())).resolve()
        try:
            requested_path.relative_to(allowed_base)
        except ValueError:
            logger.warning("[%s] Path traversal attempt: %s", g.request_id, requested_path)
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"message": "Access denied: path outside allowed directory"},
                    }
                ),
                403,
            )

        if not requested_path.exists():
            logger.warning("[%s] File not found: %s", g.request_id, requested_path)
            return jsonify({"success": False, "error": {"message": "File not found"}}), 404

        # Check if it's actually a file
        if not requested_path.is_file():
            logger.warning("[%s] Not a file: %s", g.request_id, requested_path)
            return jsonify({"success": False, "error": {"message": "Path is not a file"}}), 400

        logger.info("[%s] Opening file: %s", g.request_id, requested_path)
        content = file_handler.read_file(str(requested_path))
        base_dir = str(requested_path.parent)
        html_content = markdown_processor.process(
            content,
            {
                "base_dir": base_dir,
                "allowed_base": str(allowed_base),
            },
        )
        html_content = _rewrite_image_urls(html_content, base_dir)
        html_content = _rewrite_md_links(html_content, base_dir)

        return (
            jsonify(
                {
                    "success": True,
                    "content": content,
                    "html": html_content,
                    "path": str(requested_path),
                }
            ),
            200,
        )

    except ValidationError as e:
        logger.warning("[%s] Validation error: %s", g.request_id, e.messages)
        return (
            jsonify(
                {"success": False, "error": {"message": "Invalid input", "details": e.messages}}
            ),
            400,
        )
    except FileNotFoundError as e:
        logger.warning("[%s] File not found: %s", g.request_id, e)
        return jsonify({"success": False, "error": {"message": "File not found"}}), 404
    except ValueError as e:
        logger.warning("[%s] Value error: %s", g.request_id, e)
        return jsonify({"success": False, "error": {"message": str(e)}}), 400
    except Exception as e:
        logger.error("[%s] Error opening file: %s", g.request_id, e, exc_info=True)
        return jsonify({"success": False, "error": {"message": "Internal server error"}}), 500


@api_bp.route("/export/pdf", methods=["POST"])
def export_pdf() -> Tuple[Dict[str, Any], int]:
    """Export rendered HTML to PDF with proper cleanup."""
    pdf_path = None
    pdf_exporter = None
    try:
        # Validate input
        schema = ExportSchema()
        data = schema.load(request.get_json(silent=True) or {})

        html_content = data.get("html", "")
        filename = data.get("filename", "document.pdf")

        # Sanitize filename to prevent path traversal
        filename = secure_filename(filename)
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        logger.info("[%s] Exporting PDF: %s", g.request_id, filename)

        # Create temporary PDF with automatic cleanup
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        # Use explicit resource management
        pdf_exporter = get_pdf_exporter()
        pdf_exporter.export(html_content, pdf_path)

        # Send file and schedule cleanup after sending
        response = send_file(
            pdf_path, as_attachment=True, download_name=filename, mimetype="application/pdf"
        )

        # Clean up temp file after response
        @response.call_on_close
        def cleanup():
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.unlink(pdf_path)
                except OSError as e:
                    logger.warning("Failed to delete temp file %s: %s", pdf_path, e)

        return response

    except ValidationError as e:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except OSError:
                pass  # Best effort cleanup
        logger.warning("[%s] Validation error: %s", g.request_id, e.messages)
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Invalid input",
                        "type": "ValidationError",
                        "details": e.messages,
                    },
                }
            ),
            400,
        )
    except Exception as e:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except OSError:
                pass  # Best effort cleanup
        logger.error("[%s] Error exporting PDF: %s", g.request_id, e, exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Internal server error", "type": type(e).__name__},
                }
            ),
            500,
        )


@api_bp.route("/export/word", methods=["POST"])
def export_word() -> Tuple[Dict[str, Any], int]:
    """Export content to Word document with proper cleanup."""
    docx_path = None
    try:
        # Validate input
        schema = ExportSchema()
        data = schema.load(request.get_json(silent=True) or {})

        html_content = data.get("html", "")
        markdown_content = data.get("markdown", "")
        filename = data.get("filename", "document.docx")

        # Sanitize filename to prevent path traversal
        filename = secure_filename(filename)
        if not filename.endswith(".docx"):
            filename += ".docx"

        logger.info("[%s] Exporting Word: %s", g.request_id, filename)

        # Create temporary Word document
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            docx_path = tmp.name

        word_exporter = get_word_exporter()
        word_exporter.export(html_content, markdown_content, docx_path)

        response = send_file(
            docx_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        # Clean up temp file after response
        @response.call_on_close
        def cleanup():
            if docx_path and os.path.exists(docx_path):
                try:
                    os.unlink(docx_path)
                except OSError as e:
                    logger.warning("Failed to delete temp file %s: %s", docx_path, e)

        return response

    except ValidationError as e:
        if docx_path and os.path.exists(docx_path):
            try:
                os.unlink(docx_path)
            except OSError:
                pass  # Best effort cleanup
        logger.warning("[%s] Validation error: %s", g.request_id, e.messages)
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Invalid input",
                        "type": "ValidationError",
                        "details": e.messages,
                    },
                }
            ),
            400,
        )
    except Exception as e:
        if docx_path and os.path.exists(docx_path):
            try:
                os.unlink(docx_path)
            except OSError:
                pass  # Best effort cleanup
        logger.error("[%s] Error exporting Word: %s", g.request_id, e, exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Internal server error", "type": type(e).__name__},
                }
            ),
            500,
        )


@api_bp.route("/translate", methods=["POST"])
def translate_content() -> Tuple[Dict[str, Any], int]:
    """Translate markdown content with validation."""
    try:
        # Validate input
        schema = TranslateSchema()
        data = schema.load(request.get_json(silent=True) or {})

        content = data.get("content", "")
        source_lang = data.get("source", "auto")
        target_lang = data.get("target", "en")

        logger.info("[%s] Translating from %s to %s", g.request_id, source_lang, target_lang)

        translator = get_translator()

        # Validate language codes
        supported = translator.get_supported_languages()
        if target_lang not in supported and target_lang != "auto":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "message": f"Unsupported target language: {target_lang}",
                            "supported": list(supported.keys()),
                        },
                    }
                ),
                400,
            )

        translated = translator.translate(content, source_lang, target_lang)

        return jsonify({"success": True, "translated": translated}), 200

    except ValidationError as e:
        logger.warning("[%s] Validation error: %s", g.request_id, e.messages)
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Invalid input",
                        "type": "ValidationError",
                        "details": e.messages,
                    },
                }
            ),
            400,
        )
    except (ValueError, TimeoutError) as e:
        logger.warning("[%s] Translate error: %s", g.request_id, e)
        return (
            jsonify({"success": False, "error": {"message": str(e), "type": type(e).__name__}}),
            400,
        )
    except Exception as e:
        req_id = getattr(g, "request_id", "unknown")
        logger.error("[%s] Error translating: %s", req_id, e, exc_info=True)
        return (
            jsonify({"success": False, "error": {"message": "Internal server error"}}),
            500,
        )


@api_bp.route("/transform/diagram", methods=["POST"])
def transform_diagram():
    """Transform diagram code (mermaid, plantuml) to image."""
    try:
        schema = DiagramSchema()
        schema.load(request.get_json(silent=True) or {})
        # Diagram rendering is handled client-side; server acknowledges the request
        return jsonify(
            {"success": True, "message": "Diagram transformation supported on client-side"}
        )
    except ValidationError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Invalid input",
                        "type": "ValidationError",
                        "details": e.messages,
                    },
                }
            ),
            400,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/email/share", methods=["POST"])
def share_via_email():
    """Prepare content for email sharing."""
    try:
        schema = EmailShareSchema()
        data = schema.load(request.get_json(silent=True) or {})
        subject = data.get("subject", "Shared Document")

        mailto_link = f"mailto:?subject={subject}&body=Please see attached document"

        return jsonify({"success": True, "mailto": mailto_link})
    except ValidationError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Invalid input",
                        "type": "ValidationError",
                        "details": e.messages,
                    },
                }
            ),
            400,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
