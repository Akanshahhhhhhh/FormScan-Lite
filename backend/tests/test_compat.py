"""Tests for the frontend-compatible endpoints (the URL names and fields the React app uses).

Fast tests need no models and no internet. The slow ones (run with --run-slow) make a real
translation and real audio through the frontend's URLs.
"""
import base64
import io

import pytest

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def assert_error(resp, status, code):
    assert resp.status_code == status, resp.get_data(as_text=True)
    data = resp.get_json()
    assert data["code"] == code
    assert isinstance(data["error"], str) and data["error"]


def not_json(client, url):
    return client.post(url, data="this is not json", content_type="text/plain")


# ---------------------------------------------------------------- health
def test_health_same_as_before(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


# ------------------------------------------------------------------- OCR
def ocr(client, filename="a.png", content=PNG_BYTES, language="en", with_image=True):
    data = {}
    if language is not None:
        data["language"] = language
    if with_image:
        data["image"] = (io.BytesIO(content), filename)
    return client.post("/api/ocr/extract", data=data, content_type="multipart/form-data")


def test_ocr_extract_no_image(client):
    assert_error(ocr(client, with_image=False), 400, "no_image")


def test_ocr_extract_missing_language(client):
    assert_error(ocr(client, language=None), 400, "missing_language")


def test_ocr_extract_unsupported_language(client):
    assert_error(ocr(client, language="fr"), 400, "unsupported_language")


def test_ocr_extract_unsupported_file_type(client):
    assert_error(ocr(client, filename="a.gif"), 400, "unsupported_file_type")


def test_ocr_extract_invalid_image(client):
    assert_error(ocr(client, content=b"not a picture"), 400, "invalid_image")


# ------------------------------------------------------------- translate
def tr(client, **body):
    return client.post("/api/translate/translate", json=body)


def test_translate_compat_missing_text(client):
    assert_error(tr(client, text="", src_lang="en", tgt_lang="ta"), 400, "missing_text")


def test_translate_compat_same_language(client):
    assert_error(tr(client, text="hello", src_lang="en", tgt_lang="en"), 400, "same_language")


def test_translate_compat_unsupported_language(client):
    assert_error(tr(client, text="hello", src_lang="en", tgt_lang="fr"), 400, "unsupported_language")


def test_translate_compat_not_json(client):
    assert_error(not_json(client, "/api/translate/translate"), 400, "bad_request")


# ------------------------------------------------------------------- TTS
def tts(client, **body):
    return client.post("/api/tts/generate", json=body)


def test_tts_compat_missing_text(client):
    assert_error(tts(client, text="", language="en"), 400, "missing_text")


def test_tts_compat_unsupported_language(client):
    assert_error(tts(client, text="hello", language="fr"), 400, "unsupported_language")


def test_tts_compat_not_json(client):
    assert_error(not_json(client, "/api/tts/generate"), 400, "bad_request")


# ------------------------------------------------------------------- FAQ
def ask(client, query, language="en"):
    return client.post("/api/faq/ask", json={"query": query, "language": language})


def test_faq_ask_match_has_frontend_fields(client):
    r = ask(client, "birth certificate")
    assert r.status_code == 200
    data = r.get_json()
    assert data["matched"] is True
    assert data["question"] == "How do I apply for a birth certificate?"
    assert data["answer"]
    assert 0 < data["confidence"] <= 1


def test_faq_ask_no_match_has_frontend_fields(client):
    r = ask(client, "qzxv")
    assert r.status_code == 200
    data = r.get_json()
    assert data["matched"] is False
    assert data["answer"] is None
    assert data["question"] is None
    assert data["confidence"] == 0


def test_faq_ask_missing_query(client):
    assert_error(ask(client, ""), 400, "missing_question")


def test_faq_ask_not_json(client):
    assert_error(not_json(client, "/api/faq/ask"), 400, "bad_request")


# -------------------------------------------------------------- feedback
def frontend_feedback(client, **body):
    return client.post("/api/feedback", json=body)


@pytest.mark.parametrize("feature", ["read_document", "translate", "faq"])
def test_feedback_frontend_shape_saved(client, keep_feedback_file, feature):
    r = frontend_feedback(client, feature=feature, helpful=True, details={})
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_feedback_frontend_shape_not_helpful_saved(client, keep_feedback_file):
    r = frontend_feedback(client, feature="faq", helpful=False, details={"language": "bn", "comment": "wrong"})
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_feedback_frontend_shape_bad_helpful(client):
    assert_error(frontend_feedback(client, feature="faq", helpful="maybe"), 400, "invalid_rating")


def test_feedback_frontend_shape_bad_feature(client):
    assert_error(frontend_feedback(client, feature="video", helpful=True), 400, "invalid_feature")


def test_feedback_real_shape_still_works(client, keep_feedback_file):
    r = client.post("/api/feedback", json={"rating": "helpful", "feature": "faq"})
    assert r.status_code == 201
    assert r.get_json()["status"] == "saved"


# ------------------------------------------------------------------ slow
@pytest.mark.slow
def test_translate_compat_real(client):
    r = tr(client, text="The fee is Rs. 250.", src_lang="en", tgt_lang="ta")
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json()
    assert data["translated_text"].strip()
    assert data["src_lang"] == "en"
    assert data["tgt_lang"] == "ta"


@pytest.mark.slow
def test_tts_compat_real(client):
    r = tts(client, text="Hello, this is a test.", language="en")
    assert r.status_code == 200, r.get_data(as_text=True)
    audio_url = r.get_json()["audio_url"]
    audio = client.get(audio_url)
    assert audio.status_code == 200
    assert audio.mimetype == "audio/mpeg"
