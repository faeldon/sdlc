---
id: 002
slug: rename-drafts
kind: spec
created: 2026-11-01
updated: 2026-11-01
---

# 002 — Rename a saved draft · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

R1. `drafts.rename(old, new)` moves the text saved under `old` to `new`, and `titles()` lists `new`
and not `old`. `test_a_renamed_draft_keeps_its_text_under_the_new_title` fails if it doesn't.

R2. Renaming onto a title already saved, or from one never saved, changes nothing and returns
`False`. `test_a_rename_onto_a_taken_title_changes_nothing` fails if a draft is lost.

## Design

`rename()` sits beside `save()` in `drafts.py` and moves the entry in `DRAFTS` with `pop`, after
checking both titles.

## Contracts touched

None: `save()` and `titles()` are unchanged.

## Alternatives rejected

- Overwriting a taken title: it loses the draft saved there.

## Verification

```bash
python -c "import drafts; drafts.save('a', 'x'); print(drafts.rename('a', 'b'), drafts.titles())"
```

Healthy output: `True ['b']`.
