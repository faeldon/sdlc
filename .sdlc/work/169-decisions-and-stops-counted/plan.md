---
id: 169
slug: decisions-and-stops-counted
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 169 — The retrospective counts decisions and stops · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/factory_records.py`: new copies under `factory.py`'s names (`MENDED`, `ARCHIVE_RE`,
  `KEPT_ANSWER`, `CONFIRMED`, `SUPERSEDED`), core's own `LOOK_SEEN = "seen"`, and
  `autonomy_counts(show, listing)` beside `run_counts()`, reusing `opening()`, `DECISION_RE`,
  `LEDGER_RE`, `DECIDED`, `SETTLED`, `DECISION_FILE`, `LEDGER_FILE`. Docstring names retro as a
  reader.
- `scripts/retro.py`: `_records_at(home, rec)` (show/listing at the change's own commit, through
  `sdlc._git`, shaped as `closing._branch_files()`), `_autonomy(home, changes)` summing
  `sdlc.factory_records.autonomy_counts()`, `"autonomy"` in `retro()`'s JSON, two `UNMEASURED`
  entries, and `after_gate_by` / `after_gate_unnamed` in `_extra_report()`.
- `scripts/sdlc.py`: `closed_changes()` keeps `rec["landed"]` from the change commit's trailers it
  already parses (`own`); `rebasing_branches(root, trees=None)`; `held_by_rebase()` walks
  `_change_trees()` once; `_by_state()`'s fallback calls `column()`.
- `scripts/metrics.py`: `close_span()` keeps the span's skill on an `after_gate` stop;
  `summarize()` adds `after_gate: {skill: n}`; `trailers()` writes `Sdlc-AfterGate: <skill>
  stops=<n>`; `parse_trailers()` reads them into `after_gate`; docstring contract line.
- `tests/test_retro.py`: R1–R9, R12, R16 tests (fixture factory changes via `_close(texts=…)`,
  plus a trailer on the change's own commit).
- `tests/test_metrics.py`: R11.
- `tests/test_modules.py`: `RECORD_NAMES` gains the new names; the board-and-close test covers
  `retro.py`; `test_look_seen_is_the_decide_skills_answer` (R10).
- `tests/test_sdlc.py`: R13, R14.
- `docs/REFERENCE.md` (*Retrospectives*, *Metrics*), `AGENTS.md` (map sentence): R15.

## Work order

1. **The reader.** `autonomy_counts()` and its constants, with R1–R4 tests calling it on dict-backed
   `show`/`listing`, and the `RECORD_NAMES`/`LOOK_SEEN` pins (R10). Stops with a pure function
   tested alone.
2. **Retro's autonomy.** `_records_at`, `_autonomy`, `landed` in `closed_changes()`, the JSON and
   `UNMEASURED` (R5–R9, R16), tested through `retro()` on fixture repos; retro covered by the
   through-`sdlc` test.
3. **After-gate by skill.** `metrics` summarize/trailers/parse (R11), then `_extra_report()`
   (R12).
4. **Status nits.** R13, R14.
5. **Docs.** R15.

## Tests

- R1 `test_autonomy_counts_are_none_for_a_change_built_by_hand`
- R2 `test_autonomy_counts_every_escalation_current_and_archived`
- R3, R8 `test_autonomy_counts_read_each_ledger_answer_by_its_mark` (the reader, then through
  `retro()` for the rate)
- R4 `test_autonomy_counts_tell_a_landing_mend_from_a_build_mend`
- R5 `test_retro_autonomy_says_a_decision_it_cannot_read`
- R6 `test_retro_autonomy_leaves_hand_built_changes_out`
- R7 `test_retro_autonomy_counts_auto_landed_from_the_change_commit`
- R9 `test_retro_says_what_autonomy_cannot_count`
- R10 `test_the_board_and_close_read_records_through_sdlc` (extended),
  `test_every_shared_name_is_the_factorys`, `test_no_factory_record_is_named_outside_its_reader`,
  `test_the_record_readers_live_in_factory_records` (new names), `test_look_seen_is_the_decide_skills_answer`
- R11 `test_an_after_gate_stop_names_the_skill_whose_gate_it_followed` (`tests/test_metrics.py`)
- R12 `test_retro_names_the_skill_an_after_gate_stop_followed`
- R13 `test_held_by_rebase_walks_the_change_trees_once` (`tests/test_sdlc.py`), with
  `tests/test_board.py`'s rebase tests
- R14 `test_by_state_places_a_record_without_a_column_as_column_does` (`tests/test_sdlc.py`)
- R15 docs, checked at review.
- R16 the R5–R7 retro tests assert `_state()` is unchanged with factory fixtures in the window.

## As built

- `asked.blocking` counts the blocking lines the person answered, as `default` counts kept and
  changed and `look` seen and checked: what they were asked and answered. Open lines are in
  `looks.open` and the reader's `blocking.open`, not in `asked`.
- `test_the_record_readers_live_in_factory_records` also checks `retro.py` defines none of the
  copies, beside the board-and-close test R10 names.
- An extra R8 test, `test_retro_autonomy_rates_kept_defaults_without_the_landings_yes`, runs R3's
  ledger through `retro()`.

## Rollback

`git revert` covers it all: no data is written (retro stays read-only), nothing is published.
`Sdlc-AfterGate` lines already written on `Close` commits stay in history after a revert; the old
`parse_trailers()` reads them as an unknown key (`out["aftergate"]`, last line wins) and nothing
reads that, so they are harmless.
