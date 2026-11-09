# English–Bengali translation evaluation set

`en_bn_public_service.json` holds 25 English public-service sentences, each paired with a Bengali reference translation. It is test data for the future `POST /api/translate/translate` endpoint (see `docs/API_CONTRACT.md`). It is not training data, and the FAQ answers in `backend/data/faqs/` are kept separate from it.

## Record format

| Field | Meaning |
|---|---|
| `id` | Stable ID, `tr_bn_001` … `tr_bn_025`. Never renumber; add new items at the end |
| `category` | `government_services`, `documents`, `public_health`, `education`, `transportation`, `digital_services` |
| `length` | `short`, `medium` or `complex` (multi-clause), for reporting scores by difficulty |
| `en` | English source sentence |
| `bn_reference` | Bengali reference translation (meaning-based, not word-for-word) |
| `reference_origin` | Who wrote the reference and how |
| `notes` | Rationale, terms being tested, or where a fact in the sentence comes from |
| `review_status` | `needs_review` → `approved` (accepted as is) or `revised` (corrected by reviewer) |
| `reviewed_by`, `reviewed_on` | Reviewer name and date (YYYY-MM-DD); `null` until reviewed |

The sentences are illustrative. Most are not official notices, and none should be read as a statement of current policy. The one factual claim with a source (the 21-day birth registration period, `tr_bn_006`) is cited in `notes`.

## How it will be used

1. Send each `en` sentence to the API as `{ "text": en, "src_lang": "en", "tgt_lang": "bn" }`.
2. Score the returned `translated_text` against `bn_reference` with chrF. For example, using `sacrebleu`:
   ```python
   from sacrebleu.metrics import CHRF
   score = CHRF().corpus_score(hypotheses, [references])
   ```
   chrF compares character n-grams, which suits Bengali's rich word endings better than BLEU.
3. Report the score overall, by `category` and by `length`. Also have a person read 10–20 outputs, as the project plan requires.
4. Optionally, run the reverse direction (`bn` → `en`) with `en` as the reference.

## Why human review comes first

The references were drafted by an AI assistant and have not been checked by a fluent Bengali reader. chrF only measures closeness to the reference. If a reference is unnatural or wrong, the scores mislead: a good system output can be marked down, or a bad one rewarded.

Before reporting any scores:
- A fluent reader checks every reference, fixes it if needed, and sets `review_status`, `reviewed_by` and `reviewed_on`.
- Scores computed while any item is `needs_review` are provisional only.

## Validate

```
python eval/translation/validate_translation_set.py
```
The script checks fields, IDs, categories, scripts, duplicates and review metadata. It does not judge translation quality.
