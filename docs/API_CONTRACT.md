# FormScan-Lite — API Contract (backend)

Written by Neharin (Backend Lead). Last updated: 22 Oct 2026.
Branch: `feature/backend-setup`

**Base URL (development):** `http://127.0.0.1:5000`
**CORS:** enabled for all origins (development only).
**Format:** JSON responses. Every error has an `error` field with a plain message.

## Status

| Endpoint | Status |
|---|---|
| `POST /api/ocr` | Built and tested |
| `POST /api/translate` | Built and tested |
| `POST /api/tts` | Planned (Week 3) |
| `POST /api/feedback` | Planned (Week 3) |
| `POST /api/faq` | Planned (Week 4) |
| `GET /api/health` | Planned |

The endpoint names above are the real ones. Older planning documents used longer names
(`/api/ocr/extract`, `/api/translate/translate`, `/api/tts/generate`, `/api/faq/ask`).
**Please use the names in this table.**

Language codes everywhere: `en` (English), `bn` (Bengali), `ta` (Tamil).

---

## POST /api/ocr — read text from an image

**Request:** `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `image` | file | the document photo |
| `language` | text | `bn`, `ta` or `en` — the language written in the image |

**Success (200):**

```json
{
  "text": "பிறப்புச் சான்றிதழ்",
  "confidence": 0.53,
  "engine": "tesseract"
}
```

- `confidence` is a number from 0 to 1. Seen so far on real handwritten samples: Tamil about 0.53, Bengali about 0.33.
  The two engines do not measure confidence in exactly the same way, so show it as a hint ("check the text"), not as a precise percentage.
- `engine` is `tesseract` for Tamil and `easyocr` for Bengali and English.
- The response may contain extra fields. Ignore the ones you don't use.
- Handwriting is hard. Always let the user edit the text before translating.

**Errors:** `400` (no image, empty file name, missing or unsupported `language`) and `500` (OCR failed).
Body: `{"error": "message"}`.

**Not enforced yet (planned):** only png / jpg / jpeg, maximum 5 MB.

---

## POST /api/translate — translate text

**Request:** JSON

```json
{
  "text": "Please bring your birth certificate to the panchayat office.",
  "source_lang": "en",
  "target_lang": "ta"
}
```

**Success (200):**

```json
{
  "translated_text": "தயவுசெய்து உங்கள் பிறப்புச் சான்றிதழை பஞ்சாயத்து அலுவலகத்திற்கு கொண்டு வாருங்கள்.",
  "source_lang": "en",
  "target_lang": "ta",
  "model": "ai4bharat/indictrans2-en-indic-dist-200M"
}
```

- All six directions work: `en→bn`, `en→ta`, `bn→en`, `ta→en`, `bn→ta`, `ta→bn`.
  Bengali ↔ Tamil is translated directly (no English in between).
- Source and target must be different.
- Maximum 5000 characters per request.
- Several lines and several sentences are fine. Line breaks are kept.
- Numbers, phone numbers and web addresses are protected and restored.

**Errors:** body is `{"error": "message", "code": "short_code"}`

| HTTP | `code` | When |
|---|---|---|
| 400 | `bad_request` | body is not JSON |
| 400 | `missing_text` | empty or missing `text` |
| 400 | `text_too_long` | more than 5000 characters |
| 400 | `unsupported_language` | language is not `en`, `bn` or `ta` |
| 400 | `same_language` | source and target are the same |
| 503 | `model_load_failed` | the translation model could not be loaded on the server |
| 500 | `translation_failed` | anything else went wrong |

### Speed — please read (frontend)

- The first request for each direction after the server starts is **slow**, because the model loads into memory.
  Normally about 20–60 seconds. The very first time on a new computer it also downloads the models (about 1 GB each), which can take several minutes.
- After that, one request usually takes 1–6 seconds.
- Please use a long timeout for this call (at least 5 minutes), and show a message such as "Loading the translation model, please wait…".
- The server translates one request at a time.

### Known limits

- The model can drop small words. Example seen: in "The fee is Rs. 250", the Tamil result left out "Rs.".
  Show the translation as editable text and avoid presenting it as 100% accurate.
- Bengali output may use the word *shongshapatro* (শংসাপত্র) for "certificate" where documents often use *shonod* (সনদ). Both are correct.

---

## Planned endpoints (not built yet)

Shapes may change. Build against mocks for these.

- `POST /api/tts` — text and language in, audio file (or audio URL) out. Needs internet (gTTS).
- `POST /api/feedback` — user marks a result as helpful or not helpful.
- `POST /api/faq` — question in `en`, `bn` or `ta`; answer and confidence out; honest "I don't have information about this" when nothing matches.

## Mock data for demo mode

OCR:

```json
{"text": "জন্ম সনদের জন্য আবেদন", "confidence": 0.41, "engine": "easyocr"}
```

Translate:

```json
{"translated_text": "What documents are required for a birth certificate?",
 "source_lang": "bn", "target_lang": "en", "model": "mock"}
```
