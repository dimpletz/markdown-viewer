"""
API routes for markdown processing, export, and translation.
"""

from flask import Blueprint, request, jsonify, send_file, current_app, g
from pathlib import Path
import os
import tempfile
import logging
from typing import Dict, Any, Tuple
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
        required=False,
        validate=validate.OneOf(["mermaid", "plantuml"]),
        load_default="mermaid"
    )


class EmailShareSchema(Schema):
    """Schema for email share request."""
    html = fields.Str(required=True, validate=validate.Length(max=52428800))  # 50MB max
    subject = fields.Str(required=False, validate=validate.Length(max=200), load_default="Shared Document")

api_bp = Blueprint("api", __name__)

# Initialize services (consider using dependency injection for better testability)
markdown_processor = MarkdownProcessor()
file_handler = FileHandler()


@api_bp.route('/test', methods=['GET'])
def test_page():
    """Serve the test interface page."""
    test_html_path = Path(__file__).parent.parent / 'test.html'
    if test_html_path.exists():
        return send_file(test_html_path, mimetype='text/html')
    return jsonify({"error": "Test page not found"}), 404


# Lazy initialization for resource-heavy services
def get_pdf_exporter() -> PDFExporter:
    """Get or create PDF exporter instance."""
    if 'pdf_exporter' not in g:
        g.pdf_exporter = PDFExporter()
    return g.pdf_exporter


def get_word_exporter() -> WordExporter:
    """Get or create Word exporter instance."""
    if 'word_exporter' not in g:
        g.word_exporter = WordExporter()
    return g.word_exporter


def get_translator() -> ContentTranslator:
    """Get or create translator instance."""
    if 'translator' not in g:
        g.translator = ContentTranslator()
    return g.translator


@api_bp.teardown_app_request
def cleanup_resources(error=None):
    """Clean up resources after request."""
    # Clean up PDF exporter
    pdf_exporter = g.pop('pdf_exporter', None)
    if pdf_exporter is not None:
        try:
            if hasattr(pdf_exporter, 'close'):
                pdf_exporter.close()
        except Exception as e:
            logger.warning(f"Error cleaning up PDF exporter: {e}")
    
    # Clean up Word exporter
    word_exporter = g.pop('word_exporter', None)
    if word_exporter is not None:
        try:
            if hasattr(word_exporter, 'close'):
                word_exporter.close()
        except Exception as e:
            logger.warning(f"Error cleaning up Word exporter: {e}")
    
    # Clean up translator
    translator = g.pop('translator', None)
    if translator is not None:
        try:
            if hasattr(translator, 'close'):
                translator.close()
        except Exception as e:
            logger.warning(f"Error cleaning up translator: {e}")


@api_bp.route("/health", methods=["GET"])
def health_check() -> Tuple[Dict[str, Any], int]:
    """Health check endpoint with comprehensive checks."""
    checks = {
        "api": True,
        "disk_space": check_disk_space(),
        "temp_dir": os.path.exists(current_app.config.get('TEMP_FOLDER', '/tmp'))
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        "status": "ok" if all_healthy else "degraded",
        "message": "Markdown Viewer API is running",
        "checks": checks,
        "capabilities": {
            "pdf_export": _check_playwright_available()
        }
    }), status_code


