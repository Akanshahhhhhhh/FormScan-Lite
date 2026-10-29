"""Fast tests for every endpoint. No models, no internet, nothing saved."""
import base64
import io
import json
from pathlib import Path

import pytest

# a real 1x1 PNG picture (used to pass the "is it an image" checks)
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

FAQ_FILE = Path(__file__).resolve().parents[1] / "data" / "faqs" / "faqs.json"


def assert_error(resp, status, code):
    assert resp.status_code == status, resp.get_data(as_text=True)
    data = resp.get_json()
    assert data["code"] == code
    assert isinstance(data["error"], str) and data["error"]


def not_json(client, url):
    return client.post(url, data="this is not json", content_type="text/plain")


# ---------------------------------------------------------------- health
def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_health_post_not_allowed(client):
    assert client.post("/api/health").status_code == 405


# ------------------------------------------------------------------- OCR
def ocr_post(client, filename="a.png", content=PNG_BYTES, language="en", with_image=True):
    data = {}
    if language is not None:
        data["language"] = language
    if with_image:
        data["image"] = (io.BytesIO(content), filename)
    return client.post("/api/ocr", data=data, content_type="multipart/form-data")


def test_ocr_no_image(client):
    assert_error(ocr_post(client, with_image=False), 400, "no_image")


def test_ocr_missing_language(client):
    assert_error(ocr_post(client, language=None), 400, "missing_language")


def test_ocr_unsupported_language(client):
    assert_error(ocr_post(client, language="fr"), 400, "unsupported_language")


def test_ocr_unsupported_file_type(client):
    assert_error(ocr_post(client, filename="a.gif"), 400, "unsupported_file_type")


def test_ocr_file_too_large(client):
    big = PNG_BYTES + b"0" * (11 * 1024 * 1024)
    assert_error(ocr_post(client, content=big), 413, "file_too_large")


def test_ocr_invalid_image(client):
    assert_error(ocr_post(client, content=b"not a picture"), 400, "invalid_image")


# ------------------------------------------------------------- translate
def tr(client, **body):
    return client.post("/api/translate", json=body)


def test_translate_missing_text(client):
    assert_error(tr(client, text="", source_lang="en", target_lang="ta"), 400, "missing_text")


def test_translate_text_too_long(client):
    assert_error(
        tr(client, text="a" * 5001, source_lang="en", target_lang="ta"),
        400,
        "text_too_long",
    )


def test_translate_unsupported_language(client):
    assert_error(
        tr(client, text="hello", source_lang="en", target_lang="fr"),
        400,
        "unsupported_language",
    )


def test_translate_same_language(client):
    assert_error(
        tr(client, text="hello", source_lang="en", target_lang="en"),
        400,
        "same_language",
    )


def test_translate_not_json(client):
    assert_error(not_json(client, "/api/translate"), 400, "bad_request")


# ------------------------------------------------------------------- TTS
def tts(client, **body):
    return client.post("/api/tts", json=body)


def test_tts_missing_text(client):
    assert_error(tts(client, text="", language="en"), 400, "missing_text")


def test_tts_unsupported_language(client):
    assert_error(tts(client, text="hello", language="fr"), 400, "unsupported_language")


def test_tts_text_too_long(client):
    assert_error(tts(client, text="a" * 3001, language="en"), 400, "text_too_long")


def test_tts_no_speakable_text(client):
    assert_error(tts(client, text="!!! ???", language="en"), 400, "no_speakable_text")


def test_tts_not_json(client):
    assert_error(not_json(client, "/api/tts"), 400, "bad_request")


def test_audio_unknown_file(client):
    r = client.get("/api/audio/" + "a" * 32 + ".mp3")
    assert_error(r, 404, "not_found")


# -------------------------------------------------------------- feedback
GOOD_VOTE = {"rating": "helpful", "feature": "translate", "language": "bn", "comment": "ok"}


def fb(client, **changes):
    body = dict(GOOD_VOTE)
    body.update(changes)
    return client.post("/api/feedback", json=body)


def test_feedback_invalid_rating(client):
    assert_error(fb(client, rating="great"), 400, "invalid_rating")


