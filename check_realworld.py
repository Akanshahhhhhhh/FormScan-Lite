"""
FormScan-Lite — real-world evaluation set checker.
Usage (from project root):
    python check_realworld.py data/real_world/bengali
    python check_realworld.py data/real_world/bengali --leak-check data/bengali

Expects <folder>/ground_truth.csv with columns:
    filename,text,source,condition
  filename  : image file in the same folder (e.g. bn_rw_001.jpg)
  text      : manually checked transcription (Bengali)
  source    : where the image came from (own photo / public notice / licence)
  condition : short note on quality (clean, low_light, skewed, blurred, ...)
Reports missing/extra images, empty or non-Bengali text, duplicates and
(optionally) byte-identical copies of IIIT train/val/test images.
"""
import argparse
import csv
import hashlib
import re
from pathlib import Path

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
REQUIRED = ["filename", "text", "source", "condition"]
BENGALI = re.compile(r"[ঀ-৿]")


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--target", type=int, default=20)
    ap.add_argument("--leak-check", metavar="DATASET_DIR", help="e.g. data/bengali (slow: hashes every image)")
    args = ap.parse_args()

    folder = Path(args.folder)
    csv_path = folder / "ground_truth.csv"
    problems = []
    if not csv_path.is_file():
        raise SystemExit(f"Missing {csv_path}")

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing_cols = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing_cols:
            raise SystemExit(f"ground_truth.csv is missing columns: {missing_cols}")
        rows = [(reader.line_num, r) for r in reader]  # line_num handles multi-line cells

    seen, ok = set(), 0
    for n, r in rows:
        name = (r["filename"] or "").strip()
        tag = f"line {n} ({name or 'no filename'})"
        bad = False
        if not name:
            problems.append(f"{tag}: empty filename"); continue
        if name in seen:
            problems.append(f"{tag}: listed twice"); bad = True
        seen.add(name)
        if not (folder / name).is_file():
            problems.append(f"{tag}: image file not found"); bad = True
        text = (r["text"] or "").strip()
        if not text or text.upper() == "TODO":
            problems.append(f"{tag}: transcription missing"); bad = True
        elif not BENGALI.search(text):
            problems.append(f"{tag}: transcription has no Bengali characters"); bad = True
        if not (r["source"] or "").strip():
            problems.append(f"{tag}: source/permission not recorded"); bad = True
        ok += not bad

    images = {p.name for p in folder.iterdir() if p.suffix.lower() in IMG_EXT}
    for extra in sorted(images - seen):
        problems.append(f"{extra}: image in folder but not in ground_truth.csv")

    hashes = {}
    for name in sorted(seen & images):
        hashes.setdefault(md5(folder / name), []).append(name)
    for names in hashes.values():
        if len(names) > 1:
            problems.append(f"identical image files: {names}")

    if args.leak_check:
        ds = {md5(p) for p in Path(args.leak_check).rglob("*") if p.suffix.lower() in IMG_EXT}
        for h, names in hashes.items():
            if h in ds:
                problems.append(f"{names}: identical to an image in {args.leak_check} (leakage)")

    print(f"{csv_path}\n  rows: {len(rows)}   valid: {ok}   images in folder: {len(images)}   target: {args.target}")
    print("  conditions:", sorted({(r['condition'] or '').strip() for _, r in rows}))
    for p in problems:
        print("  - " + p)
    if ok < args.target:
        print(f"  SHORTFALL: {args.target - ok} more valid images needed.")
    elif not problems:
        print("  All good.")


if __name__ == "__main__":
    main()
