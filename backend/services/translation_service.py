"""
translation_service.py - FormScan-Lite translation (IndicTrans2 distilled models).

Directions (language codes: en, bn, ta):
    en -> bn / ta      uses  ai4bharat/indictrans2-en-indic-dist-200M
    bn / ta -> en      uses  ai4bharat/indictrans2-indic-en-dist-200M
    bn <-> ta          uses  ai4bharat/indictrans2-indic-indic-dist-320M  (direct, no English pivot)

How it works (same steps as the official IndicTrans2 example):
    1. IndicProcessor.preprocess_batch  (normalise text, add language tags, script change)
    2. tokenizer + model.generate
    3. IndicProcessor.postprocess_batch (restore numbers/URLs, change script back)

The models are gated on Hugging Face: log in once with `huggingface-cli login`
after clicking "agree" on each model page.
Models load lazily on the first request for that direction (about 1 GB download each,
first time only) and stay in memory after that.
"""

import logging
import re
import threading

try:  # normal case: app.py is run from the backend/ folder
    from services.indic_processor_lite import IndicProcessor
except ImportError:  # fallback when imported as a package
    from .indic_processor_lite import IndicProcessor

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
LANG_CODES = {
    "en": "eng_Latn",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
}

MODEL_NAMES = {
    "en-indic": "ai4bharat/indictrans2-en-indic-dist-200M",
    "indic-en": "ai4bharat/indictrans2-indic-en-dist-200M",
    "indic-indic": "ai4bharat/indictrans2-indic-indic-dist-320M",
}

MAX_CHARS = 5000        # longest text accepted in one request
BATCH_SIZE = 4          # sentences translated together
MAX_WORDS_PER_PIECE = 80  # very long sentences are cut into pieces of this size
MAX_LENGTH = 256        # max tokens in / out (the model's limit)
NUM_BEAMS = 5           # same as the official example
# The IndicTrans2 model code fails with the "cache" on transformers 4.57 (error:
# 'NoneType' object has no attribute 'shape'), so the cache is off. Short sentences
# are still fast (a few seconds). Do not turn this on unless that bug is fixed.
USE_CACHE = False


