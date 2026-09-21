"""
Shared dataset + preprocessing for FormScan-Lite.

NEITHER teammate edits this file alone. It defines the preprocessing
contract: change the resize or normalisation here and the two models stop
being comparable and the Flask backend breaks.

Usage:
    from src.common import load_cfg
    from src.dataset import IndicWordDataset, ctc_collate

    cfg = load_cfg("config.yaml")
    train_ds = IndicWordDataset("bengali", "train", cfg)
"""

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from .common import gt_path, load_exclude, read_gt, repo_path


def preprocess_image(img, h, w, mean, std):
    """
    Grayscale -> aspect-preserving resize to height h -> right-pad (white)
    or crop to width w -> normalise. Returns float32 array (1, h, w).

    Padding rather than squashing: Indic words vary a lot in length, and
    stretching short words distorts the glyphs.
    """
    img = img.convert("L")
    ow, oh = img.size
    new_w = max(1, int(round(ow * (h / oh))))
    img = img.resize((new_w, h), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    if new_w < w:
        arr = np.concatenate([arr, np.ones((h, w - new_w), np.float32)], axis=1)
    elif new_w > w:
        arr = arr[:, :w]
    return ((arr - mean) / std)[None, :, :]


def load_charset(cfg, script):
    p = repo_path(cfg, cfg["scripts"][script]["charset_out"])
    cs = json.loads(p.read_text(encoding="utf-8"))
    if cs["unicode_norm"] != cfg["shared"]["unicode_norm"]:
        raise ValueError("config unicode_norm != charset file. Rebuild with src/charset.py.")
    return cs


class IndicWordDataset(Dataset):
    """One class for both scripts; only the charset JSON differs."""

    def __init__(self, script, split, cfg, limit=None):
        assert split in ("train", "val", "test")
        sh = cfg["shared"]
        self.h, self.w = sh["img_height"], sh["img_width"]
        self.mean, self.std = sh["normalize_mean"], sh["normalize_std"]

        cs = load_charset(cfg, script)
        self.stoi, self.itos = cs["stoi"], cs["itos"]
        self.num_classes, self.blank = cs["num_classes"], cs["blank_index"]

        gt = gt_path(cfg, script, split)
        self.img_dir = gt.parent                     # path rule
        exclude = load_exclude(cfg, script, split)

        # Words with characters unseen in train:
        #   train/val -> skipped (CTC cannot learn or score them)
        #   test      -> KEPT. Dropping them would remove the hardest words
        #                and inflate reported accuracy. The raw label is kept
        #                for CER, so unseen characters count as errors.
        self.is_test = split == "test"
        self.samples, n_excl, n_oov = [], 0, 0
        for rel, label in read_gt(gt, sh["unicode_norm"]):
            if rel in exclude:
                n_excl += 1
                continue
            if not all(c in self.stoi for c in label):
                n_oov += 1
                if not self.is_test:
                    continue
            self.samples.append((rel, label))
            if limit and len(self.samples) >= limit:
                break

        oov_note = "kept, scored as errors" if self.is_test else "skipped"
        print(f"[{script}/{split}] samples {len(self.samples)}  "
              f"excluded {n_excl}  unseen-char words {n_oov} ({oov_note})")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        rel, label = self.samples[i]
        x = preprocess_image(Image.open(self.img_dir / rel), self.h, self.w, self.mean, self.std)
        y = [self.stoi[c] for c in label if c in self.stoi]   # only differs on test OOV
        return torch.from_numpy(x), torch.tensor(y, dtype=torch.long), len(y), label


def ctc_collate(batch):
    """Pack variable-length targets for nn.CTCLoss."""
    imgs, targets, lengths, labels = zip(*batch)
    return (torch.stack(imgs, 0), torch.cat(targets, 0),
            torch.tensor(lengths, dtype=torch.long), list(labels))


def ctc_greedy_decode(logits, itos, blank=0):
    """
    logits: (T, B, C). Returns decoded strings. Used in training eval AND in
    the Flask backend, so both produce identical text.
    """
    if logits.dim() != 3:
        raise ValueError("expected 3D logits of shape (T, B, C)")
    if logits.shape[2] != len(itos):
        raise ValueError(f"logits have {logits.shape[2]} classes but charset has "
                         f"{len(itos)}: wrong charset JSON for this model.")
    ids = logits.argmax(-1).transpose(0, 1).cpu().numpy()   # (B, T)
    out = []
    for seq in ids:
        prev, chars = -1, []
        for k in seq:
            if k != prev and k != blank:
                chars.append(itos[k])
            prev = k
        out.append("".join(chars))
    return out
