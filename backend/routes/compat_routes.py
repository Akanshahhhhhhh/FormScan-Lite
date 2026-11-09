"""Frontend-compatible endpoints.

The React frontend (frontend/src/services/api.js) uses its own URL names and field names.
Instead of changing the frontend, these routes accept exactly what the frontend sends,
pass it on to the real backend endpoints, and give back exactly what the frontend expects.

  Frontend calls                      Real endpoint it uses
  POST /api/ocr/extract         ->    POST /api/ocr
  POST /api/translate/translate ->    POST /api/translate
  POST /api/tts/generate        ->    POST /api/tts
  POST /api/faq/ask             ->    POST /api/faq
  POST /api/feedback            ->    POST /api/feedback (same URL: the frontend's body shape is converted)
  GET  /api/health              ->    (same)

Errors from the real endpoints are passed through unchanged, so the frontend can show
the "error" text as before.
"""
from flask import Blueprint, current_app, jsonify, request

compat_bp = Blueprint('compat', __name__)

FEEDBACK_FEATURES = {
    'read_document': 'ocr',
    'ocr': 'ocr',
    'translate': 'translate',
    'tts': 'tts',
    'faq': 'faq',
}


def _call_real(method, url, **kwargs):
    """Call one of our own real endpoints inside the same app and return its response."""
    client = current_app.test_client()
    return getattr(client, method)(url, **kwargs)


def _relay_error(resp):
    data = resp.get_json(silent=True)
    if not isinstance(data, dict):
        data = {'error': 'Something went wrong on the server.', 'code': 'server_error'}
    return jsonify(data), resp.status_code


def _json_body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else None


def _bad_request_from_real(url):
    """The body was not JSON: let the real endpoint produce its normal bad_request error."""
    return _call_real('post', url, data='not json', content_type='text/plain')


@compat_bp.route('/api/ocr/extract', methods=['POST'])
def ocr_extract():
    form = {}
    language = request.form.get('language')
    if language is not None:
        form['language'] = language
    image = request.files.get('image')
    if image is not None:
        form['image'] = (image.stream, image.filename or '')
    resp = _call_real('post', '/api/ocr', data=form, content_type='multipart/form-data')
    if resp.status_code != 200:
        return _relay_error(resp)
    data = resp.get_json()
    data['language'] = language
    return jsonify(data), 200


@compat_bp.route('/api/translate/translate', methods=['POST'])
def translate_compat():
    body = _json_body()
    if body is None:
        resp = _bad_request_from_real('/api/translate')
    else:
        resp = _call_real('post', '/api/translate', json={
            'text': body.get('text', ''),
            'source_lang': body.get('src_lang', ''),
            'target_lang': body.get('tgt_lang', ''),
        })
    if resp.status_code != 200:
        return _relay_error(resp)
    data = resp.get_json()
    data['src_lang'] = data.get('source_lang')
    data['tgt_lang'] = data.get('target_lang')
    return jsonify(data), 200


@compat_bp.route('/api/tts/generate', methods=['POST'])
def tts_generate():
    body = _json_body()
    if body is None:
        resp = _bad_request_from_real('/api/tts')
    else:
        resp = _call_real('post', '/api/tts', json={
            'text': body.get('text', ''),
            'language': body.get('language', ''),
        })
    if resp.status_code != 200:
        return _relay_error(resp)
    return jsonify(resp.get_json()), 200


@compat_bp.route('/api/faq/ask', methods=['POST'])
def faq_ask():
    body = _json_body()
    if body is None:
        resp = _bad_request_from_real('/api/faq')
    else:
        resp = _call_real('post', '/api/faq', json={
            'question': body.get('query', ''),
            'language': body.get('language', ''),
        })
    if resp.status_code != 200:
        return _relay_error(resp)
    data = resp.get_json()
    matched = bool(data.get('matched'))
    return jsonify({
        'matched': matched,
        'id': data.get('id'),
        'question': data.get('matched_question') if matched else None,
        'answer': data.get('answer') if matched else None,
        'confidence': data.get('score', 0) if matched else 0,
        'suggestions': data.get('suggestions', []),
    }), 200


def frontend_feedback_to_real(body):
    """Turn the frontend's feedback body into the real one.

    Frontend: {"feature": "read_document", "helpful": true, "details": {...}}
    Real:     {"rating": "helpful", "feature": "ocr", "language": "bn", "comment": "..."}
    """
    helpful = body.get('helpful')
    if helpful is True:
        rating = 'helpful'
    elif helpful is False:
        rating = 'not_helpful'
    else:
        rating = ''
    feature = body.get('feature')
    real = {
        'rating': rating,
        'feature': FEEDBACK_FEATURES.get(feature, feature) or '',
    }
    details = body.get('details')
    if isinstance(details, dict):
        if isinstance(details.get('language'), str):
            real['language'] = details['language']
        if isinstance(details.get('comment'), str):
            real['comment'] = details['comment']
    return real


@compat_bp.before_app_request
def accept_frontend_feedback_shape():
    """POST /api/feedback with the frontend's body shape (it has a "helpful" field).

    The real body shape (it has a "rating" field) is not touched and goes straight to the
    real endpoint. The converted body has no "helpful" field, so this hook does not run twice.
    """
    if request.path != '/api/feedback' or request.method != 'POST':
        return None
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or 'helpful' not in body:
        return None
    resp = _call_real('post', '/api/feedback', json=frontend_feedback_to_real(body))
    if resp.status_code == 201:
        return jsonify({'status': 'ok'}), 200
    return _relay_error(resp)
