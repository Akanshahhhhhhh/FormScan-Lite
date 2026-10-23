from flask import Blueprint, jsonify, request

from services.faq_service import FAQError, ask, list_questions

faq_bp = Blueprint('faq', __name__)

STATUS = {
    'bad_request': 400,
    'missing_question': 400,
    'question_too_long': 400,
    'unsupported_language': 400,
    'faq_unavailable': 500,
}


def _error(exc):
    return jsonify({'error': exc.message, 'code': exc.code}), STATUS.get(exc.code, 500)


@faq_bp.route('/api/faq', methods=['POST'])
def faq_ask():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Send a JSON body with question and language.',
                        'code': 'bad_request'}), 400
    try:
        return jsonify(ask(data.get('question'), data.get('language')))
    except FAQError as exc:
        return _error(exc)


@faq_bp.route('/api/faq/questions', methods=['GET'])
def faq_questions():
    try:
        language = request.args.get('language', '')
        return jsonify({'language': language.strip().lower(),
                        'questions': list_questions(language)})
    except FAQError as exc:
        return _error(exc)