class TranslationError(Exception):
    """Error that the API route can turn into a clean JSON message."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# ----------------------------------------------------------------------------
# Internal state
# ----------------------------------------------------------------------------
_lock = threading.Lock()   # one translation at a time (processor keeps a queue)
_processor = None          # one shared IndicProcessor
_models = {}               # model key -> (tokenizer, model, device)


def _get_processor():
    global _processor
    if _processor is None:
        _processor = IndicProcessor(inference=True)
    return _processor


def _model_key(source, target):
    if source == "en":
        return "en-indic"
    if target == "en":
        return "indic-en"
    return "indic-indic"


def _load_model(key):
    """Load (once) and return (tokenizer, model, device). Imports torch lazily."""
    if key in _models:
        return _models[key]
    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        name = MODEL_NAMES[key]
        logger.info("Loading translation model %s (first time can take a few minutes)", name)
        tokenizer = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(name, trust_remote_code=True)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        model.eval()
    except Exception as exc:  # noqa: BLE001 - we want a friendly message for any load problem
        logger.exception("Could not load model for %s", key)
        raise TranslationError(
            "model_load_failed",
            "Translation model could not be loaded. Check the internet connection, "
            "that you ran 'huggingface-cli login', and that you accepted the conditions "
            "on the model page. Details: " + str(exc)[:300],
        ) from exc
    _models[key] = (tokenizer, model, device)
    return _models[key]


def _generate_texts(key, prepared):
    """Run the model on already-preprocessed sentences. Returns decoded strings."""
    import torch

    tokenizer, model, device = _load_model(key)
    inputs = tokenizer(
        prepared,
        truncation=True,
        max_length=MAX_LENGTH,
        padding="longest",
        return_tensors="pt",
        return_attention_mask=True,
    ).to(device)

    with torch.no_grad():
        generated = model.generate(
            **inputs,
            use_cache=USE_CACHE,
            min_length=0,
            max_length=MAX_LENGTH,
            num_beams=NUM_BEAMS,
            num_return_sequences=1,
        )

    return tokenizer.batch_decode(
        generated, skip_special_tokens=True, clean_up_tokenization_spaces=True
    )


def preload(keys=None):
    """Optional: load models ahead of time (e.g. in a background thread at startup)
    so the first user request is not slow. keys: list of 'en-indic', 'indic-en',
    'indic-indic'; default = all three (needs about 3 GB of RAM)."""
    for key in (keys or list(MODEL_NAMES)):
        with _lock:
            _load_model(key)


# ----------------------------------------------------------------------------
# Text splitting (OCR text can be many lines / sentences)
# ----------------------------------------------------------------------------
# Split after . ! ? when the next thing is a capital letter, a quote/bracket or a
# non-English letter (so "Rs. 250" is NOT split). Danda marks always split.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[]|[^\x00-\x7F])|(?<=[\u0964\u0965])\s*")


def _split_long(sentence):
    words = sentence.split()
    if len(words) <= MAX_WORDS_PER_PIECE:
        return [sentence]
    return [
        " ".join(words[i:i + MAX_WORDS_PER_PIECE])
        for i in range(0, len(words), MAX_WORDS_PER_PIECE)
    ]


def split_text(text):
    """Return (pieces, layout). layout is a list of lines; each line is a list of
    indexes into pieces (empty list = blank line, kept so the layout is preserved)."""
    pieces, layout = [], []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        idxs = []
        if line:
            for sent in _SENTENCE_END.split(line):
                sent = sent.strip()
                if not sent:
                    continue
                for part in _split_long(sent):
                    idxs.append(len(pieces))
                    pieces.append(part)
        layout.append(idxs)
    return pieces, layout


# ----------------------------------------------------------------------------
# Public function
# ----------------------------------------------------------------------------
def translate(text, source, target):
    """Translate text. source/target are 'en', 'bn' or 'ta'.

    Returns {"translated_text", "source_lang", "target_lang", "model"}.
    Raises TranslationError with a code and a friendly message on problems.
    """
    if not isinstance(text, str) or not text.strip():
        raise TranslationError("missing_text", "No text to translate.")
    if len(text) > MAX_CHARS:
        raise TranslationError(
            "text_too_long", f"Text is too long ({len(text)} characters). Maximum is {MAX_CHARS}."
        )
    if source not in LANG_CODES or target not in LANG_CODES:
        raise TranslationError(
            "unsupported_language", "Languages must be one of: en, bn, ta."
        )
    if source == target:
        raise TranslationError("same_language", "Source and target language must be different.")

    pieces, layout = split_text(text)
    if not pieces:
        raise TranslationError("missing_text", "No text to translate.")

    key = _model_key(source, target)
    src_code, tgt_code = LANG_CODES[source], LANG_CODES[target]
    processor = _get_processor()
    results = []

    with _lock:
        try:
            for i in range(0, len(pieces), BATCH_SIZE):
                batch = pieces[i:i + BATCH_SIZE]
                prepared = processor.preprocess_batch(batch, src_lang=src_code, tgt_lang=tgt_code)
                decoded = _generate_texts(key, prepared)
                results.extend(processor.postprocess_batch(decoded, lang=tgt_code))
        except TranslationError:
            processor.reset_placeholders()
            raise
        except Exception as exc:  # noqa: BLE001
            processor.reset_placeholders()
            logger.exception("Translation failed")
            raise TranslationError("translation_failed", "Translation failed: " + str(exc)[:300]) from exc

    if len(results) != len(pieces):
        raise TranslationError("translation_failed", "Translation returned the wrong number of sentences.")

    out_lines = [" ".join(results[j] for j in idxs) for idxs in layout]
    return {
        "translated_text": "\n".join(out_lines).strip(),
        "source_lang": source,
        "target_lang": target,
        "model": MODEL_NAMES[key],
    }