---
id: 207
slug: change-origin
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 207 — A change records where its finding came from · plan

> Written by the builder after reading the code the spec names, against spec R1–R12.

## Files to change

- `scripts/sdlc.py`: `ORIGINS = ("host", "self")` beside `IMPACTS` (R1); `load_change()` reads
  `origin:` with `frontmatter_list()` into `rec["origin"]`, an error for a bad value or several
  (R2); `_change_record()` gains `origin=None`, set only to a value in `ORIGINS` (R3);
  `BODY_KEYS` gains `"Origin"` (R11).
- `scripts/closing.py`: `origin_trailer(main, branch)` beside `fix_trailers()`, reusing its
  `sdlc._git(... show {branch}:{rel}/{branch}/intent.md)` read and `sdlc.frontmatter_list()`;
  `_step_remove_folder()` appends its lines after the `Sdlc-Fixes` ones (R4, R5).
- `scripts/metrics.py`: `"origin"` joins the text-valued keys in `parse_trailers()` (R6); a
  docstring paragraph for `Sdlc-Origin` (R7).
- `scripts/retro.py`: `_origins(changes)`, pure, and `"origins"` in `retro()`'s dict (R8).
- `skills/retro/SKILL.md`: `origins` in its figures, read against the host's own docs (R9).
- `skills/intent/SKILL.md`: Step 1 proposes `origin:`, Step 3 shows it, Step 4's question gains
  `, found in a host` / `, found here`, Step 5 writes it (R10).
- `skills/intent/batch.md`: a batch proposes and shows `origin:` as a single run does (R10).
- `skills/idea/SKILL.md`, `skills/bug/SKILL.md`: `Origin: host` in Step 3's entry shape, only when
  the account says so (R11).
- `docs/REFERENCE.md`: *Metrics* (`Sdlc-Origin`), *Retrospectives* (`origins`), the intent's
  `origin:` line and the register's `Origin:` body line (R12).
- `docs/FEATURES.md`: an `Sdlc-Origin` bullet and an `origin:` bullet (R12).
- Tests: `tests/test_sdlc.py`, `tests/test_archive.py`, `tests/test_metrics.py`,
  `tests/test_retro.py`, `tests/test_skills.py`.
- `tests/test_archive.py`'s `_normal()` and `tests/fixtures/close-output.json` (found while
  building, not in the spec): the golden close output pinned `plugin=1.10.0`, which Release 1.11.0
  made stale, so `test_close_output_is_unchanged` failed on the base branch itself. `_normal()`
  now masks the version as it masks shas; raised as a default decision.

Not touched: `templates/intent.md` (the skill adds the line, as it does `serves:`), so no
`drift`/`record` cycle.

## Work order

1. **Values and an open change** (R1, R2): `ORIGINS`, `load_change()`; tests in `test_sdlc.py`.
2. **A closed change's record** (R3): `_change_record()`; test calls `_change_record()`, the
   function `closed_changes()` builds every record with, on three intents.
3. **Reading the trailer back** (R6, R7): `parse_trailers()` and the docstring.
4. **Close writes it** (R4, R5): `origin_trailer()` and `_step_remove_folder()`; tests in
   `test_archive.py` closing a real change, one with no line, one dropped.
5. **The retrospective** (R8, R9): `_origins()`, `retro()`, the retro skill.
6. **The register's line** (R11): `BODY_KEYS`, idea and bug skills.
7. **Intent skill** (R10).
8. **Docs** (R12), `tests/test_feature_map.py` green.

## Tests

- R1: `test_origin_values_are_host_and_self` (test_sdlc).
- R2: `test_vet_strict_passes_a_change_with_no_origin`,
  `test_an_origin_outside_host_and_self_is_an_error` (test_sdlc).
- R3: `test_a_closed_change_without_origin_reads_none` (test_sdlc).
- R4: `test_close_writes_an_origin_trailer` (test_archive).
  Also `test_an_invalid_origin_closes_without_the_trailer`: `origin_trailer()` gives `[]` for a
  word outside the two and for a branch that doesn't exist.
- R5: `test_a_change_without_origin_closes_without_the_trailer`,
  `test_a_dropped_change_carries_no_origin_trailer` (test_archive). The rerun case rests on
  `_close_commit()`'s existing early return, covered by the existing rerun tests.
- R6: `test_parse_trailers_reads_origin_as_text` (test_metrics).
- R7, R12: `tests/test_feature_map.py` (existing) fails until FEATURES.md names `Sdlc-Origin`.
- R8: `test_retro_counts_changes_by_origin` (test_retro).
  Also `test_a_window_before_origins_reads_as_all_unknown`, and `origins` joins
  `test_it_reports_every_key_and_writes_nothing`'s keys.
- R9: `test_retro_skill_reads_origins` (test_skills).
- R10: `test_intent_proposes_an_origin` (test_skills).
- R11: `test_an_entry_reads_its_origin_line` (test_sdlc), `test_idea_and_bug_offer_an_origin_line`
  (test_skills).

## Rollback

`git revert` undoes all of it. Not undone: `Sdlc-Origin` trailers already on `Close` commits and
`origin:` lines in intents in history; both are harmless once reverted, since `parse_trailers()`
then reads the trailer as an unused name, and nothing reads the line. Nothing is published.
