"""
FormScan-Lite — FAQ file checker.
Usage (from project root):
    python check_faqs.py backend/data/faqs/bengali_faqs.json
Flags unfinished entries (TODO), missing/unofficial sources, duplicate ids,
answers that aren't in Bengali/Tamil script, and weak keyword lists.
"""
import json
import re
import sys
from collections import Counter
from urllib.parse import urlparse

REQUIRED = ["id", "category", "question", "keywords", "answer", "source", "verified_on"]
SCRIPT = {"bengali": r"[ঀ-৿]", "tamil": r"[஀-௿]"}
OFFICIAL = (".gov.in", ".nic.in")


def main(path):
    data = json.load(open(path, encoding="utf-8"))
    lang = next((k for k in SCRIPT if k in path.lower()), None)
    problems, done = [], 0

    ids = Counter(e.get("id") for e in data)
    for dup, n in ids.items():
        if n > 1:
            problems.append(f"duplicate id: {dup} (x{n})")

    for e in data:
        eid = e.get("id", "?")
        missing = [f for f in REQUIRED if f not in e]
        if missing:
            problems.append(f"{eid}: missing fields {missing}")
            continue
        todo = [f for f in REQUIRED if e[f] == "TODO"]
        if todo:
            problems.append(f"{eid}: still TODO -> {', '.join(todo)}")
            continue
        host = urlparse(e["source"]).netloc
        if not host.endswith(OFFICIAL):
            problems.append(f"{eid}: source is not a .gov.in/.nic.in site ({host or e['source']})")
        if len(e["keywords"]) < 3:
            problems.append(f"{eid}: add at least 3 keywords")
        if lang and not re.search(SCRIPT[lang], e["answer"]):
            problems.append(f"{eid}: answer is not in {lang} script")
        if len(e["answer"]) > 600:
            problems.append(f"{eid}: answer is long ({len(e['answer'])} chars) — keep it short for TTS")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["verified_on"]):
            problems.append(f"{eid}: verified_on should be YYYY-MM-DD")
        if not any(p for p in problems if p.startswith(eid + ":")):
            done += 1

    print(f"{path}\n  entries: {len(data)}   complete: {done}   categories: {dict(Counter(e.get('category') for e in data))}")
    for p in problems:
        print("  - " + p)
    if not problems:
        print("  All good. Ready to commit.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "backend/data/faqs/bengali_faqs.json")