def test_feedback_invalid_feature(client):
    assert_error(fb(client, feature="video"), 400, "invalid_feature")


def test_feedback_unsupported_language(client):
    assert_error(fb(client, language="fr"), 400, "unsupported_language")


def test_feedback_comment_too_long(client):
    assert_error(fb(client, comment="a" * 501), 400, "comment_too_long")


def test_feedback_not_json(client):
    assert_error(not_json(client, "/api/feedback"), 400, "bad_request")


def test_feedback_saved(client, keep_feedback_file):
    r = fb(client)
    assert r.status_code == 201
    data = r.get_json()
    assert data["status"] == "saved"
    assert len(data["id"]) == 32


# ------------------------------------------------------------------- FAQ
def faq(client, question, language):
    return client.post("/api/faq", json={"question": question, "language": language})


@pytest.mark.parametrize(
    "question,language,expected_id",
    [
        ("birth certificate", "en", "faq-001"),
        ("nativity certificate tamil nadu", "en", "faq-016"),
        ("tamil nadu ration card smart card", "en", "faq-017"),
        ("ரேஷன் அட்டை விண்ணப்பம்", "ta", "faq-017"),
        ("west bengal caste certificate", "en", "faq-018"),
        ("কাস্ট সার্টিফিকেট", "bn", "faq-018"),
        ("west bengal digital ration card", "en", "faq-019"),
    ],
)
def test_faq_matches(client, question, language, expected_id):
    r = faq(client, question, language)
    assert r.status_code == 200
    data = r.get_json()
    assert data["matched"] is True
    assert data["id"] == expected_id
    assert data["language"] == language
    assert data["answer"]
    assert 0 <= data["score"] <= 1


@pytest.mark.parametrize(
    "question,language",
    [
        ("what is the weather today", "en"),
        ("qzxv", "en"),
        ("আজকের আবহাওয়া কেমন", "bn"),
    ],
)
def test_faq_no_match(client, question, language):
    r = faq(client, question, language)
    assert r.status_code == 200
    data = r.get_json()
    assert data["matched"] is False
    assert data["id"] is None
    assert data["answer"] is None
    assert data["matched_question"] is None


def test_faq_missing_question(client):
    assert_error(faq(client, "", "en"), 400, "missing_question")


def test_faq_question_too_long(client):
    assert_error(faq(client, "a" * 301, "en"), 400, "question_too_long")


def test_faq_unsupported_language(client):
    assert_error(faq(client, "birth certificate", "fr"), 400, "unsupported_language")


def test_faq_not_json(client):
    assert_error(not_json(client, "/api/faq"), 400, "bad_request")


def test_faq_list_unsupported_language(client):
    r = client.get("/api/faq/questions?language=fr")
    assert_error(r, 400, "unsupported_language")


# ----------------------------------------------- FAQ data file (faqs.json)
@pytest.fixture(scope="module")
def faq_entries():
    return json.loads(FAQ_FILE.read_text(encoding="utf-8"))


def test_faq_ids_are_unique(faq_entries):
    ids = [e["id"] for e in faq_entries]
    assert len(ids) == len(set(ids))


def test_faq_entries_have_required_fields(faq_entries):
    for e in faq_entries:
        for field in ("id", "category", "status", "question", "keywords", "answer"):
            assert field in e, f"{e.get('id')} is missing {field}"
        assert e["question"].get("en") and e["answer"].get("en"), f"{e['id']} needs English"


def test_faq_each_language_has_all_three_parts(faq_entries):
    for e in faq_entries:
        for lang in ("en", "bn", "ta"):
            parts = [lang in e["question"], lang in e["keywords"], lang in e["answer"]]
            assert all(parts) or not any(parts), f"{e['id']} is half-filled for {lang}"


@pytest.mark.parametrize("language", ["en", "bn", "ta"])
def test_faq_list_matches_data(client, faq_entries, language):
    r = client.get(f"/api/faq/questions?language={language}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["language"] == language
    expected = [e["id"] for e in faq_entries if e["question"].get(language)]
    assert [q["id"] for q in data["questions"]] == expected
