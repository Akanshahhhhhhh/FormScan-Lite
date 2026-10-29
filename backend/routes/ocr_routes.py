import logging
import os
import uuid

from flask import Blueprint, jsonify, request
from PIL import Image

from services.ocr_service import SUPPORTED_LANGUAGES, extract_text

logger = logging.getLogger(__name__)

ocr_bp = Blueprint('ocr', __name__)

UPLOAD_FOLDER = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

STATUS = {
    'no_image': 400,
    'missing_language': 400,
    'unsupported_language': 400,
    'empty_filename': 400,
    'unsupported_file_type': 400,
    'invalid_image': 400,
    'file_too_large': 413,
    'ocr_failed': 500,
}


def error(code, message):
    return jsonify({'error': message, 'code': code}), STATUS[code]


@ocr_bp.route('/api/ocr', methods=['POST'])
def ocr_endpoint():
    if 'image' not in request.files:
        return error('no_image', 'No image file provided')

    file = request.files['image']
    language = (request.form.get('language') or '').strip().lower()

    if not language:
        return error('missing_language', "Missing 'language' field (use 'bn', 'ta', or 'en')")
    if language not in SUPPORTED_LANGUAGES:
        return error('unsupported_language', "Language must be 'bn', 'ta' or 'en'")
    if file.filename == '':
        return error('empty_filename', 'Empty filename')

    # Use the extension only (the original name may be Bengali/Tamil letters).
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return error('unsupported_file_type', 'Only png, jpg and jpeg images are allowed')

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_BYTES:
        return error('file_too_large', 'Image is too big. Maximum size is 10 MB')

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Random name: two people uploading "form.jpg" never overwrite each other.
    filepath = os.path.join(UPLOAD_FOLDER, f'{uuid.uuid4().hex}{ext}')
    file.save(filepath)

    try:
        try:
            with Image.open(filepath) as img:
                img.verify()
        except Exception:
            return error('invalid_image', 'This file is not a valid image')

        try:
            result = extract_text(filepath, language)
            return jsonify(result), 200
        except ValueError as exc:
            return error('unsupported_language', str(exc))
        except Exception:
            logger.exception('OCR failed (%s)', language)
            return error('ocr_failed', 'OCR processing failed. Please try another image.')
    finally:
        # Government forms are private: do not keep the photo after reading it.
        try:
            os.remove(filepath)
        except OSError:
            pass
