---
id: 175
slug: pipeline-figures
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 175 — The retrospective reports the pipeline's gates, trains and reviews · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `cmd_gate()` writes `Waited: {waited}` after `Seconds:`;
  `step_text()` writes `DEPTH: <full|light>` from `out["depth"]`; `read_step()` returns `depth`;
  new names `WAITED_RE`, `DEPTH_RE`, `LAND_TRAIN` (moved from `landing.py`), `TRAIN_GATE_RE`,
  `LAND_ACCEPT`; `accept_path()` builds from `LAND_ACCEPT`; docstring names the two lines.
- `plugins/factory/scripts/landing.py`: `LAND_TRAIN` read as `factory.LAND_TRAIN` (its own
  definition removed), as `factory.EJECTIONS` already is.
- `scripts/sdlc.py`: `cmd_gate()` writes `Waited:` from `_hand_slot()`'s `waited`;
  `conflicts_resolved()` keeps its path and reads the text through
  `factory_records.resolved_files()`, so the one rule lives in the module.
- `scripts/factory_records.py`: the five copies above; `read_gate_attempts(text)` (the line
  reading `gate_attempts()` now calls, with `waited`); `read_step()` gains `depth`;
  `CONFLICTS` and `resolved_files(text)`; new pure `pipeline_counts(show, listing)`; the
  `autonomy_counts()` comment (R14).
- `scripts/retro.py`: `_pipeline(home, changes, previous)`; `_p85()` shared with `lead_view()`;
  `retro()` computes `_previous_window()` once for `process_views()` and `_pipeline()`;
  `cmd_retro()` drops `pipeline.changes` without `--metrics`; `_none_reason()`'s regex (R13).
- `tests/test_retro.py`: the pipeline fixtures (R1, R2, R4, R5, R7, R8, R11) and the
  `_none_reason()` tests (R13).
- `tests/test_modules.py`: `RECORD_FILES` gains `land-train.md`, `land-accept.md`;
  `RECORD_NAMES` gains the new copies.
- `tests/test_hand_gate.py`: `_masked()` masks `Waited:` as it masks `Seconds:`.
- `tests/test_factory.py`: a gate attempt carries `Waited:` (R3); `step_text()` writes `DEPTH:`
  (R6).
- `tests/test_board.py`: the `read_step()` pin's cases carry a `depth` (R6).
- `tests/test_train.py`: `factory_records.TRAIN_GATE_RE` reads every `GATE:` line
  `train_record()` writes (R10).
- `docs/REFERENCE.md` (*Retrospectives*), `docs/RETRO-SCORECARD.md`, `plugins/factory/README.md`,
  and `docs/FEATURES.md` / `docs/PROCESS.md` only if `tests/test_feature_map.py` asks (R15).

Reused, not re-derived: `_records_at()`, `_coverage()`, `_share()`, `_previous_window()`,
`gate_kind()`, `read_land_step()`, `read_land_times()`, `_json_rows()`, `opening()`.

Confirmed from history (the spec's open assumption): every factory change closed from 166 to
179 holds `runs/step.md`, `runs/land-step.md`, `runs/land-times.jsonl` and `runs/land-train.md`
at its own commit, and `build/land-*.gate.md` / `build/land-accept.md` where the landing ran
them (173 has both). No figure is missing for every change.

## Work order

1. **The nits** (R13, R14): `_none_reason()`'s regex, with its two tests; the comment.
2. **`Waited:`** (R3): factory test red, then both writers; the hand-gate shape pin masks it.
3. **`DEPTH:`** (R6): `step_text()` writes it, both `read_step()`s read it; pin cases carry it.
4. **The copies** (R9, R10): the five names in `factory.py` and the module; `LAND_TRAIN` moved;
   `accept_path()` from `LAND_ACCEPT`; `read_gate_attempts()`; `resolved_files()`; the
   `TRAIN_GATE_RE` test against `train_record()`; `RECORD_FILES`/`RECORD_NAMES`.
5. **`pipeline_counts()` and `_pipeline()`**, slice by figure, each test first:
   empty window (R1) → gates (R2) → red gate (R4) → landing (R5) → depth (R7) → unreviewed (R8)
   → `--metrics` (R11).
6. **Docs** (R12, R15).

## Tests

- R1: `test_pipeline_is_null_with_no_factory_change`: a window of hand-built changes; every
  rate/share/median/p85 is `null` and every `n` 0.
- R2: `test_pipeline_gates_by_window`: known `Seconds:` → median and p85 per kind; an attempt
  without `Waited:` counts in `seconds.n`, not `wait.n`; the hand gate is in neither.
- R3: `test_a_gate_attempt_records_its_wait` (factory); the hand gate's shape pin, `Waited:`
  masked.
- R4: `test_pipeline_red_gate_rate`: one red-then-green build and one green → `rate: 0.5`.
- R5: `test_pipeline_landing_train_figures`: two trained changes share one red tip at prefix 2 →
  `bisections` 1; one ejection by `gate` → `ejections.gate == 1`; moves, accepts, conflicts.
- R6: `test_the_step_record_names_its_depth` (factory) and the board's `read_step()` pin.
- R7: `test_pipeline_depth_share`: full, light, and an older run → `share: 0.5, n: 2`, older in
  `missing_because` as `depth not recorded`.
- R8: `test_pipeline_unreviewed_landings`: one landing of each kind.
- R9, R10: `tests/test_modules.py`'s scan and shared-name pin; the `TRAIN_GATE_RE` test.
- R11: `cmd_retro()` without `--metrics` has no `pipeline.changes`; with it, it has.
- R12: no `mends` key under `pipeline` (asserted in the R1 test); REFERENCE.md points to
  `autonomy.spurious_stops`.
- R13: two `_none_reason()` tests, the second in a thread joined with a timeout.
- R14: comment only, no test (as the spec says).
- R15: docs; `tests/test_feature_map.py` run by name.

## Rollback

`git revert` undoes everything. What it doesn't: gate records and `runs/step.md` written by runs
built after this lands keep their `Waited:` and `DEPTH:` lines. Every reader matches by line, so
an older script passes over them; nothing needs undoing.

## As built

- R13's timing test runs `_none_reason()` in a child process with a timeout, not a thread: `re`
  holds the GIL while it matches, so a thread's `join(timeout)` never returns on a regression (the
  first red run hung for the full minute). Same guarantee: a regression fails, never hangs.
- `conflicts.md`'s one rule is `factory_records.resolved_files(text)`, which `sdlc.py`'s
  `conflicts_resolved()` now calls; the module's `CONFLICTS` is pinned to `sdlc.CONFLICTS` in the
  R5 test.
- `unreviewed` carries `coverage` and `missing_because` (`unreviewed not recorded`) for a factory
  landing from before the `unreviewed=` field; its `n` is the landings with a value.
- `bisections` is `{"total": n}`, so each landing figure is a dict beside `landing.n`.
- The existing `test_retro_prints_each_change_s_numbers_only_when_asked` pops
  `pipeline.changes` as it pops `cost.changes`.
- `docs/RETRO-SCORECARD.md`'s wave 3 marks S10 done: 175, as S4 was marked for 174.
