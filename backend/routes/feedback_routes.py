from flask import Blueprint, jsonify, request

from services.feedback_service import FeedbackError, save_feedback

feedback_bp = Blueprint('feedback', __name__)

STATUS = {
    'bad_request': 400,
    'invalid_rating': 400,
    'invalid_feature': 400,
    'unsupported_language': 400,
    'comment_too_long': 400,
    'save_failed': 500,
}


@feedback_bp.route('/api/feedback', methods=['POST'])
def post_feedback():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Send a JSON body with rating and feature.',
                        'code': 'bad_request'}), 400
    try:
        feedback_id = save_feedback(
            data.get('rating'),
            data.get('feature'),
            data.get('language'),
            data.get('comment'),
        )
    except FeedbackError as exc:
        return jsonify({'error': exc.message, 'code': exc.code}), STATUS.get(exc.code, 500)

    return jsonify({'status': 'saved', 'id': feedback_id}), 201
