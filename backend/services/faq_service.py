"""FAQ service: finds the FAQ question closest to what the user typed.

Pure Python (no scikit-learn / scipy). It compares small letter groups
(character 3-grams) with TF-IDF, which works for English, Bengali and Tamil
and still copes with spelling differences like "aadhar" / "aadhaar".

FAQ data: backend/data/faqs/faqs.json (edit the file, no restart needed).
"""
import json
import logging
import math
import os
import threading
import unicodedata
from collections import Counter

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
FAQ_FILE = os.path.join(BASE_DIR, 'data', 'faqs', 'faqs.json')

SUPPORTED_LANGUAGES = ('en', 'bn', 'ta')
MAX_QUESTION_CHARS = 300
MIN_SCORE = 0.30        # below this we say "no match" (tune in Week 6)
MAX_SUGGESTIONS = 3

EN_STOPWORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'be', 'do', 'does', 'did', 'i', 'me', 'my',
    'we', 'you', 'your', 'how', 'what', 'where', 'when', 'which', 'who', 'to', 'for',
    'of', 'in', 'on', 'at', 'and', 'or', 'can', 'should', 'get', 'it', 'about',
    'please', 'tell', 'mean', 'means', 'meaning',
}


class FAQError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def normalize(text, language):
    """Lowercase, remove punctuation (including the Hindi/Bengali danda), keep all
    letters AND vowel signs (Bengali/Tamil need their combining marks)."""
    text = unicodedata.normalize('NFC', text).lower()
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat == 'Cf':          # invisible joiners
            continue
        out.append(ch if cat[0] in 'LMN' else ' ')
    words = ''.join(out).split()
    if language == 'en':
        kept = [w for w in words if w not in EN_STOPWORDS]
        words = kept or words
    return ' '.join(words)


def _grams(text):
    padded = f' {text} '
    return Counter(padded[i:i + 3] for i in range(max(len(padded) - 2, 0)))


def _vectorise(grams, idf, default_idf):
    vec = {g: (1 + math.log(c)) * idf.get(g, default_idf) for c, g in ((c, g) for g, c in grams.items())}
    norm = math.sqrt(sum(v * v for v in vec.values()))
    return vec, norm


class _Index:
    """TF-IDF index for one language."""

    def __init__(self, language, entries):
        self.language = language
        self.items = []
        docs = []
        for e in entries:
            question = (e.get('question') or {}).get(language)
            answer = (e.get('answer') or {}).get(language)
            if not question or not answer:
                continue
            extra = ' '.join((e.get('keywords') or {}).get(language, []))
            docs.append(_grams(normalize(f'{question} {extra}', language)))
            self.items.append({'id': e['id'], 'question': question, 'answer': answer,
                               'category': e.get('category')})
        n = len(docs)
        df = Counter()
        for d in docs:
            df.update(d.keys())
        self.idf = {g: math.log((1 + n) / (1 + c)) + 1 for g, c in df.items()}
        self.default_idf = math.log(1 + n) + 1
        self.vectors = [_vectorise(d, self.idf, self.default_idf) for d in docs]

    def rank(self, query):
        grams = _grams(normalize(query, self.language))
        qvec, qnorm = _vectorise(grams, self.idf, self.default_idf)
        if qnorm == 0:
            return []
        scored = []
        for item, (dvec, dnorm) in zip(self.items, self.vectors):
            if dnorm == 0:
                continue
            dot = sum(w * dvec.get(g, 0.0) for g, w in qvec.items())
            scored.append((dot / (qnorm * dnorm), item))
        scored.sort(key=lambda s: s[0], reverse=True)
        return scored


_lock = threading.Lock()
_cache = {'mtime': None, 'indexes': {}}


def _get_indexes():
    try:
        mtime = os.path.getmtime(FAQ_FILE)
    except OSError:
        raise FAQError('faq_unavailable', 'The FAQ list is not available right now.')

    with _lock:
        if _cache['mtime'] == mtime and _cache['indexes']:
            return _cache['indexes']
        try:
            with open(FAQ_FILE, encoding='utf-8') as f:
                entries = json.load(f)
            if not isinstance(entries, list):
                raise ValueError('faqs.json must be a list')
            entries = [e for e in entries if isinstance(e, dict) and e.get('id')]
            indexes = {lang: _Index(lang, entries) for lang in SUPPORTED_LANGUAGES}
        except (OSError, ValueError):
            logger.exception('Could not load %s', FAQ_FILE)
            raise FAQError('faq_unavailable', 'The FAQ list is not available right now.')
        _cache['mtime'] = mtime
        _cache['indexes'] = indexes
        logger.info('FAQ loaded: %d entries', len(entries))
        return indexes


def _check_language(language):
    if not isinstance(language, str) or language.strip().lower() not in SUPPORTED_LANGUAGES:
        raise FAQError('unsupported_language', 'Language must be en, bn or ta.')
    return language.strip().lower()


def ask(question, language):
    """Return the best FAQ answer for a question. Raises FAQError."""
    if not isinstance(question, str) or not question.strip():
        raise FAQError('missing_question', 'Please type a question.')
    language = _check_language(language)
    question = question.strip()
    if len(question) > MAX_QUESTION_CHARS:
        raise FAQError('question_too_long',
                       f'Question is too long. Maximum is {MAX_QUESTION_CHARS} characters.')

    ranked = _get_indexes()[language].rank(question)
    best_score, best = ranked[0] if ranked else (0.0, None)
    matched = best is not None and best_score >= MIN_SCORE

    others = [(s, it) for s, it in ranked if s > 0 and not (matched and it is best)]
    suggestions = [{'id': it['id'], 'question': it['question']}
                   for s, it in others[:MAX_SUGGESTIONS]]

    return {
        'matched': matched,
        'id': best['id'] if matched else None,
        'answer': best['answer'] if matched else None,
        'matched_question': best['question'] if matched else None,
        'score': round(best_score, 3),
        'language': language,
        'suggestions': suggestions,
    }


def list_questions(language):
    language = _check_language(language)
    return [{'id': it['id'], 'question': it['question'], 'category': it['category']}
            for it in _get_indexes()[language].items]
