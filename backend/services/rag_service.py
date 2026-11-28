"""
rag_service.py  -  retrieval part of the chatbot (RAG).

What it does:
  1. Reads backend/data/faqs/faqs.json and cuts each answer into chunks
     (short answers stay one chunk; long answers are split with overlap).
  2. Turns every chunk into numbers (embedding) with intfloat/multilingual-e5-small.
     Uses transformers + torch directly (NOT sentence-transformers / scikit-learn,
     because Windows Application Control blocks a scikit-learn file).
  3. Saves the numbers in backend/data/rag_index/ so the next start is fast.
     The cache is rebuilt by itself when faqs.json changes.
  4. retrieve(question, lang) returns the best chunks (top k) that pass a score
     threshold. An empty list means "I don't know".

The vector store is a plain numpy matrix (a few hundred chunks do not need
FAISS or Chroma). retrieve() is the only function other code should call, so
the store can be swapped later without touching the rest.

Demo (from the backend folder):
    ..\\venv\\Scripts\\python.exe services\\rag_service.py
"""
import hashlib
import json
import logging
import threading
import time
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
FAQ_PATH = BASE_DIR / "data" / "faqs" / "faqs.json"
INDEX_DIR = BASE_DIR / "data" / "rag_index"                  # cache (ignored by git)

MODEL_NAME = "intfloat/multilingual-e5-small"
LANGS = ("en", "bn", "ta")

# Scores of this model are squeezed between about 0.75 and 0.95.
# First test (5 English questions): good matches 0.85-0.95, off-topic 0.76-0.77.
# 0.82: Gemini also checks the passages, so the search limit stays low (tested 2026-11-25).
DEFAULT_MIN_SCORE = 0.82
MAX_WORDS = 120      # longest chunk
OVERLAP_WORDS = 20   # words repeated between two chunks of a long text


# ---------------------------------------------------------------- chunking
def chunk_text(text, max_words=MAX_WORDS, overlap=OVERLAP_WORDS):
    """Split text into chunks of at most max_words words, with overlap."""
    words = (text or "").split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]
    step = max(1, max_words - overlap)
    chunks = []
    for start in range(0, len(words), step):
        piece = words[start:start + max_words]
        chunks.append(" ".join(piece))
        if start + max_words >= len(words):
            break
    return chunks


def _answer_for(faq, lang):
    """Answer text of an FAQ entry in one language (None if there is none)."""
    ans = faq.get("answer")
    if isinstance(ans, dict):
        return ans.get(lang)
    if isinstance(ans, str):
        return ans if lang == "en" else None
    return None


