"""Text-to-speech service (gTTS).

Makes an mp3 for a piece of text in English, Bengali or Tamil.
Audio is cached: the same text + language gives the same file, so the
second request is instant and needs no internet.
"""
import hashlib
import logging
import os
import uuid

from gtts import gTTS

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
AUDIO_DIR = os.path.join(BASE_DIR, 'outputs', 'audio')

SUPPORTED_LANGUAGES = {'en', 'bn', 'ta'}
MAX_CHARS = 3000


class TTSError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def audio_path(filename):
    return os.path.join(AUDIO_DIR, filename)


def generate_audio(text, language):
    """Return {'filename', 'characters', 'cached'}. Raises TTSError."""
    if not isinstance(text, str) or not text.strip():
        raise TTSError('missing_text', 'Please send some text to read aloud.')
    if not isinstance(language, str) or not language.strip():
        raise TTSError('unsupported_language', 'Please send a language: en, bn or ta.')

    text = text.strip()
    language = language.strip().lower()

    if language not in SUPPORTED_LANGUAGES:
        raise TTSError('unsupported_language', 'Language must be en, bn or ta.')
    if len(text) > MAX_CHARS:
        raise TTSError('text_too_long', f'Text is too long. Maximum is {MAX_CHARS} characters.')

    os.makedirs(AUDIO_DIR, exist_ok=True)

    key = hashlib.sha256(f'{language}:{text}'.encode('utf-8')).hexdigest()[:32]
    filename = f'{key}.mp3'
    final_path = audio_path(filename)

    if os.path.isfile(final_path) and os.path.getsize(final_path) > 0:
        logger.info('TTS cache hit: %s (%s, %d chars)', filename, language, len(text))
        return {'filename': filename, 'characters': len(text), 'cached': True}

    # Write to a temp file first, so a half-written mp3 is never served.
    tmp_path = f'{final_path}.{uuid.uuid4().hex}.tmp'
    try:
        gTTS(text=text, lang=language, slow=False).save(tmp_path)
        os.replace(tmp_path, final_path)
    except Exception as exc:
        logger.exception('gTTS failed (%s, %d chars)', language, len(text))
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        if 'No text' in str(exc):
            raise TTSError('no_speakable_text', 'There is nothing to read aloud in this text.')
        raise TTSError('tts_failed',
                       'Could not create the audio. gTTS needs an internet connection.')

    logger.info('TTS created: %s (%s, %d chars)', filename, language, len(text))
    return {'filename': filename, 'characters': len(text), 'cached': False}
