import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from services.ocr_service import extract_text

ocr_bp = Blueprint('ocr', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')

@ocr_bp.route('/api/ocr', methods=['POST'])
def ocr_endpoint():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    language = request.form.get('language')

    if not language:
        return jsonify({"error": "Missing 'language' field (use 'bn', 'ta', or 'en')"}), 400

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        result = extract_text(filepath, language)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"OCR processing failed: {str(e)}"}), 500