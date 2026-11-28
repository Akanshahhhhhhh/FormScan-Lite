"""Tests for POST /api/chat. The real RAG + Gemini call is replaced by a fake,
so these tests are fast and need no internet."""
import pytest

from app import app
from services import llm_service


@pytest.fixture()
def chat_client():
    app.config["TESTING"] = True
    return app.test_client()


FAKE_RESULT = {
    "question": "x",
    "lang": "en",
    "known": True,
    "answer": "Apply at the local registration office.",
    "sources": [{"faq_id": "faq-001", "question": "How do I apply for a birth certificate?",
                 "score": 0.9, "urls": ["https://example.gov.in"]}],
    "fallback_used": False,
    "error": None,
    "model": "gemini-3-flash-preview",
    "retrieval_ms": 15,
    "llm_ms": 1200,
}


@pytest.fixture()
def fake_answer(monkeypatch):
    calls = []

    def _fake(question, lang):
        calls.append((question, lang))
        return dict(FAKE_RESULT)

    monkeypatch.setattr(llm_service, "answer_question", _fake)
    return calls


def test_chat_ok(chat_client, fake_answer):
    r = chat_client.post("/api/chat", json={"question": "  how do i get a birth certificate?  ",
                                            "language": "en"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["known"] is True
    assert body["answer"].startswith("Apply")
    assert body["sources"][0]["faq_id"] == "faq-001"
    assert body["fallback_used"] is False
    assert body["language"] == "en"
    # the question is trimmed before it reaches the service
    assert fake_answer == [("how do i get a birth certificate?", "en")]


@pytest.mark.parametrize("lang", ["bn", "ta"])
def test_chat_other_languages(chat_client, fake_answer, lang):
    r = chat_client.post("/api/chat", json={"question": "test", "language": lang})
    assert r.status_code == 200
    assert fake_answer[-1][1] == lang


def test_chat_language_defaults_to_english(chat_client, fake_answer):
    r = chat_client.post("/api/chat", json={"question": "test"})
    assert r.status_code == 200
    assert fake_answer[-1][1] == "en"


def test_chat_missing_question(chat_client, fake_answer):
    r = chat_client.post("/api/chat", json={"language": "en"})
    assert r.status_code == 400
    assert r.get_json()["code"] == "MISSING_QUESTION"
    assert fake_answer == []


def test_chat_blank_question(chat_client, fake_answer):
    r = chat_client.post("/api/chat", json={"question": "   ", "language": "en"})
    assert r.status_code == 400
    assert r.get_json()["code"] == "MISSING_QUESTION"


def test_chat_question_too_long(chat_client, fake_answer):
    r = chat_client.post("/api/chat", json={"question": "a" * 301, "language": "en"})
    assert r.status_code == 400
    assert r.get_json()["code"] == "QUESTION_TOO_LONG"
    assert fake_answer == []


def test_chat_question_exactly_300_is_ok(chat_client, fake_answer):
    r = chat_client.post("/api/chat", json={"question": "a" * 300, "language": "en"})
    assert r.status_code == 200


def test_chat_bad_language(chat_client, fake_answer):
    r = chat_client.post("/api/chat", json={"question": "test", "language": "fr"})
    assert r.status_code == 400
    assert r.get_json()["code"] == "UNSUPPORTED_LANGUAGE"
    assert fake_answer == []


def test_chat_not_json(chat_client, fake_answer):
    r = chat_client.post("/api/chat", data="hello", content_type="text/plain")
    assert r.status_code == 400
    assert r.get_json()["code"] == "INVALID_JSON"


def test_chat_service_crash_gives_500(chat_client, monkeypatch):
    def _boom(question, lang):
        raise RuntimeError("boom")

    monkeypatch.setattr(llm_service, "answer_question", _boom)
    r = chat_client.post("/api/chat", json={"question": "test", "language": "en"})
    assert r.status_code == 500
    assert r.get_json()["code"] == "CHAT_FAILED"


def test_chat_unknown_question_passes_through(chat_client, monkeypatch):
    def _unknown(question, lang):
        return {"known": False, "answer": "I don't know.", "sources": [],
                "fallback_used": False, "error": None, "model": None,
                "retrieval_ms": 12, "llm_ms": 0}

    monkeypatch.setattr(llm_service, "answer_question", _unknown)
    r = chat_client.post("/api/chat", json={"question": "pizza in Kolkata", "language": "en"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["known"] is False
    assert body["sources"] == []


@pytest.mark.parametrize("lang", ["en", "bn", "ta"])
def test_chat_unknown_answer_is_in_the_users_language(chat_client, monkeypatch, lang):
    from routes.chat_routes import NOT_FOUND_MESSAGES

    def _unknown(question, language):
        return {"known": False, "answer": "Sorry, I could not find an answer.",
                "sources": [], "fallback_used": False, "error": None,
                "model": None, "retrieval_ms": 10, "llm_ms": 0}

    monkeypatch.setattr(llm_service, "answer_question", _unknown)
    r = chat_client.post("/api/chat", json={"question": "pizza", "language": lang})
    assert r.status_code == 200
    body = r.get_json()
    assert body["known"] is False
    assert body["answer"] == NOT_FOUND_MESSAGES[lang]
    assert body["answer"].strip() != ""