def _check_playwright_available() -> bool:
    """Check if Playwright Chromium browser binary is installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            executable = p.chromium.executable_path
            return os.path.exists(executable)
    except Exception:
        return False


@api_bp.route("/csrf", methods=["GET"])
def get_csrf_token() -> Tuple[Dict[str, Any], int]:
    """Get CSRF token for JavaScript requests."""
    from flask_wtf.csrf import generate_csrf
    return jsonify({
        "csrf_token": generate_csrf()
    }), 200


def check_disk_space() -> bool:
    """Check if sufficient disk space is available (cross-platform)."""
    import shutil
    try:
        temp_folder = current_app.config.get('TEMP_FOLDER', os.path.expanduser('~'))
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
        
        logger.info(f"[{g.request_id}] Rendering markdown, size: {len(markdown_content)} bytes")
        
        html_content = markdown_processor.process(markdown_content, options)
        
        return jsonify({
            "success": True,
            "html": html_content
        }), 200
        
    except ValidationError as e:
        logger.warning(f"[{g.request_id}] Validation error: {e.messages}")
        return jsonify({
            "success": False,
            "error": {
                "message": "Invalid input",
                "details": e.messages
            }
        }), 400
    except ValueError as e:
        logger.warning(f"[{g.request_id}] Value error: {e}")
        return jsonify({
            "success": False,
            "error": {"message": str(e)}
        }), 400
    except Exception as e:
        logger.error(f"[{g.request_id}] Error rendering markdown: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": "Internal server error"}
        }), 500


@api_bp.route("/file/open", methods=["POST"])
def open_file() -> Tuple[Dict[str, Any], int]:
    """Open and render a markdown file with path traversal protection."""
    try:
        # Validate input
        schema = FilePathSchema()
        data = schema.load(request.get_json(silent=True) or {})
        file_path = data.get("path", "")
        
        # Resolve to absolute path and validate
        requested_path = Path(file_path).resolve()
        
        # SECURITY: Restrict file access to allowed base directory
        allowed_base = Path(current_app.config.get('ALLOWED_DOCUMENTS_DIR', Path.home())).resolve()
        try:
            requested_path.relative_to(allowed_base)
        except ValueError:
            logger.warning(f"[{g.request_id}] Path traversal attempt: {requested_path}")
            return jsonify({
                "success": False,
                "error": {"message": "Access denied: path outside allowed directory"}
            }), 403
        
        if not requested_path.exists():
            logger.warning(f"[{g.request_id}] File not found: {requested_path}")
            return jsonify({
                "success": False,
                "error": {"message": "File not found"}
            }), 404
        
        # Check if it's actually a file
        if not requested_path.is_file():
            logger.warning(f"[{g.request_id}] Not a file: {requested_path}")
            return jsonify({
                "success": False,
                "error": {"message": "Path is not a file"}
            }), 400
        
        logger.info(f"[{g.request_id}] Opening file: {requested_path}")
        content = file_handler.read_file(str(requested_path))
        html_content = markdown_processor.process(content)
        
        return jsonify({
            "success": True,
            "content": content,
            "html": html_content,
            "path": str(requested_path)
        }), 200
        
    except ValidationError as e:
        logger.warning(f"[{g.request_id}] Validation error: {e.messages}")
        return jsonify({
            "success": False,
            "error": {"message": "Invalid input", "details": e.messages}
        }), 400
    except FileNotFoundError as e:
        logger.warning(f"[{g.request_id}] File not found: {e}")
        return jsonify({
            "success": False,
            "error": {"message": "File not found"}
        }), 404
    except ValueError as e:
        logger.warning(f"[{g.request_id}] Value error: {e}")
        return jsonify({
            "success": False,
            "error": {"message": str(e)}
        }), 400
    except Exception as e:
        logger.error(f"[{g.request_id}] Error opening file: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": "Internal server error"}
        }), 500


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
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        logger.info(f"[{g.request_id}] Exporting PDF: {filename}")
        
        # Create temporary PDF with automatic cleanup
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name
        
        # Use explicit resource management
        pdf_exporter = get_pdf_exporter()
        pdf_exporter.export(html_content, pdf_path)
        
        # Send file and schedule cleanup after sending
        response = send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )
        
        # Clean up temp file after response
        @response.call_on_close
        def cleanup():
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.unlink(pdf_path)
                except OSError as e:
                    logger.warning(f"Failed to delete temp file {pdf_path}: {e}")
        
        return response
        
    except ValidationError as e:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except OSError:
                pass  # Best effort cleanup
        logger.warning(f"[{g.request_id}] Validation error: {e.messages}")
        return jsonify({
            "success": False,
            "error": {"message": "Invalid input", "type": "ValidationError", "details": e.messages}
        }), 400
    except Exception as e:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except OSError:
                pass  # Best effort cleanup
        logger.error(f"[{g.request_id}] Error exporting PDF: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": "Internal server error", "type": type(e).__name__}
        }), 500


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
        if not filename.endswith('.docx'):
            filename += '.docx'
        
        logger.info(f"[{g.request_id}] Exporting Word: {filename}")
        
        # Create temporary Word document
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            docx_path = tmp.name
        
        word_exporter = get_word_exporter()
        word_exporter.export(html_content, markdown_content, docx_path)
        
        response = send_file(
            docx_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # Clean up temp file after response
        @response.call_on_close
        def cleanup():
            if docx_path and os.path.exists(docx_path):
                try:
                    os.unlink(docx_path)
                except OSError as e:
                    logger.warning(f"Failed to delete temp file {docx_path}: {e}")
        
        return response
        
    except ValidationError as e:
        if docx_path and os.path.exists(docx_path):
            try:
                os.unlink(docx_path)
            except OSError:
                pass  # Best effort cleanup
        logger.warning(f"[{g.request_id}] Validation error: {e.messages}")
        return jsonify({
            "success": False,
            "error": {"message": "Invalid input", "type": "ValidationError", "details": e.messages}
        }), 400
    except Exception as e:
        if docx_path and os.path.exists(docx_path):
            try:
                os.unlink(docx_path)
            except OSError:
                pass  # Best effort cleanup
        logger.error(f"[{g.request_id}] Error exporting Word: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": "Internal server error", "type": type(e).__name__}
        }), 500


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
        
        logger.info(f"[{g.request_id}] Translating from {source_lang} to {target_lang}")
        
        translator = get_translator()
        
        # Validate language codes
        supported = translator.get_supported_languages()
        if target_lang not in supported and target_lang != 'auto':
            return jsonify({
                "success": False,
                "error": {
                    "message": f"Unsupported target language: {target_lang}",
                    "supported": list(supported.keys())
                }
            }), 400
        
        translated = translator.translate(content, source_lang, target_lang)
        
        return jsonify({
            "success": True,
            "translated": translated
        }), 200
        
    except ValidationError as e:
        logger.warning(f"[{g.request_id}] Validation error: {e.messages}")
        return jsonify({
            "success": False,
            "error": {"message": "Invalid input", "type": "ValidationError", "details": e.messages}
        }), 400
    except (ValueError, TimeoutError) as e:
        logger.warning(f"[{g.request_id}] Translate error: {e}")
        return jsonify({
            "success": False,
            "error": {"message": str(e), "type": type(e).__name__}
        }), 400
    except Exception as e:
        req_id = getattr(g, 'request_id', 'unknown')
        logger.error(f"[{req_id}] Error translating: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {"message": str(e), "type": type(e).__name__}
        }), 500


@api_bp.route("/transform/diagram", methods=["POST"])
def transform_diagram():
    """Transform diagram code (mermaid, plantuml) to image."""
    try:
        schema = DiagramSchema()
        data = schema.load(request.get_json(silent=True) or {})
        # Diagram rendering is handled client-side; server acknowledges the request
        return jsonify({
            "success": True,
            "message": "Diagram transformation supported on client-side"
        })
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": {"message": "Invalid input", "type": "ValidationError", "details": e.messages}
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/email/share", methods=["POST"])
def share_via_email():
    """Prepare content for email sharing."""
    try:
        schema = EmailShareSchema()
        data = schema.load(request.get_json(silent=True) or {})
        subject = data.get("subject", "Shared Document")
        
        mailto_link = f"mailto:?subject={subject}&body=Please see attached document"
        
        return jsonify({
            "success": True,
            "mailto": mailto_link
        })
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": {"message": "Invalid input", "type": "ValidationError", "details": e.messages}
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
