# FormScan-Lite API contract (frontend ↔ backend)

The frontend calls exactly these endpoints. Base URL: `http://localhost:5000`.
Every error response should be JSON: `{ "error": "Plain message shown to the user" }`.

Backend must enable CORS (`pip install flask-cors`, then `CORS(app)`), because the
frontend runs on port 5173 and the backend on 5000.

Language codes everywhere: `bn` (Bengali), `ta` (Tamil), `en` (English).

---

## GET /api/health
Response: `{ "status": "ok" }`

## POST /api/ocr/extract
Request: `multipart/form-data`
- `image`: the uploaded file (jpg/png/webp, ≤ 10 MB)
- `language`: `bn` | `ta` | `en`

Response:
```json
{ "text": "extracted text", "confidence": 0.72, "language": "bn" }
```
`confidence` is a number from 0 to 1 (average of EasyOCR line confidences).
If nothing is found, return `"text": ""` and `"confidence": 0` (not an error).

## POST /api/translate/translate
Request (JSON): `{ "text": "...", "src_lang": "en", "tgt_lang": "bn" }`
Response: `{ "translated_text": "...", "src_lang": "en", "tgt_lang": "bn" }`

No confidence score here: IndicTrans2 does not output one, so we do not show a fake number.

## POST /api/tts/generate
Request (JSON): `{ "text": "...", "language": "bn" }`
Response: `{ "audio_url": "/audio/abc123.mp3" }`

The backend saves the mp3 and serves it, for example:
```python
from flask import send_from_directory
@app.route('/audio/<path:name>')
def audio(name):
    return send_from_directory('outputs', name)
```
Note: gTTS needs an internet connection.

## POST /api/faq/ask
Request (JSON): `{ "query": "...", "language": "bn" }`

Match found:
```json
{ "matched": true, "question": "Closest FAQ question", "answer": "Answer in the requested language", "confidence": 0.9 }
```
No match:
```json
{ "matched": false, "answer": null, "confidence": 0 }
```

## POST /api/feedback
Request (JSON): `{ "feature": "read_document" | "translate" | "faq", "helpful": true, "details": {} }`
Response: `{ "status": "ok" }`
Simplest version: append each request as one line to `logs/feedback.jsonl`.
