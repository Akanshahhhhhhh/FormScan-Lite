r"""Make the audio for every FAQ answer ahead of the demo.

The voice (gTTS) needs internet to make NEW audio. Audio that is already made is
saved in backend\outputs\audio and plays with NO internet. Run this script once
with internet on, and the FAQ voice will work on demo day even if the Wi-Fi fails.

Run from the backend folder:
    ..\venv\Scripts\python.exe make_demo_audio.py              (make the audio)
    ..\venv\Scripts\python.exe make_demo_audio.py --dry-run    (only count, no internet)

You can run it again any time. Audio that already exists is not made twice.
"""
import json
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
FAQ_FILE = BACKEND_DIR / "data" / "faqs" / "faqs.json"
LANGUAGES = ("en", "bn", "ta")
MAX_CHARS = 3000  # same limit as POST /api/tts
PAUSE_SECONDS = 1.0  # small pause so Google does not block us
RETRIES = 2


def collect_jobs(entries):
    """One job per (FAQ id, language) that has an answer."""
    jobs = []
    for entry in entries:
        for lang in LANGUAGES:
            text = (entry.get("answer") or {}).get(lang)
            if text and text.strip():
                jobs.append((entry["id"], lang, text))
    return jobs


def main():
    dry_run = "--dry-run" in sys.argv
    os.chdir(BACKEND_DIR)
    entries = json.loads(FAQ_FILE.read_text(encoding="utf-8"))
    jobs = collect_jobs(entries)

    counts = {lang: sum(1 for _, l, _ in jobs if l == lang) for lang in LANGUAGES}
    print(f"FAQ entries: {len(entries)}")
    print(f"Audio files needed: {len(jobs)}  (en {counts['en']}, bn {counts['bn']}, ta {counts['ta']})")
    too_long = [(i, l, len(t)) for i, l, t in jobs if len(t) > MAX_CHARS]
    for faq_id, lang, size in too_long:
        print(f"  TOO LONG (over {MAX_CHARS} characters): {faq_id} {lang} has {size}")
    if dry_run:
        print("Dry run: nothing was made.")
        return 0

    sys.path.insert(0, str(BACKEND_DIR))
    from app import app  # the real app, so the audio is saved exactly as the server saves it

    client = app.test_client()
    made, already, failed = 0, 0, []
    for number, (faq_id, lang, text) in enumerate(jobs, start=1):
        label = f"[{number}/{len(jobs)}] {faq_id} {lang}"
        if len(text) > MAX_CHARS:
            failed.append((faq_id, lang, "too long"))
            print(f"{label}  SKIPPED (too long)")
            continue
        result = None
        for attempt in range(1, RETRIES + 2):
            resp = client.post("/api/tts", json={"text": text, "language": lang})
            if resp.status_code == 200:
                result = resp.get_json()
                break
            if attempt <= RETRIES:
                time.sleep(3)
        if result is None:
            code = (resp.get_json() or {}).get("code", resp.status_code)
            failed.append((faq_id, lang, code))
            print(f"{label}  FAILED ({code})")
            continue
        if result.get("cached"):
            already += 1
            print(f"{label}  already made")
        else:
            made += 1
            print(f"{label}  made")
            time.sleep(PAUSE_SECONDS)

    print()
    print(f"Made now: {made}")
    print(f"Already made before: {already}")
    print(f"Failed or skipped: {len(failed)}")
    for faq_id, lang, why in failed:
        print(f"  {faq_id} {lang}: {why}")
    if failed:
        print("If the failures say tts_failed, check the internet and run the script again.")
        return 1
    print("ALL DONE. The FAQ voice now works without internet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
