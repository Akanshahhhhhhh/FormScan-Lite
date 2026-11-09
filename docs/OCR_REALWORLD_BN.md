# Bengali real-world OCR evaluation set (printed text)

Purpose: test whether OCR that works on the IIIT benchmark also works on real photos of printed Bengali public-service text, such as notices, forms, signs and pamphlets. This set is **evaluation only**. It must never be used for training or model selection.

Status (18 Oct 2026): tooling ready, **0 of 20 images collected**.

## Where things live

```
data/real_world/bengali/          (git-ignored, like all of data/)
├── ground_truth.csv              manifest: one row per image
├── bn_rw_001.jpg
└── ...
results/ocr_eval_bn_realworld.csv per-image predictions (separate from the IIIT baseline)
```

The IIIT benchmark baseline stays in `results/ocr_eval_bn.csv` (300 handwritten words, seed 42) and is not touched. Images stay out of git, because third-party photos may not be redistributable and the repo is public.

## Manifest columns

Copy `docs/realworld_ground_truth_template.csv` to `data/real_world/bengali/ground_truth.csv`. Save it as **CSV UTF-8**.

| Column | Required | What to write |
|---|---|---|
| `id` | recommended | `bn_rw_001` … `bn_rw_020`; never reuse or renumber |
| `filename` | yes | Image file in the same folder, e.g. `bn_rw_001.jpg` |
| `text` | yes | Exact visible Bengali text. Keep line breaks (Excel: Alt+Enter), punctuation and digits as printed. Leave out text you genuinely cannot read, and mention it in `condition` |
| `source` | yes | `own photo`, or the page title / author |
| `source_url` | recommended | File page URL (e.g. the Wikimedia Commons page), or empty for your own photo |
| `license` | recommended | Exactly as stated on the source page (e.g. `CC BY-SA 4.0`), or `own photo` |
| `retrieved_on` | recommended | Date taken or downloaded, `YYYY-MM-DD` |
| `condition` | yes | e.g. `clean`, `low_light`, `skewed`, `blurred`, `curved`, `mixed_script` |
| `transcribed_by` | recommended | Who typed and checked the text |
| `transcription_status` | recommended | `needs_review` until a fluent Bengali reader has compared the text against the image, then `verified` |

## What counts as a usable image

- Printed Bengali text in a real setting, ideally public-service: notices, forms, office or transport signs, health posters, pamphlets.
- About 20 images, with a deliberate mix of conditions: some clean, some angled, some in poor light or with a busy background.
- **Not allowed:** filled-in personal forms, ID cards, faces, phone numbers, addresses or anything identifying a private person. Crop or skip them.
- **Sources, in order of preference:**
  1. Your own photos of public notices and signs. Provenance is clear, so record `own photo`.
  2. Wikimedia Commons photos with a licence shown on the file page. Copy the licence exactly.
  3. Never use images from news sites or social media unless the licence clearly allows reuse.

## Run the checks and the evaluation

From the project root, with the venv active:

```
python check_realworld.py data/real_world/bengali --leak-check data/bengali
python eval_bengali_ocr.py --labels data/real_world/bengali/ground_truth.csv --images-root data/real_world/bengali --n 0
```

The first command checks the set. It flags missing images and transcriptions, duplicate files or IDs, missing licence or source, bad dates, images not listed in the manifest, and byte-identical copies of IIIT images. The second runs EasyOCR on every image. Results go to `results/ocr_eval_bn_realworld.csv` automatically, never to the baseline file.

## Metric and normalisation

- **CER** = total character edit distance ÷ total reference characters, over all images. This is the same formula as the baseline run.
- Before comparing, both texts are Unicode **NFC**-normalised and trimmed. Reference line breaks and repeated spaces are collapsed to single spaces, because EasyOCR returns its text pieces joined by spaces. Line breaks are still worth keeping in the manifest for future layout-aware OCR.
- Reading order: EasyOCR's order is used as is. On multi-column layouts, order mistakes count as character errors, so read CER on such images with care.
- The script's "word accuracy" is an exact match of the whole page, which is almost always 0 for full images. **Report CER for this set, not word accuracy.** Per-image errors are in the output CSV (`edit_distance` divided by the length of `ground_truth`).

## Limitations

- 20 images give a rough indication only, so report CER with the sample size and avoid strong comparisons.
- CER is meaningful only after every row is `verified`. Results from rows still marked `needs_review` are provisional.
- This covers printed text only. Handwriting performance comes from the IIIT benchmark (baseline CER 76.6%).

## Adding more examples later

Continue the numbering (`bn_rw_021`, …), fill every column, run `check_realworld.py` with `--target` set to the new total, and re-run the evaluation.
