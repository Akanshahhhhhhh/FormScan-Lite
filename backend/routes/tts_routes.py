import os
import re

from flask import Blueprint, jsonify, request, send_from_directory

from services.tts_service import AUDIO_DIR, TTSError, generate_audio

tts_bp = Blueprint('tts', __name__)

STATUS = {
    'bad_request': 400,
    'missing_text': 400,
    'text_too_long': 400,
    'unsupported_language': 400,
    'no_speakable_text': 400,
    'tts_failed': 503,
}

FILENAME_RE = re.compile(r'^[a-f0-9]{32}\.mp3$')


@tts_bp.route('/api/tts', methods=['POST'])
def create_audio():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Send a JSON body with text and language.',
                        'code': 'bad_request'}), 400
    try:
        result = generate_audio(data.get('text'), data.get('language'))
    except TTSError as exc:
        return jsonify({'error': exc.message, 'code': exc.code}), STATUS.get(exc.code, 500)

    return jsonify({
        'audio_url': f"/api/audio/{result['filename']}",
        'language': str(data.get('language')).strip().lower(),
        'characters': result['characters'],
        'cached': result['cached'],
    })


@tts_bp.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    if not FILENAME_RE.match(filename) or not os.path.isfile(os.path.join(AUDIO_DIR, filename)):
        return jsonify({'error': 'Audio file not found.', 'code': 'not_found'}), 404
    return send_from_directory(AUDIO_DIR, filename, mimetype='audio/mpeg')
