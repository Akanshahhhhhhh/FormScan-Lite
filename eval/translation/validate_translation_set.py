"""
FormScan-Lite — validate the EN–BN translation evaluation set.
Usage (from project root):
    python eval/translation/validate_translation_set.py
    python eval/translation/validate_translation_set.py path/to/other_set.json
Checks structure only (fields, IDs, scripts, duplicates). It cannot judge
translation quality — that needs a fluent human reviewer.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT = Path(__file__).with_name("en_bn_public_service.json")
FIELDS = ["id", "category", "length", "en", "bn_reference", "reference_origin",
          "notes", "review_status", "reviewed_by", "reviewed_on"]
REQUIRED_TEXT = ["id", "category", "length", "en", "bn_reference", "reference_origin", "review_status"]
CATEGORIES = {"government_services", "documents", "public_health", "education",
              "transportation", "digital_services"}
LENGTHS = {"short", "medium", "complex"}
STATUSES = {"needs_review", "approved", "revised"}
ID_RE = re.compile(r"tr_bn_\d{3}")
BENGALI = re.compile(r"[ঀ-৿]")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def main(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Malformed JSON: {e}")
    if not isinstance(data, list):
        raise SystemExit("Top level must be a JSON list of records.")

    problems = []
    for i, r in enumerate(data):
        tag = r.get("id", f"record #{i + 1}") if isinstance(r, dict) else f"record #{i + 1}"
        if not isinstance(r, dict):
            problems.append(f"{tag}: not a JSON object"); continue
        missing = [f for f in FIELDS if f not in r]
        extra = [f for f in r if f not in FIELDS]
        if missing: problems.append(f"{tag}: missing fields {missing}")
        if extra: problems.append(f"{tag}: unexpected fields {extra}")
        for f in REQUIRED_TEXT:
            if f in r and (not isinstance(r[f], str) or not r[f].strip()):
                problems.append(f"{tag}: '{f}' is empty or not text")
        if not ID_RE.fullmatch(str(r.get("id", ""))):
            problems.append(f"{tag}: id should look like tr_bn_001")
        if r.get("category") not in CATEGORIES: problems.append(f"{tag}: unknown category {r.get('category')!r}")
        if r.get("length") not in LENGTHS: problems.append(f"{tag}: length must be one of {sorted(LENGTHS)}")
        if r.get("review_status") not in STATUSES: problems.append(f"{tag}: review_status must be one of {sorted(STATUSES)}")
        en, bn = str(r.get("en", "")), str(r.get("bn_reference", ""))
        if BENGALI.search(en): problems.append(f"{tag}: English source contains Bengali characters")
        if bn and not BENGALI.search(bn): problems.append(f"{tag}: Bengali reference has no Bengali characters")
        if r.get("review_status") in ("approved", "revised"):
            if not r.get("reviewed_by"): problems.append(f"{tag}: reviewed but 'reviewed_by' is empty")
            if not DATE_RE.fullmatch(str(r.get("reviewed_on") or "")): problems.append(f"{tag}: reviewed_on should be YYYY-MM-DD")
        elif r.get("reviewed_by") or r.get("reviewed_on"):
            problems.append(f"{tag}: has reviewer details but status is still needs_review")

    records = [r for r in data if isinstance(r, dict)]
    for field in ("id", "en", "bn_reference"):
        for value, n in Counter(r.get(field) for r in records).items():
            if value and n > 1:
                problems.append(f"duplicate {field} ({n}x): {str(value)[:60]}")

    status = Counter(r.get("review_status") for r in records)
    print(f"{path}")
    print(f"  records: {len(data)}")
    print(f"  categories: {dict(sorted(Counter(r.get('category') for r in records).items()))}")
    print(f"  lengths: {dict(sorted(Counter(r.get('length') for r in records).items()))}")
    print(f"  review status: {dict(status)}")
    for p in problems:
        print("  - " + p)
    if problems:
        sys.exit(1)
    print("  Structure OK.")
    if status.get("needs_review"):
        print(f"  NOTE: {status['needs_review']} reference(s) still need human review — "
              "do not report chrF from this set as final until they are approved.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
