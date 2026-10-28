# FormScan-Lite Backend API Contract

Last updated: 2026-10-25. Backend: Flask, `http://127.0.0.1:5000` (CORS is on).
Languages used everywhere: `en` (English), `bn` (Bengali), `ta` (Tamil).

Status: **OCR, Translate, TTS, Audio, Feedback, FAQ and Health are built and tested.**

The React frontend uses its own URL names (for example `/api/ocr/extract`). Those are built in too: see **section 7** at the end. The frontend code needs no change.

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

Note: the list has 30 entries so far. All 30 entries were written from official pages, but they still need a human check, and the Bengali and Tamil text still needs a native speaker's check. Entries faq-016 and faq-017 are about Tamil Nadu and exist only in `en` and `ta`; faq-018 and faq-019 are about West Bengal and exist only in `en` and `bn`. So `GET /api/faq/questions` returns a different number of questions per language. The `category` of an entry is one of: `certificates`, `identity`, `forms`, `voting`, `travel`, `schemes`, `rights`. More entries will be added.

---

## 6. Health check

`GET /api/health`

Success `200`:

```json
{ "status": "ok" }
```

- Use it to check that the backend is running (for example when the app opens, or to show a "server is offline" message).
- Only `GET` works. Other methods give `405`.

---

## 7. Endpoints used by the React frontend

`frontend/src/services/api.js` calls these URLs. They are built into the backend and work like the endpoints above, with the field names the frontend expects. Errors are exactly the same as in sections 1 to 6: `{ "error": "...", "code": "..." }` with the same HTTP codes. The frontend shows `error`.

| Frontend calls | Same as | What is different |
|---|---|---|
| `POST /api/ocr/extract` | `POST /api/ocr` (section 1) | The answer also has `"language"`. It still has `confidence_level`, `warning` and `engine`. |
| `POST /api/translate/translate` | `POST /api/translate` (section 2) | Send `src_lang` and `tgt_lang` (not `source_lang`, `target_lang`). The answer has `src_lang` and `tgt_lang`. |
| `POST /api/tts/generate` | `POST /api/tts` (section 3) | Same body and answer. `audio_url` is a path like `/api/audio/abc.mp3`, so put the base URL in front. |
| `POST /api/faq/ask` | `POST /api/faq` (section 5) | Send `query` (not `question`). The answer has `matched`, `question`, `answer`, `confidence`, and also `id` and `suggestions`. |
| `POST /api/feedback` | `POST /api/feedback` (section 4) | The frontend body is also accepted, see below. |
| `GET /api/health` | `GET /api/health` (section 6) | No difference. |

**FAQ answer for the frontend:**

```json
{ "matched": true, "id": "faq-001", "question": "How do I apply for a birth certificate?",
  "answer": "Apply at the local registrar office ...", "confidence": 0.8, "suggestions": [] }
```

When nothing matches: `"matched": false`, `"question": null`, `"answer": null`, `"confidence": 0`, and `suggestions` can show tappable questions.

**Feedback body from the frontend:**

```json
{ "feature": "read_document", "helpful": true, "details": { "language": "bn", "comment": "Very clear" } }
```

- `feature` can be `read_document` (saved as `ocr`), `translate`, `tts` or `faq`.
- `helpful` must be `true` or `false`.
- `details` is optional. Only `language` (`en`, `bn`, `ta`) and `comment` (text, max 500 characters) are saved.
- The answer is `200` `{ "status": "ok" }`. The body from section 4 (with `rating`) still works and answers `201`.

**Limits to remember in the frontend:** the largest image is **5 MB** (not 10 MB), and OCR answers for new images can take a while the first time, so keep the 120 second timeout.
