"""
FormScan-Lite — Bengali OCR evaluation (Akansha)
Runs EasyOCR on a sample of the IIIT-INDIC-HW-WORDS Bengali test split
and reports CER (character error rate) and word accuracy.

Usage (from project root):
    python eval_bengali_ocr.py --labels data/bengali/test.txt --images-root data/bengali --n 300

Each line of the labels file is expected to be:  <image_path> <ground_truth_word>
"""
import argparse
import csv
import random
import time
import unicodedata
from pathlib import Path


def levenshtein(a, b):
    """Edit distance between two strings (character level)."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


def norm(s):
    # NFC normalisation matters for Bengali: the same glyph can be encoded two ways
    return unicodedata.normalize("NFC", s).strip()



def load_labels(labels_path, images_root):
    import json

    samples = []
    labels_path = Path(labels_path)
    images_root = Path(images_root)

    if labels_path.suffix.lower() == ".json":
        with open(labels_path, encoding="utf-8") as f:
            labels = json.load(f)

        for rel_path, label in labels.items():
            img = images_root / rel_path
            if img.is_file():
                samples.append((img, norm(label)))
    elif labels_path.suffix.lower() == ".csv":
        # Real-world set: ground_truth.csv with columns filename,text.
        # Multi-line documents: collapse whitespace so it matches EasyOCR's " "-joined output.
        import csv as _csv
        with open(labels_path, encoding="utf-8-sig", newline="") as f:
            for row in _csv.DictReader(f):
                img = images_root / row["filename"]
                samples.append((img, norm(" ".join(row["text"].split()))))
    else:
        with open(labels_path, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) != 2:
                    continue

                rel_path, label = parts
                img = images_root / rel_path
                samples.append((img, norm(label)))

    return samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True, help="Path to test.txt")
    ap.add_argument("--images-root", required=True, help="Folder the image paths are relative to")
    ap.add_argument("--n", type=int, default=300, help="Number of samples (0 = all)")
    ap.add_argument("--lang", default="bn", help="EasyOCR language code (bn or ta)")
    ap.add_argument("--gpu", action="store_true", help="Use GPU if available")
    ap.add_argument("--out", default="results/ocr_eval_bn.csv")
    args = ap.parse_args()

    import easyocr  # imported here so --help works without it installed

    samples = load_labels(args.labels, args.images_root)
    if not samples:
        raise SystemExit("No samples loaded — check the labels file format and paths.")
    missing = [s for s in samples[:20] if not s[0].exists()]
    if missing:
        raise SystemExit(f"Image not found: {missing[0][0]}  — check --images-root")

    random.seed(42)
    if args.n and args.n < len(samples):
        samples = random.sample(samples, args.n)

    print(f"Loading EasyOCR ({args.lang})... first run downloads the model.")
    reader = easyocr.Reader([args.lang, "en"], gpu=args.gpu)

    total_edits = total_chars = exact = 0
    rows = []
    t0 = time.time()
    for i, (img, ref) in enumerate(samples, 1):
        result = reader.readtext(str(img), detail=1, paragraph=False)
        pred = norm(" ".join(text for _, text, _ in result))
        conf = sum(c for _, _, c in result) / len(result) if result else 0.0
        edits = levenshtein(pred, ref)
        total_edits += edits
        total_chars += len(ref)
        exact += int(pred == ref)
        rows.append([str(img), ref, pred, edits, round(conf, 3)])
        if i % 25 == 0:
            print(f"  {i}/{len(samples)}  running CER = {total_edits / total_chars:.3f}")

    cer = total_edits / total_chars
    word_acc = exact / len(samples)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["image", "ground_truth", "prediction", "edit_distance", "confidence"])
        w.writerows(rows)

    print("\n=== Results ===")
    print(f"Samples        : {len(samples)}")
    print(f"CER            : {cer:.3f}  ({cer * 100:.1f}%)")
    print(f"Word accuracy  : {word_acc:.3f}  (WER = {1 - word_acc:.3f})")
    print(f"Time           : {time.time() - t0:.0f}s")
    print(f"Per-sample CSV : {args.out}")


if __name__ == "__main__":
    main()