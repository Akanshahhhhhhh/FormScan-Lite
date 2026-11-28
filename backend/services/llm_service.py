"""
llm_service.py  -  answer step of the chatbot (RAG).

answer_question(question, lang) does:
  1. retrieve() from rag_service finds the best chunks.
  2. If no chunk passes the score threshold -> "I don't know" (the LLM is NOT called).
  3. Otherwise the chunks go to Gemini with a grounded prompt: answer ONLY from
     the numbered sources, say which sources were used, answer in the user's language.
  4. If Gemini cannot be reached (no internet, quota), the text of the best
     chunk is returned instead (fallback_used = True), so the demo never breaks.

Key: read from the Windows variable GEMINI_API_KEY (never written in a file).
Optional variables: GEMINI_MODELS (comma list, tried in order; default
                    gemini-3-flash-preview,gemini-flash-lite-latest,gemini-flash-latest),
                    GEMINI_THINKING (default low; low/medium/high).
If a model is busy (HTTP 503/429/500) or unknown (404), the next model is tried.

Uses only the Python standard library for the web call (urllib).

Demo (from the backend folder):
    ..\\venv\\Scripts\\python.exe services\\llm_service.py
"""
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request

try:
    from services.rag_service import retrieve
except ImportError:                       # when run as: python services\llm_service.py
    from rag_service import retrieve

log = logging.getLogger(__name__)

MODELS = [m.strip() for m in os.environ.get(
    "GEMINI_MODELS",
    "gemini-3-flash-preview,gemini-flash-lite-latest,gemini-flash-latest").split(",") if m.strip()]
THINKING = os.environ.get("GEMINI_THINKING", "low")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_SECONDS = 12

LANG_NAMES = {"en": "English", "bn": "Bengali", "ta": "Tamil"}

DONT_KNOW = {
    "en": "Sorry, I could not find an answer to this question in my sources.",
    "bn": "দুঃখিত, আমার তথ্যসূত্রে এই প্রশ্নের উত্তর খুঁজে পাইনি।",
    "ta": "மன்னிக்கவும், எனது ஆதாரங்களில் இந்தக் கேள்விக்கான பதிலை நான் கண்டறியவில்லை.",
}


BUSY = {
    "en": "The assistant is busy right now. Please choose the question that matches yours:",
    "bn": "সহকারী এখন ব্যস্ত আছে। নিচের প্রশ্নগুলির মধ্যে কোনটি আপনার প্রশ্নের সাথে মেলে দেখুন:",
    "ta": "உதவியாளர் இப்போது பிஸியாக உள்ளது. கீழே உள்ள கேள்விகளில் உங்கள் கேள்விக்குப் பொருந்துவதைத் தேர்ந்தெடுக்கவும்:",
}


class LLMError(Exception):
    pass


class ModelUnavailable(LLMError):
    """This model is busy or unknown. Try the next one."""


# ------------------------------------------------------------------ prompt
def build_prompt(question, lang, chunks):
    language = LANG_NAMES.get(lang, "English")
    blocks = []
    for n, c in enumerate(chunks, 1):
        blocks.append(f"[{n}] Question: {c['question']}\n    Answer: {c['text']}")
    system = (
        "You are the help chatbot of FormScan-Lite, which helps people in India "
        "understand government services and forms.\n"
        "Rules:\n"
        "1. Answer ONLY with facts that are written in the numbered sources. "
        "Do not use any other knowledge.\n"
        "2. If the sources do not answer the question, set \"known\" to false and "
        "leave \"answer\" empty.\n"
        f"3. Write the answer in {language}, in simple short sentences, at most 6 sentences.\n"
        "4. Do not invent fees, dates, office names or links.\n"
        "5. Reply with JSON only, in this exact shape: "
        "{\"known\": true or false, \"answer\": \"...\", \"used\": [source numbers you used]}"
    )
    user = "Sources:\n" + "\n".join(blocks) + f"\n\nUser question: {question}"
    return system, user


