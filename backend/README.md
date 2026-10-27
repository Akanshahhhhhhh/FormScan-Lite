# FormScan-Lite Backend

The backend of **FormScan-Lite**, a reader for Indian government documents in English, Bengali and Tamil. It reads text from a photo of a form (OCR), translates it, reads it aloud (text to speech) and answers common questions about government paperwork (FAQ chatbot).

Backend: Neharin. Frontend (React): Akansha.

Status date: 2026-10-25. Everything listed under "What works" has been run and tested on a Windows laptop.

## What works

| Feature | Endpoint | How it works |
|---|---|---|
| Read text from an image | `POST /api/ocr` | EasyOCR for Bengali and English, Tesseract for Tamil. Returns a confidence score (0 to 1) and a level (low, medium, high) with a warning when the text may be wrong. |
| Translate | `POST /api/translate` | IndicTrans2 distilled models. All directions between English, Bengali and Tamil. |
| Text to speech | `POST /api/tts`, `GET /api/audio/<file>` | Google gTTS. Audio files are saved, so the same text never needs to be made twice. |
| FAQ chatbot | `POST /api/faq`, `GET /api/faq/questions` | Matches the question to 30 hand-written FAQ entries (character 3-gram TF-IDF, no big libraries). |
| Feedback | `POST /api/feedback` | Saves a helpful / not helpful vote. No document text is stored. |
| Health check | `GET /api/health` | Returns `{"status": "ok"}`. |

The full request and response shapes, with examples and all error codes, are in [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md). Every error has the same shape: `{ "error": "message", "code": "short_code" }`.

## What you need before you start

- Windows, Python 3.13 and a virtual environment (this project uses a `venv` folder in the main project folder).
- **Tesseract OCR** with the Tamil language file (`tam.traineddata`), installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- A **Hugging Face account**. The three IndicTrans2 models are gated: open each model page, accept the conditions, then run `hf auth login` once.
  - `ai4bharat/indictrans2-en-indic-dist-200M`
  - `ai4bharat/indictrans2-indic-en-dist-200M`
  - `ai4bharat/indictrans2-indic-indic-dist-320M`
- **Internet** the first time (the models download), and any time new audio is made.

## Install and run

Use the **Command Prompt** (PowerShell blocks the virtual environment by default). From the main project folder:

```
venv\Scripts\activate
cd backend
pip install -r requirements.txt
python app.py
```

The server starts at `http://127.0.0.1:5000`. Check it by opening `http://127.0.0.1:5000/api/health` in a browser.

Good to know:
- The first Bengali/English OCR request and the first translation in each direction are slow (models load, about 20 seconds). After that translation takes about 1 to 6 seconds. The frontend should show a spinner and allow a timeout of at least 60 seconds.
- On the project laptop, one Windows security setting (Windows Application Control) blocks a library file used by EasyOCR, and the server was first started in an Administrator window. It is not confirmed yet whether this is still needed. If the server stops with a DLL error, try an Administrator Command Prompt.

## Run the tests

From the `backend` folder:

```
python -m pip install pytest
python -m pytest
```

This runs 46 fast tests in about 2 seconds (no internet, no models). To also run the slow tests (real translation in all 6 directions and real audio), add `--run-slow`. They need internet and take about 90 seconds:

```
python -m pytest --run-slow
```

The tests are in `backend/tests/`. The test that saves a feedback vote puts `feedback.jsonl` back exactly as it was.

## Demo audio (works without internet)

Making new audio needs internet. To make sure the FAQ voice works on demo day even if the Wi-Fi fails, make all the FAQ answer audio once, with internet on:

```
python make_demo_audio.py
```

It makes about 86 audio files (one for each FAQ answer in each language it has) and saves them in `backend/outputs/audio`. Run it again after any change to the FAQ; files that already exist are not made twice. Use `--dry-run` to only count them. The audio files stay on the laptop that made them. This covers FAQ answers only: voice for a newly scanned document still needs internet.

## Folder guide

```
backend/
  app.py                 starts the server and registers all routes
  config.py              settings
  routes/                one file per endpoint group (ocr, translate, tts, feedback, faq, health)
  services/              the real work: OCR, translation, text to speech, FAQ matching
  data/faqs/faqs.json    the FAQ entries (English, Bengali, Tamil)
  outputs/audio/         saved audio files
  tests/                 pytest tests
  make_demo_audio.py     makes the FAQ audio ahead of the demo
docs/API_CONTRACT.md     full API description for the frontend
```

## FAQ data

`backend/data/faqs/faqs.json` has 30 entries, written from official government pages. Each entry has a `status`, a `checked` date and a list of `sources`.

- All entries are marked "researched, needs human check". Nobody has checked them yet against the live official pages.
- Entries `faq-016` and `faq-017` are about Tamil Nadu (English and Tamil only). Entries `faq-018` and `faq-019` are about West Bengal (English and Bengali only).
- The Bengali and Tamil text was written by an AI assistant and **must be checked by a native speaker before the demo**.
- Fees and rules that change often (for example the Aadhaar update fee) must be checked again on the official site before the demo.

## Known limits

- **Handwriting vs printed forms.** The datasets used for this project are handwritten, but real government forms are mostly printed. Real handwritten test samples scored low confidence (Bengali 0.33, Tamil 0.53), and the app shows a warning when confidence is low. Testing on real printed forms and tuning the confidence thresholds is still to do.
- **Tamil OCR uses Tesseract.** EasyOCR's Tamil model has a known, unresolved bug (open issues on the EasyOCR GitHub), so Tesseract is used for Tamil.
- **Translation quality.** The meaning was correct in all tests, but small details can change. For example, "Rs." was dropped in one Tamil translation (the phone number was kept). Different words can be used for the same thing (for example certificate).
- **Voice quality.** The audio plays correctly, but it has not been checked by a native Bengali or Tamil speaker.
- **Internet.** New audio needs internet (see the demo audio section).
- **Not done yet.** Formal accuracy measurement (CER/WER for OCR, chrF for translation).
