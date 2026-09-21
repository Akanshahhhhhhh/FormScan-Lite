"""
Shared helpers: config loading, path resolution, annotation parsing,
and exclusion lists. Used by charset.py, make_excludes.py and dataset.py.
"""

import unicodedata
from pathlib import Path

import yaml

SPLITS = ("train", "val", "test")


def load_cfg(path="config.yaml"):
    """Load config and remember where it lives, so relative paths resolve
    from the repo root no matter which folder you run a script from."""
    path = Path(path).resolve()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["_repo_root"] = path.parent
    return cfg


def repo_path(cfg, p):
    """Resolve a config path relative to the repo root."""
    p = Path(p)
    return p if p.is_absolute() else cfg["_repo_root"] / p


def gt_path(cfg, script, split):
    return repo_path(cfg, cfg["scripts"][script][f"gt_{split}"])


def exclude_path(cfg, script, split):
    return repo_path(cfg, cfg["shared"]["exclude_dir"]) / f"{script}_{split}_exclude.txt"


def read_gt(gt_file, norm="NFC"):
    """
    Yield (relative_image_path, label) from an annotation file.

    Format: "<relative/path.jpg><TAB or spaces><label>", UTF-8.
    Image location rule: Path(gt_file).parent / relative_image_path
    """
    gt_file = Path(gt_file)
    with open(gt_file, encoding="utf-8-sig") as f:      # -sig strips a BOM if present
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            if "\t" in line:
                img, label = line.split("\t", 1)
            else:
                parts = line.split(None, 1)
                if len(parts) != 2:
                    raise ValueError(
                        f"{gt_file.name} line {lineno} has no label: {line!r}\n"
                        "This annotation file is unlabelled or malformed."
                    )
                img, label = parts
            label = unicodedata.normalize(norm, label.strip())
            if not label:
                raise ValueError(f"{gt_file.name} line {lineno}: empty label")
            yield img.strip().replace("\\", "/"), label


def load_exclude(cfg, script, split):
    """Set of relative image paths to skip for this split (empty if no file)."""
    p = exclude_path(cfg, script, split)
    if not p.exists():
        return set()
    return {
        l.strip().replace("\\", "/")
        for l in p.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.startswith("#")
    }