# ---------------------------------------------------------------- Gemini call
def _call_gemini(system, user, model, with_thinking=True):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is not set")
    gen_cfg = {"temperature": 0.2, "responseMimeType": "application/json"}
    if with_thinking and THINKING:
        gen_cfg["thinkingConfig"] = {"thinkingLevel": THINKING}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": gen_cfg,
    }
    req = urllib.request.Request(
        API_URL.format(model=model),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        if e.code == 400 and with_thinking:
            log.warning("%s rejected the thinking setting, retrying without it", model)
            return _call_gemini(system, user, model, with_thinking=False)
        if e.code in (404, 429, 500, 503):
            raise ModelUnavailable(f"{model}: HTTP {e.code}")
        raise LLMError(f"{model}: HTTP {e.code}: {detail}")
    except Exception as e:                                   # no internet, timeout...
        raise LLMError(f"{model}: not reachable: {e}")

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts if not p.get("thought"))
    except (KeyError, IndexError, TypeError):
        raise LLMError(f"Unexpected Gemini reply: {str(data)[:300]}")


def _generate(system, user):
    """Try the models in order. Returns (text, model_used)."""
    problems = []
    for model in MODELS:
        try:
            return _call_gemini(system, user, model), model
        except ModelUnavailable as e:
            log.warning("Model not available, trying the next one: %s", e)
            problems.append(str(e))
        except LLMError as e:
            if "timed out" in str(e):
                log.warning("Model timed out, trying the next one: %s", e)
                problems.append(str(e))
                continue
            if "not reachable" in str(e) or "GEMINI_API_KEY" in str(e):
                raise                           # no internet or no key: next model will not help
            problems.append(str(e))
    raise LLMError("all models failed: " + " | ".join(problems))


def _parse_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise LLMError("Gemini did not return JSON")


# ----------------------------------------------------------------- main API
def _source_items(chunks, used_numbers=None):
    items, seen = [], set()
    for n, c in enumerate(chunks, 1):
        if used_numbers is not None and n not in used_numbers:
            continue
        if c["faq_id"] in seen:
            continue
        seen.add(c["faq_id"])
        urls = c.get("sources") or []
        if isinstance(urls, str):
            urls = [urls]
        items.append({"faq_id": c["faq_id"], "question": c["question"],
                      "score": c["score"], "urls": urls})
    return items


def answer_question(question, lang="en", k=10, min_score=None):
    t0 = time.time()
    chunks = retrieve(question, lang, k=k, min_score=min_score)
    t_retrieve = time.time() - t0
    result = {"question": question, "lang": lang, "known": False, "answer": "",
              "sources": [], "fallback_used": False, "error": None, "model": None,
              "retrieval_ms": round(t_retrieve * 1000), "llm_ms": 0}

    if not chunks:
        result["answer"] = DONT_KNOW.get(lang, DONT_KNOW["en"])
        return result

    system, user = build_prompt(question, lang, chunks)
    t1 = time.time()
    try:
        text, result["model"] = _generate(system, user)
        parsed = _parse_json(text)
        result["llm_ms"] = round((time.time() - t1) * 1000)
        if parsed.get("known") and (parsed.get("answer") or "").strip():
            used = {int(x) for x in parsed.get("used", []) if str(x).isdigit()}
            result["known"] = True
            result["answer"] = parsed["answer"].strip()
            result["sources"] = _source_items(chunks, used or None)
        else:
            result["answer"] = DONT_KNOW.get(lang, DONT_KNOW["en"])
    except (LLMError, ValueError) as e:
        log.warning("LLM step failed, using the best FAQ text: %s", e)
        result["llm_ms"] = round((time.time() - t1) * 1000)
        result["error"] = str(e)
        result["fallback_used"] = True
        result["known"] = True
        top = _source_items(chunks)[:3]
        lines = "\n".join(f"{i}. {s['question']}" for i, s in enumerate(top, 1))
        result["answer"] = BUSY.get(lang, BUSY["en"]) + "\n" + lines
        result["sources"] = top
    return result


# -------------------------------------------------------------------- demo
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tests = [
        ("en", "how do i get a birth certificate?"),
        ("bn", "জন্ম সনদের জন্য কীভাবে আবেদন করব?"),
        ("ta", "ஆதாருடன் பான் இணைப்பது எப்படி?"),
        ("en", "what is the best pizza in Kolkata"),
    ]
    for lang, q in tests:
        r = answer_question(q, lang)
        print("\n" + "=" * 70)
        print(f"[{lang}] {q}")
        print(f"known={r['known']}  fallback={r['fallback_used']}  model={r['model']}  "
              f"retrieval={r['retrieval_ms']} ms  llm={r['llm_ms']} ms")
        if r["error"]:
            print("error:", r["error"])
        print("ANSWER:", r["answer"])
        for s in r["sources"]:
            print(f"  source {s['faq_id']} ({s['score']}): {s['urls'][:2]}")
