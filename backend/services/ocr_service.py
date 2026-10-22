"""OCR service: EasyOCR for Bengali/English, Tesseract for Tamil.

Every result has the same shape:
    text, confidence (0 to 1), confidence_level (low/medium/high), warning, engine
"""
import logging
import threading

import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SUPPORTED_LANGUAGES = ('bn', 'ta', 'en')

# (high_from, medium_from) for each engine. Starting values only:
# tune them in Week 6 when you test on real printed forms.
CONFIDENCE_THRESHOLDS = {
    'easyocr': (0.70, 0.40),
    'tesseract': (0.80, 0.55),
}
DEFAULT_THRESHOLDS = (0.80, 0.55)

WARNING_LOW = ('Low confidence: the text may have mistakes. '
               'Please check it against the original document.')
WARNING_MEDIUM = ('Medium confidence: please double-check names, dates and amounts.')
WARNING_NO_TEXT = ('No text was found in this image. '
                   'Try a clearer photo with good light.')

# EasyOCR is imported only when Bengali/English is first used, so the server
# starts faster and Tamil/TTS/translation do not need EasyOCR to load.
_easyocr_reader = None
_reader_lock = threading.Lock()


def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        with _reader_lock:
            if _easyocr_reader is None:
                import easyocr  # lazy import
                _easyocr_reader = easyocr.Reader(['bn', 'en'])
    return _easyocr_reader


def confidence_level(confidence, engine):
    """Turn a 0-1 confidence into 'low', 'medium' or 'high' for this engine."""
    high, medium = CONFIDENCE_THRESHOLDS.get(engine, DEFAULT_THRESHOLDS)
    if confidence >= high:
        return 'high'
    if confidence >= medium:
        return 'medium'
    return 'low'


def build_result(text, confidence, engine):
    text = (text or '').strip()
    if not text:
        return {'text': '', 'confidence': 0.0, 'confidence_level': 'low',
                'warning': WARNING_NO_TEXT, 'engine': engine}

    confidence = max(0.0, min(1.0, float(confidence)))
    level = confidence_level(confidence, engine)
    warning = {'low': WARNING_LOW, 'medium': WARNING_MEDIUM, 'high': None}[level]
    return {'text': text, 'confidence': round(confidence, 3),
            'confidence_level': level, 'warning': warning, 'engine': engine}


def extract_text_bengali(image_path):
    reader = get_easyocr_reader()
    results = reader.readtext(image_path)
    text = " ".join(res[1] for res in results)
    avg_confidence = (sum(res[2] for res in results) / len(results)) if results else 0.0
    return build_result(text, avg_confidence, 'easyocr')


def extract_text_tamil(image_path):
    with Image.open(image_path) as image:
        data = pytesseract.image_to_data(image, lang='tam',
                                         output_type=pytesseract.Output.DICT)

    words = [w for w in data['text'] if w.strip()]
    confidences = [float(c) for c, w in zip(data['conf'], data['text'])
                   if w.strip() and float(c) != -1]

    text = " ".join(words)
    avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
    return build_result(text, avg_confidence, 'tesseract')


def extract_text(image_path, language):
    """language: 'bn' for Bengali, 'ta' for Tamil, 'en' for English"""
    if language == 'ta':
        return extract_text_tamil(image_path)
    elif language in ('bn', 'en'):
        return extract_text_bengali(image_path)
    else:
        raise ValueError(f"Unsupported language: {language}")
