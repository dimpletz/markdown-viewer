"""
Flask application factory and configuration.
"""

import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
import uuid

from flask import Flask, g, jsonify, request, send_from_directory, Blueprint
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect


# Configuration classes
class Config:  # pylint: disable=too-few-public-methods
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    TEMP_FOLDER = os.path.join(os.path.dirname(__file__), "temp")
    # Default to filesystem root — the server only binds to 127.0.0.1 so
    # restricting by path adds no real security for a local desktop tool.
    ALLOWED_DOCUMENTS_DIR = os.environ.get(
        "ALLOWED_DOCUMENTS_DIR",
        str(pathlib.Path(pathlib.Path.home().anchor)),  # C:\ on Windows, / on Unix
    )

    # Security settings — server always binds to 127.0.0.1 over HTTP,
    # so SESSION_COOKIE_SECURE must be False (Secure flag is for HTTPS only).
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    WTF_CSRF_TIME_LIMIT = None  # CSRF token doesn't expire


class DevelopmentConfig(Config):  # pylint: disable=too-few-public-methods
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):  # pylint: disable=too-few-public-methods
    """Production configuration."""

    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,
}


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    if not app.debug:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/markdown_viewer.log", maxBytes=10485760, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] [%(pathname)s:%(lineno)d] %(message)s"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        # Also capture logs from all markdown_viewer sub-modules
        pkg_logger = logging.getLogger("markdown_viewer")
        pkg_logger.addHandler(file_handler)
        pkg_logger.setLevel(logging.INFO)
        app.logger.info("Markdown Viewer startup")


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:  # pylint: disable=too-many-locals
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Auto-generate an ephemeral SECRET_KEY if not explicitly set.
    # This server always binds to 127.0.0.1 only, so there is no session data
    # worth protecting across restarts. A persistent SECRET_KEY is only needed
    # when deploying as a shared/network-accessible server (set via env var).
    env = os.getenv("FLASK_ENV", "production")
    if not os.environ.get("SECRET_KEY") and (config is None or "SECRET_KEY" not in config):
        import secrets as _secrets  # pylint: disable=import-outside-toplevel

        os.environ["SECRET_KEY"] = _secrets.token_hex()

    # Load configuration
    try:
        app.config.from_object(config_by_name.get(env, config_by_name["default"]))
    except ValueError as e:
        # Re-raise configuration errors with clear message
        raise RuntimeError(f"Configuration error: {e}") from e

    # Config.SECRET_KEY is a class-level attribute evaluated at import time,
    # so if we auto-generated the key above we must push it into app.config now.
    if os.environ.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    # Apply custom configuration
    if config:
        app.config.update(config)

    # Configure logging
    configure_logging(app)

    # Enable CORS for Electron and local testing
    backend_port = os.environ.get("BACKEND_PORT", "5000")

    # In development, allow file:// and localhost origins
    if env == "development" or app.debug:
        cors_origins = "*"  # Allow all origins in development
    else:
        # In production, restrict to specific origins
        cors_origins = [
            f"http://localhost:{backend_port}",
            f"http://127.0.0.1:{backend_port}",
            "app://.",
        ]

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "X-CSRF-Token", "X-CSRFToken"],
                "expose_headers": ["Content-Type"],
                "supports_credentials": True,
                "max_age": 3600,
            }
        },
    )

    # Enable CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Ensure required temp directory exists
    os.makedirs(app.config["TEMP_FOLDER"], exist_ok=True)

    # Add request ID for tracing
    @app.before_request
    def add_request_id():
        g.request_id = str(uuid.uuid4())

    @app.after_request
    def log_request(response):
        request_id = getattr(g, "request_id", "unknown")
        app.logger.info(
            "[%s] %s %s %s", request_id, request.method, request.path, response.status_code
        )
        return response

    # Register blueprints
    from .routes import api_bp  # pylint: disable=import-outside-toplevel

    app.register_blueprint(api_bp, url_prefix="/api")

    # Serve the Electron renderer UI for browser mode
    renderer_dir = os.path.join(os.path.dirname(__file__), "electron", "renderer")
    ui_bp = Blueprint("ui", __name__)

    @ui_bp.route("/")
    def index():
        return send_from_directory(renderer_dir, "index.html")

    @ui_bp.route("/styles/<path:filename>")
    def renderer_styles(filename):
        return send_from_directory(os.path.join(renderer_dir, "styles"), filename)

    @ui_bp.route("/scripts/<path:filename>")
    def renderer_scripts(filename):
        return send_from_directory(os.path.join(renderer_dir, "scripts"), filename)

    app.register_blueprint(ui_bp)

    # Register error handlers
    from werkzeug.exceptions import HTTPException  # pylint: disable=import-outside-toplevel

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions with consistent format."""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": e.description, "type": e.name, "code": e.code},
                }
            ),
            e.code,
        )

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all other exceptions."""
        app.logger.error("Unhandled exception: %s", e, exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Internal server error", "type": "InternalServerError"},
                }
            ),
            500,
        )

    return app
