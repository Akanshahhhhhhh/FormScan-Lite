"""
Build the character set for one script from its TRAIN annotation file.

Run once per script, before training. Writes a JSON that training,
evaluation and the Flask backend all load, so every character keeps the
same index everywhere.

Usage (from the repo root):
    python src/charset.py --script bengali
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.common import gt_path, load_cfg, read_gt, repo_path  # noqa: E402


def build(script, cfg):
    shared = cfg["shared"]
    gt = gt_path(cfg, script, "train")
    if not gt.exists():
        raise FileNotFoundError(f"Train annotation not found: {gt}\nCheck gt_train in config.yaml.")

    counter, n = Counter(), 0
    for _, label in read_gt(gt, shared["unicode_norm"]):
        counter.update(label)
        n += 1

    chars = sorted(counter)                   # codepoint order: reproducible
    itos = ["<blank>"] + chars                # index 0 = CTC blank
    stoi = {c: i for i, c in enumerate(itos)}

    out = repo_path(cfg, cfg["scripts"][script]["charset_out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "script": script,
        "unicode_norm": shared["unicode_norm"],
        "blank_index": shared["blank_index"],
        "num_classes": len(itos),
        "itos": itos,
        "stoi": stoi,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"script        : {script}")
    print(f"train samples : {n}")
    print(f"unique chars  : {len(chars)}")
    print(f"num_classes   : {len(itos)}  (chars + CTC blank)")
    print(f"written to    : {out}")
    print("\nRarest 15 characters (inspect for junk):")
    for c, k in counter.most_common()[-15:]:
        print(f"  {c!r}  U+{ord(c):04X}  {k}x")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True, choices=["bengali", "kannada"])
    ap.add_argument("--config", default="config.yaml")
    a = ap.parse_args()
    build(a.script, load_cfg(a.config))