def load_faq_list():
    data = json.loads(FAQ_PATH.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("faqs", "entries", "items"):
            if key in data:
                data = data[key]
                break
    if not isinstance(data, list):
        raise RuntimeError("Could not find the FAQ list inside faqs.json")
    return data


def build_chunks(faqs):
    """One dict per chunk: faq_id, lang, question, text, sources, state."""
    chunks = []
    for faq in faqs:
        questions = faq.get("question") or {}
        for lang in LANGS:
            question = questions.get(lang)
            answer = _answer_for(faq, lang)
            if not question or not answer:
                continue
            for n, piece in enumerate(chunk_text(answer)):
                chunks.append({
                    "chunk_id": f"{faq.get('id')}-{lang}-{n}",
                    "faq_id": faq.get("id"),
                    "lang": lang,
                    "question": question,
                    "text": piece,
                    "sources": faq.get("sources", []),
                    "state": faq.get("state"),
                })
    return chunks


# --------------------------------------------------------------- embedding
class Embedder:
    """multilingual-e5 through transformers + torch (loaded only when needed)."""

    def __init__(self, name=MODEL_NAME):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self._torch = torch
        self.tok = AutoTokenizer.from_pretrained(name)
        self.model = AutoModel.from_pretrained(name)
        self.model.eval()

    def encode(self, texts, batch_size=16):
        torch = self._torch
        parts = []
        for i in range(0, len(texts), batch_size):
            batch = self.tok(texts[i:i + batch_size], max_length=512,
                             padding=True, truncation=True, return_tensors="pt")
            with torch.no_grad():
                out = self.model(**batch)
            mask = batch["attention_mask"].unsqueeze(-1).float()
            emb = (out.last_hidden_state * mask).sum(1) / mask.sum(1)
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            parts.append(emb.numpy())
        return np.vstack(parts) if parts else np.zeros((0, 384), dtype="float32")


# ------------------------------------------------------------------- index
class _Index:
    def __init__(self, chunks, vectors, embedder):
        self.chunks = chunks
        self.vectors = vectors                      # (n_chunks, dim), normalised
        self.langs = np.array([c["lang"] for c in chunks])
        self.embedder = embedder


_index = None
_lock = threading.Lock()


def _signature():
    h = hashlib.sha1()
    h.update(FAQ_PATH.read_bytes())
    h.update(MODEL_NAME.encode("utf-8"))
    h.update(f"{MAX_WORDS}-{OVERLAP_WORDS}".encode("utf-8"))
    return h.hexdigest()[:16]


def _get_index():
    global _index
    with _lock:
        sig = _signature()
        if _index is not None and getattr(_index, "sig", None) == sig:
            return _index
        faqs = load_faq_list()
        chunks = build_chunks(faqs)
        embedder = Embedder()
        cache = INDEX_DIR / f"index_{sig}.npy"
        vectors = None
        if cache.exists():
            vectors = np.load(cache)
            if vectors.shape[0] != len(chunks):
                vectors = None
        if vectors is None:
            log.info("RAG: building index for %d chunks", len(chunks))
            texts = ["passage: " + c["question"] + "\n" + c["text"] for c in chunks]
            vectors = embedder.encode(texts)
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            np.save(cache, vectors)
        _index = _Index(chunks, vectors, embedder)
        _index.sig = sig
        return _index


def retrieve(question, lang="en", k=8, min_score=None):
    """Best chunks for a question, highest score first.

    Returns [] when nothing reaches min_score (the chatbot then says
    "I don't know"). Each item: chunk_id, faq_id, lang, question, text,
    sources, state, score.
    """
    if min_score is None:
        min_score = DEFAULT_MIN_SCORE
    question = (question or "").strip()
    if not question:
        return []
    idx = _get_index()
    mask = idx.langs == lang
    if not mask.any():
        mask = idx.langs == "en"
    qv = idx.embedder.encode(["query: " + question])[0]
    positions = np.where(mask)[0]
    scores = idx.vectors[positions] @ qv
    order = np.argsort(-scores)[:k]
    results = []
    for o in order:
        score = float(scores[o])
        if score < min_score:
            break
        item = dict(idx.chunks[positions[o]])
        item["score"] = round(score, 3)
        results.append(item)
    return results


# -------------------------------------------------------------------- demo
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    t0 = time.time()
    index = _get_index()
    print(f"Index ready in {time.time() - t0:.1f} s")
    counts = {lang: int((index.langs == lang).sum()) for lang in LANGS}
    print("Chunks per language:", counts)
    if index.chunks:
        c = index.chunks[0]
        print("Sample chunk:", c["chunk_id"], "|", c["question"])
        print("  text starts:", c["text"][:120])
        print("  sources:", c["sources"][:2] if isinstance(c["sources"], list) else c["sources"])

    tests = [
        ("en", "how do i get a birth certificate?"),
        ("en", "how much is the RTI fee"),
        ("en", "what is the best pizza in Kolkata"),
        ("bn", "জন্ম সনদের জন্য কীভাবে আবেদন করব?"),
        ("ta", "ஆதாருடன் பான் இணைப்பது எப்படி?"),
    ]
    for lang, q in tests:
        t1 = time.time()
        res = retrieve(q, lang, k=3, min_score=0.0)
        ms = (time.time() - t1) * 1000
        print(f"\n[{lang}] {q}   ({ms:.0f} ms)")
        for r in res:
            mark = "PASS" if r["score"] >= DEFAULT_MIN_SCORE else "below threshold"
            print(f"  {r['score']:.3f} {mark:15s} {r['faq_id']}  {r['question']}")
