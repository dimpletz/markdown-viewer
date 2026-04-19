"""
Flask blueprint for the favourites API.

Endpoints:
  GET    /api/favourites             – list all
  GET    /api/favourites/search?q=   – FTS5/LIKE search
  GET    /api/favourites/check?path= – check if path is a favourite
  POST   /api/favourites             – add (with path traversal guard)
  PUT    /api/favourites/<id>        – update name / tags
  DELETE /api/favourites/<id>        – remove
"""

# pylint: disable=broad-exception-caught

import logging
import sqlite3
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request
from marshmallow import Schema, ValidationError, fields, validate

from .db import favourites_repo as repo

logger = logging.getLogger(__name__)

favourites_bp = Blueprint("favourites", __name__)


# ---------------------------------------------------------------------------
# Marshmallow schemas
# ---------------------------------------------------------------------------


class AddFavouriteSchema(Schema):
    path = fields.Str(required=True, validate=validate.Length(min=1, max=4096))


class UpdateFavouriteSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    tags = fields.List(
        fields.Str(validate=validate.Length(min=1, max=100)),
        validate=validate.Length(max=20),
    )


class SearchSchema(Schema):
    q = fields.Str(required=True, validate=validate.Length(min=1, max=200))


# ---------------------------------------------------------------------------
# Helper: path traversal guard (mirrors the /api/image guard in routes.py)
# ---------------------------------------------------------------------------


def _check_path_allowed(file_path: str) -> bool:
    """Return True if *file_path* is within ALLOWED_DOCUMENTS_DIR."""
    try:
        requested = Path(file_path).resolve()
    except (ValueError, OSError):
        return False
    allowed_base = Path(current_app.config.get("ALLOWED_DOCUMENTS_DIR", Path.home())).resolve()
    try:
        requested.relative_to(allowed_base)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@favourites_bp.route("/favourites", methods=["GET"])
def list_favourites():
    """Return all favourites."""
    try:
        items = repo.list_all()
        return jsonify({"success": True, "data": items})
    except Exception as exc:
        logger.error("[%s] list_favourites error: %s", getattr(g, "request_id", "-"), exc)
        return jsonify({"success": False, "error": {"message": str(exc)}}), 500


@favourites_bp.route("/favourites/search", methods=["GET"])
def search_favourites():
    """Search favourites (FTS5 / LIKE fallback). Returns max 20."""
    schema = SearchSchema()
    try:
        data = schema.load(request.args)
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Validation error", "details": err.messages},
                }
            ),
            400,
        )
    try:
        items = repo.search(data["q"])
        return jsonify({"success": True, "data": items})
    except Exception as exc:
        logger.error("[%s] search_favourites error: %s", getattr(g, "request_id", "-"), exc)
        return jsonify({"success": False, "error": {"message": str(exc)}}), 500


@favourites_bp.route("/favourites/check", methods=["GET"])
def check_favourite():
    """Return {is_favourite, id|null} for the given path query param."""
    file_path = request.args.get("path", "").strip()
    if not file_path:
        return jsonify({"success": False, "error": {"message": "path is required"}}), 400
    try:
        result = repo.check_by_path(file_path)
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        logger.error("[%s] check_favourite error: %s", getattr(g, "request_id", "-"), exc)
        return jsonify({"success": False, "error": {"message": str(exc)}}), 500


@favourites_bp.route("/favourites", methods=["POST"])
def add_favourite():
    """Add a new favourite. Applies path-traversal guard."""
    schema = AddFavouriteSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Validation error", "details": err.messages},
                }
            ),
            400,
        )

    file_path = data["path"]

    # S1 — path traversal protection
    if not _check_path_allowed(file_path):
        logger.warning(
            "[%s] Favourite path traversal attempt: %s",
            getattr(g, "request_id", "-"),
            file_path,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Access denied: path outside allowed directory"},
                }
            ),
            403,
        )

    try:
        item = repo.add(file_path)
        return jsonify({"success": True, "data": item}), 201
    except ValueError as exc:
        return jsonify({"success": False, "error": {"message": str(exc)}}), 400
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": {"message": "Already a favourite"}}), 409
    except Exception as exc:
        logger.error("[%s] add_favourite error: %s", getattr(g, "request_id", "-"), exc)
        return jsonify({"success": False, "error": {"message": str(exc)}}), 500


@favourites_bp.route("/favourites/<int:favourite_id>", methods=["PUT"])
def update_favourite(favourite_id: int):
    """Update name and/or tags for a favourite."""
    schema = UpdateFavouriteSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Validation error", "details": err.messages},
                }
            ),
            400,
        )

    try:
        item = repo.update(
            favourite_id,
            name=data.get("name"),
            tags=data.get("tags"),
        )
        return jsonify({"success": True, "data": item})
    except ValueError as exc:
        return jsonify({"success": False, "error": {"message": str(exc)}}), 404
    except Exception as exc:
        logger.error("[%s] update_favourite error: %s", getattr(g, "request_id", "-"), exc)
        return jsonify({"success": False, "error": {"message": str(exc)}}), 500


@favourites_bp.route("/favourites/<int:favourite_id>", methods=["DELETE"])
def delete_favourite(favourite_id: int):
    """Delete a favourite. Returns 404 if not found."""
    try:
        deleted = repo.delete(favourite_id)
        if not deleted:
            return jsonify({"success": False, "error": {"message": "Favourite not found"}}), 404
        return jsonify({"success": True})
    except Exception as exc:
        logger.error("[%s] delete_favourite error: %s", getattr(g, "request_id", "-"), exc)
        return jsonify({"success": False, "error": {"message": str(exc)}}), 500
