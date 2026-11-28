"""POST /api/chat - FAQ chatbot (RAG + Gemini, with FAQ fallback).

Request JSON:  {"question": "...", "language": "en" | "bn" | "ta"}
Response JSON: {"question", "language", "known", "answer", "sources",
                "fallback_used", "model", "retrieval_ms", "llm_ms"}
Errors:        {"error": "...", "code": "..."}
"""
import logging

from flask import Blueprint, jsonify, request

from services import llm_service

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = ("en", "bn", "ta")
MAX_QUESTION_LENGTH = 300

# Shown when no FAQ matches, in the language the user asked in.
NOT_FOUND_MESSAGES = {
    "en": "Sorry, I could not find an answer to this question in my sources.",
    "bn": "দুঃখিত, আমার উৎসগুলিতে এই প্রশ্নের উত্তর খুঁজে পাইনি।",
    "ta": "மன்னிக்கவும், என்னிடம் உள்ள ஆதாரங்களில் இந்த கேள்விக்கான பதிலை என்னால் கண்டுபிடிக்க முடியவில்லை.",
}


def _error(message, code, status):
    return jsonify({"error": message, "code": code}), status


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("Send a JSON body with 'question' and 'language'.",
                      "INVALID_JSON", 400)

    question = data.get("question")
    if not isinstance(question, str) or not question.strip():
        return _error("'question' is required.", "MISSING_QUESTION", 400)
    question = question.strip()
    if len(question) > MAX_QUESTION_LENGTH:
        return _error("'question' is too long (max %d characters)."
                      % MAX_QUESTION_LENGTH, "QUESTION_TOO_LONG", 400)

    language = data.get("language", "en")
    if language not in SUPPORTED_LANGUAGES:
        return _error("'language' must be one of: en, bn, ta.",
                      "UNSUPPORTED_LANGUAGE", 400)

    try:
        result = llm_service.answer_question(question, language)
    except Exception:
        logger.exception("chat failed")
        return _error("The chatbot could not answer right now. Try again.",
                      "CHAT_FAILED", 500)

    answer = result.get("answer")
    if result.get("known") is False:
        answer = NOT_FOUND_MESSAGES[language]

    return jsonify({
        "question": question,
        "language": language,
        "known": result.get("known"),
        "answer": answer,
        "sources": result.get("sources", []),
        "fallback_used": result.get("fallback_used", False),
        "model": result.get("model"),
        "retrieval_ms": result.get("retrieval_ms"),
        "llm_ms": result.get("llm_ms"),
    }), 200
