# FormScan-Lite Backend API Contract

Last updated: 2026-10-25. Backend: Flask, `http://127.0.0.1:5000` (CORS is on).
Languages used everywhere: `en` (English), `bn` (Bengali), `ta` (Tamil).

Status: **OCR, Translate, TTS, Audio, Feedback, FAQ and Health are built and tested.**

## Error format (all endpoints)

Every error is JSON with a human message and a short code. Show `error` to the user, use `code` in your logic.

```json
{ "error": "Language must be en, bn or ta.", "code": "unsupported_language" }
```

---

## 1. OCR: read text from an image

`POST /api/ocr` (multipart/form-data)

| Field | Type | Notes |
|---|---|---|
| `image` | file | png, jpg or jpeg, max 5 MB |
| `language` | text | `bn`, `ta` or `en` |

Success `200`:

```json
{
  "text": "ফি ২৫০ টাকা",
  "confidence": 0.329,
  "confidence_level": "low",
  "warning": "Low confidence: the text may have mistakes. Please check it against the original document.",
  "engine": "easyocr"
}
```

- `confidence` is 0 to 1. `confidence_level` is `low`, `medium` or `high`. Levels are worked out per engine (EasyOCR for bn/en, Tesseract for ta), so use the level, not the raw number, to decide what to show.
- `warning` is `null` when the level is `high`. Show it under the text when it is not null.
- If no text is found: `text` is `""`, `confidence` is `0.0`, level is `low`, and `warning` says to try a clearer photo.
- The uploaded photo is deleted from the server right after reading.
- The first Bengali/English request is slow (OCR models load). Show a spinner.

Errors:

| code | HTTP | Meaning |
|---|---|---|
| `no_image` | 400 | no `image` file sent |
| `missing_language` | 400 | no `language` field |
| `unsupported_language` | 400 | language is not bn, ta or en |
| `empty_filename` | 400 | file has no name |
| `unsupported_file_type` | 400 | not png, jpg or jpeg |
| `file_too_large` | 413 | bigger than 5 MB |
| `invalid_image` | 400 | file is not a real image |
| `ocr_failed` | 500 | OCR crashed, ask the user to try another image |

---

## 2. Translate

`POST /api/translate` (JSON)

```json
{ "text": "The fee is Rs. 250.", "source_lang": "en", "target_lang": "ta" }
```

Success `200`:

```json
{
  "translated_text": "கட்டணம் 250 ரூபாய்.",
  "source_lang": "en",
  "target_lang": "ta",
  "model": "ai4bharat/indictrans2-en-indic-dist-200M"
}
```

- All directions work between en, bn and ta. Source and target must be different. Max 5000 characters.
- **Speed:** the first request for each direction loads a model (about 20 seconds, much longer on the very first run on a new machine because of downloads). After that it takes about 1 to 6 seconds. Use a spinner and set the request timeout to at least 60 seconds.

Errors:

| code | HTTP |
|---|---|
| `bad_request`, `missing_text`, `text_too_long`, `unsupported_language`, `same_language` | 400 |
| `translation_failed` | 500 |
| `model_load_failed` | 503 |

---

## 3. Text to speech

`POST /api/tts` (JSON)

```json
{ "text": "கட்டணம் 250 ரூபாய்.", "language": "ta" }
```

Success `200`:

```json
{
  "audio_url": "/api/audio/f545be66576d94acc4c891e01aab7dc3.mp3",
  "language": "ta",
  "characters": 20,
  "cached": false
}
```

- `audio_url` is a path. Put the base URL in front: `http://127.0.0.1:5000` + `audio_url`, then give it to the audio player.
- Same text + same language gives the same file (`cached: true`), instant and works without internet. A new text needs internet (Google gTTS).
- Max 3000 characters.

Errors:

| code | HTTP | Meaning |
|---|---|---|
| `missing_text` | 400 | text empty or missing |
| `unsupported_language` | 400 | language is not en, bn or ta |
| `text_too_long` | 400 | more than 3000 characters |
| `no_speakable_text` | 400 | text has nothing to read (for example only symbols) |
| `bad_request` | 400 | body is not JSON |
| `tts_failed` | 503 | could not make audio, usually no internet |

`GET /api/audio/<filename>` returns the mp3 (`audio/mpeg`). Unknown file gives `404` with code `not_found`.

---

## 4. Feedback

`POST /api/feedback` (JSON)

```json
{ "rating": "helpful", "feature": "translate", "language": "bn", "comment": "Very clear" }
```

| Field | Required | Allowed values |
|---|---|---|
| `rating` | yes | `helpful`, `not_helpful` |
| `feature` | yes | `ocr`, `translate`, `tts`, `faq` |
| `language` | no | `en`, `bn`, `ta` |
| `comment` | no | text, max 500 characters |

Success `201`:

```json
{ "status": "saved", "id": "06e52278cdf34cbdb4c08125726eaaf2" }
```

Errors (all 400 unless noted): `bad_request`, `invalid_rating`, `invalid_feature`, `unsupported_language`, `comment_too_long`, `save_failed` (500).
No document text is stored, only the vote.

---

## 5. FAQ chatbot

`POST /api/faq` (JSON)

```json
{ "question": "how can i get a birth certificate", "language": "en" }
```

Success `200` when a good match is found:

```json
{
  "matched": true,
  "id": "faq-001",
  "answer": "Apply at the local registrar office of the place where the birth happened ...",
  "matched_question": "How do I apply for a birth certificate?",
  "score": 0.806,
  "language": "en",
  "suggestions": [{ "id": "faq-005", "question": "What is an income certificate?" }]
}
```

When nothing matches well, it is still `200`, but `matched` is `false`, and `id`, `answer` and `matched_question` are `null`. Show "Sorry, I could not find an answer" and the `suggestions` as tappable questions:

```json
{
  "matched": false,
  "id": null,
  "answer": null,
  "matched_question": null,
  "score": 0.013,
  "language": "en",
  "suggestions": []
}
```

- The question and the answer are in the same language you send (`en`, `bn` or `ta`). Max 300 characters.
- Spelling differences are fine ("aadhar" finds Aadhaar).
- `score` is 0 to 1. The server decides `matched`, so just use that flag.

Errors: `missing_question`, `question_too_long`, `unsupported_language`, `bad_request` (all 400), `faq_unavailable` (500).

`GET /api/faq/questions?language=ta` returns every FAQ question in that language, to show as "common questions" buttons:

```json
{
  "language": "ta",
  "questions": [
    { "id": "faq-001", "question": "பிறப்புச் சான்றிதழுக்கு எப்படி விண்ணப்பிப்பது?", "category": "certificates" }
  ]
}
```

Note: the list has 19 entries so far. faq-002 to faq-005 are still samples; faq-001 and faq-006 to faq-019 come from official pages but still need a human check. Entries faq-016 and faq-017 are about Tamil Nadu and exist only in `en` and `ta`; faq-018 and faq-019 are about West Bengal and exist only in `en` and `bn`. So `GET /api/faq/questions` returns a different number of questions per language. More entries will be added.

---

## 6. Health check

`GET /api/health`

Success `200`:

```json
{ "status": "ok" }
```

- Use it to check that the backend is running (for example when the app opens, or to show a "server is offline" message).
- Only `GET` works. Other methods give `405`.
