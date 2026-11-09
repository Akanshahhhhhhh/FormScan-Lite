"""Feedback service: saves Helpful / Not helpful votes to data/feedback.jsonl
(one JSON object per line). No document text is stored, only the vote."""
import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
FEEDBACK_FILE = os.path.join(BASE_DIR, 'data', 'feedback.jsonl')

RATINGS = {'helpful', 'not_helpful'}
FEATURES = {'ocr', 'translate', 'tts', 'faq'}
LANGUAGES = {'en', 'bn', 'ta'}
MAX_COMMENT = 500

_lock = threading.Lock()


class FeedbackError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def save_feedback(rating, feature, language=None, comment=None):
    """Validate and append one feedback line. Returns the saved id."""
    if rating not in RATINGS:
        raise FeedbackError('invalid_rating', 'rating must be "helpful" or "not_helpful".')
    if feature not in FEATURES:
        raise FeedbackError('invalid_feature', 'feature must be one of: ocr, translate, tts, faq.')

    if language is not None:
        if not isinstance(language, str) or language.strip().lower() not in LANGUAGES:
            raise FeedbackError('unsupported_language', 'language must be en, bn or ta.')
        language = language.strip().lower()

    if comment is not None:
        if not isinstance(comment, str):
            raise FeedbackError('bad_request', 'comment must be text.')
        comment = comment.strip() or None
        if comment and len(comment) > MAX_COMMENT:
            raise FeedbackError('comment_too_long',
                                f'comment is too long. Maximum is {MAX_COMMENT} characters.')

    entry = {
        'id': uuid.uuid4().hex,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'rating': rating,
        'feature': feature,
        'language': language,
        'comment': comment,
    }

    try:
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        with _lock:
            with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except OSError:
        logger.exception('Could not write feedback file')
        raise FeedbackError('save_failed', 'Could not save your feedback. Please try again.')

    logger.info('Feedback saved: %s %s', feature, rating)
    return entry['id']
