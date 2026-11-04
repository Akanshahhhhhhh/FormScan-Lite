"""
translate_routes.py - POST /api/translate

Request (JSON):
    {"text": "Hello", "source_lang": "en", "target_lang": "ta"}     # codes: en, bn, ta

Success (200):
    {"translated_text": "...", "source_lang": "en", "target_lang": "ta", "model": "..."}

Error (same format as the other endpoints):
    {"error": "message", "code": "short_code"}
"""

from flask import Blueprint, jsonify, request

try:
    from services.translation_service import TranslationError, translate
except ImportError:  # fallback when imported as a package
    from ..services.translation_service import TranslationError, translate

translate_bp = Blueprint("translate", __name__)

# error code -> HTTP status
_STATUS = {
    "missing_text": 400,
    "text_too_long": 400,
    "unsupported_language": 400,
    "same_language": 400,
    "model_load_failed": 503,
    "translation_failed": 500,
}


@translate_bp.route("/api/translate", methods=["POST"])
def translate_text():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON body with text, source_lang and target_lang.",
                        "code": "bad_request"}), 400

    try:
        result = translate(
            data.get("text"),
            str(data.get("source_lang", "")).lower(),
            str(data.get("target_lang", "")).lower(),
        )
    except TranslationError as err:
        return jsonify({"error": err.message, "code": err.code}), _STATUS.get(err.code, 500)

    return jsonify(result), 200
