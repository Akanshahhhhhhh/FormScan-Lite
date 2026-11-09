# Collecting the 20 Bengali real-world OCR images

Companion to `docs/OCR_REALWORLD_BN.md`. Target: `bn_rw_001` … `bn_rw_020`, printed Bengali only.

## Route A — your own photos (preferred: provenance is certain)

**What to photograph** (aim for this mix):

| Type | Count | Examples |
|---|---|---|
| Public notices / posters | 5 | office notice boards, health or vaccination posters |
| Forms and pamphlets (blank) | 4 | printed application forms, scheme leaflets |
| Signs | 5 | office, shop, transport, ward or street signs |
| Printed paper text | 3 | bus/rail tickets, receipts with no personal details, newspaper headline (own copy) |
| Screens / mixed script | 3 | printed Bengali + English signs, a phone screenshot of a .gov.in page |

Bengali printed matter can also come from home: food packets, medicine leaflets, calendars, school books. Use public-service text where you can.

**How to shoot** — include deliberate variety and record it in `condition`:
- ~8 `clean` (flat, well lit, straight)
- ~4 `skewed` (photographed at an angle)
- ~3 `low_light`
- ~3 `blurred` or `small_text`
- ~2 `curved` or `busy_background`

**Never include:** faces, names, phone numbers, addresses, ID cards, filled-in forms, vehicle number plates. Crop them out or skip the photo.

**After shooting:**
1. Rename to `bn_rw_001.jpg` … and copy into `data\real_world\bengali\`.
2. One row per image in `ground_truth.csv` (template: `docs/realworld_ground_truth_template.csv`).
3. Run `python check_realworld.py data/real_world/bengali` after every few images.

## Route B — Wikimedia Commons (only if the licence checks out)

These pages came up in a web search on 18 Oct 2026. **Their licences and contents are NOT confirmed** — the audit tool could not open Commons. Open each in your browser; use it only if the file page shows a free licence (CC0, CC BY, CC BY-SA, or public domain) and the photo shows printed Bengali text.

| Proposed filename | Commons page | Status |
|---|---|---|
| bn_rw_0xx.jpg | [Ward 105 (Board written in Bengali language)](https://commons.wikimedia.org/wiki/File:Ward_105_(Board_written_in_Bengali_language).jpg) | unverified |
| bn_rw_0xx.jpg | [No Smoking Notice in Bengali](https://commons.wikimedia.org/wiki/File:No_Smoking_Notice_in_Bengali.jpeg) | unverified |
| bn_rw_0xx.jpg | [A plaque describing history in Bengali](https://commons.wikimedia.org/wiki/File:A_plaque_describing_history_in_Bengali.jpg) | unverified |
| bn_rw_0xx.jpg | [Welcome Board](https://commons.wikimedia.org/wiki/File:Welcome_Board.jpg) | unverified; check it is Bengali |
| bn_rw_0xx.jpg | [KMC Ward Map (Bengali)](https://commons.wikimedia.org/wiki/File:KMC_Ward_Map_(Bengali).jpg) | unverified; a map, use only if text is legible |
| more | [Category: Bengali-language welcome signs](https://commons.wikimedia.org/wiki/Category:Bengali-language_welcome_signs) | browse; check parent "Bengali-language signs" categories |

For each one you keep, copy from the file page: the **page URL** → `source_url`, the **licence exactly as written** → `license`, the **author** → `source` (e.g. `Wikimedia Commons, <author>`), today's date → `retrieved_on`. Download the original file ("Original file" link), rename it, and skip any file that is not clearly free-licensed.

## Manifest entry guide

```
id,filename,text,source,source_url,license,retrieved_on,condition,transcribed_by,transcription_status
bn_rw_001,bn_rw_001.jpg,"<line 1>
<line 2>",own photo,,own photo,2026-10-19,clean,Akansha,needs_review
```

- `text`: type exactly what is printed, including punctuation and Bengali digits (০১২…). Keep line breaks inside the quotes (in Excel: Alt+Enter). If part is unreadable even to you, leave it out and add `partly_illegible` to `condition`.
- Type with a Bengali keyboard (e.g. Google Input Tools / Avro); do not copy text from OCR output — that would bias the evaluation.
- Save as **CSV UTF-8** in Excel, or the Bengali will be corrupted.
- `transcription_status`: `needs_review` when typed; `verified` only after a fluent Bengali reader has compared the text letter-by-letter with the image (that person goes in `transcribed_by`, or note both names, e.g. `Akansha; checked by X`).

## Done when

`python check_realworld.py data/real_world/bengali --leak-check data/bengali` shows `valid: 20`, `transcriptions verified by a fluent reader: 20/20`, and no problems. Then run the evaluation command in `docs/OCR_REALWORLD_BN.md`.
