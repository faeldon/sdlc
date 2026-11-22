---
id: 222
slug: parked-changes
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 222 — A change can be parked on a host resource, with a deadline, instead of stopping or asking · plan

> Written by the builder after reading the code, against the approved spec. Read by the reviewers
> and the approver beside the spec; updated where the build departs from it.

## Files to change

- `plugins/factory/scripts/factory.py`: `DEFAULTS["park"]` and `_park()` (the base branch's
  `[park]`, read in `load_config()` as `gate_jobs` is, with the checkout-differs warning); the
  record's names (`PARKED`, `PARKED_RE`, `RESOURCE_RE`, `HOLDER_RE`, `RETRY_RE`, `DEADLINE_RE`,
  `ATTEMPTS_RE`, `NOTE_RE`, `BUSY_RE`), `read_park()`, `park_text()`, `busy_of()`,
  `park_fields()` (R4's arithmetic, a pure function of the old record, the busy answer, the config
  and `now`), `_clock()` and `_pause()` (the stand-ins' seams); `SLOT_WAIT` and `SlotWaitExpired`
  raised by `gate_slot()`; `cmd_gate` (busy and slot-wait paths, build and landing),
  `cmd_check` (busy passed through, slot wait bounded); `cmd_verdicts(..., now=None)` and its
  `--record` (stale park removed, `STOPPED: parked`); `stop_text()` given the park; `STOPPED_RE`,
  `WAYS`, `WAYS_WHY` gain `parked`; `STEPS`; `cmd_park` (`--wait`, `--clear`) and its `@command`,
  in `HELP_ORDER`; `cmd_start` reports `parked`; `"parked.md"`-shaped path in `RECORD_GLOBS`.
- `plugins/factory/scripts/run_state.py`: `loop_state(root, ident, head, now=None)` reads the
  park through a new `_park_state()`; the docstring's "reads no state file but `runs/mended`"
  sentence changed as the spec's *Contracts touched* says.
- `plugins/factory/scripts/autopilot.py`: `build_step()` returns `parked` without a command;
  `apply_change()` keeps `retry`/`deadline` on the change; `starts()` passes over it before
  `retry`; `run_loop()` waits in slices (`PARK_SLICE = 30`) through `_pause()` while only parked
  changes remain; the `AUTOPILOT_STEPS` comment names `parked`.
- `scripts/factory_records.py`: copies of the park names and `read_park()` under `factory.py`'s
  names, `park(folder)` (the record from disk, for status and the board), `STOPPED_RE` with
  `parked`.
- `scripts/sdlc.py`: `FACTORY_STOP_NEEDS["parked"]`; `needs_of()`'s past-deadline rule from
  `rec["parked"]` and `rec["now"]` (a stamp; ISO `Z` stamps compare as text); status reads the park
  at `stage: build` and `_change_lines()` prints the `⏸` line.
- `scripts/board.py`: `AT["parked"] = 1`; `_progress()` labels the gate position with the park's
  text, state `parked`; the entry carries `parked` and `now` for `needs_of()`.
- `scripts/board.html`: `STEP_WORDS` gains `parked`.
- `plugins/factory/skills/build/SKILL.md`: `parked` (run `park --wait` in the background, back to
  Step 2), a `parked` stop reported and left, `start`'s `parked`, `park --clear` on a rerun's yes
  with an expired park; two `Bash(...)` rules.
- Docs: `plugins/factory/README.md` (*Configuration* `[park]`; *The loop's states* table),
  `docs/REFERENCE.md` (the host's side), `docs/FEATURES.md` (`parked` entry), `AGENTS.md` (the
  `verdicts` sentence).
- Tests: `tests/test_factory_park.py` (new: R1–R8, R10, R12–R14, R17), `tests/test_autopilot.py`
  (R15), `tests/test_board.py` and `tests/test_sdlc.py` (R16), `tests/test_modules.py`
  (`RECORD_NAMES`, `RECORD_FILES`, the `read_park` pin), `tests/test_factory_loop.py` (R9).

Reused, not re-derived: `_placeholders()` (which already ends in `_defused()`), `_vouch()` and
`vouched()`, `_base_factory()`, `_record_step()`, `stop_text()`, `_utc_now()`'s format,
`gate_slot()`'s lock loop, `find_change()`, `build_round()`, the autopilot test's `Steps`.

## Work order

1. **Config and the payload** (R1, R3): `[park]` read from the base branch; `busy_of()`;
   `park_fields()` and `park_text()`/`read_park()`. Unit tests on the pure functions.
2. **The gate parks** (R2, R4, R5, R12's gate side): `cmd_gate` on a busy exit or a slot wait
   past `SLOT_WAIT` writes the vouched park and no attempt; a non-busy attempt removes it. The
   tree is compared before the busy branch (round 2): a busy exit that changed the tree is a
   `FAIL` attempt, and a slot wait, where the check never ran, compares nothing.
3. **`verdicts` reads it** (R6, R7, R8, R9): `_park_state()` in `run_state.py`, `now` injected,
   the `parked` way, `--record`'s writes, `STOPPED_RE` in both copies.
4. **Landing and check** (R13, R14, R12's check side): a `problem`, never an attempt; `check`
   passes the code through, with the payload when `[park] exit` is set (see below).
5. **`park --wait` / `--clear` and `start`** (R10, R11's script side), then the build skill.
6. **Autopilot** (R15).
7. **Status and the board** (R16).
8. **The table and the docs** (R17, R18).

**`check`'s payload (the spec left it to the plan).** With `[park] exit` unset, `check` runs as
now, its output straight through. With it set, `check` captures the output and prints it once the
command ends (stdout to stdout, stderr to stderr), so the payload can be read wherever the host
printed it. The builder's Bash call shows output at the end anyway; a host without the key sees no
change (R1).

**Cut, then mark, or mark, then cut.** R3 lists "one line, cut to 200, then `_placeholders()`".
Cutting first can leave half a home path that no longer matches `DEFUSE`'s shape, so the build
marks first and cuts after; the record still never holds more than 200 characters a value.

**Status's `⏸` line, in two.** R16 words the park as one line; with two full UTC stamps it runs
past `status`'s width, where `_cut()` would drop the deadline. `status` prints `⏸ parked on
<resource>, held by <holder>;` and, under it, `retry <time>, deadline <time>`: the same words,
split at the `; `. The board's card, which wraps, keeps the one line (`sdlc.park_line()`, which
both read).

**A `parked` stop's way on names no `/sdlc:ship`.** R9 fixes its `NEXT:` as `free <resource>
(held by <holder>), then /sdlc-factory:build {id}`, so the pinned test that every way names
`/sdlc:ship` (`test_each_way_on_fits_two_lines_at_phone_width`) now exempts it: shipping a parked
change by hand would only meet the busy check again.

**Where the code landed.** `park_problem()` lives in `run_state.py`, its one caller, as
`tests/test_modules.py` requires; `busy_line()` and `_gate_busy()` sit above `cmd_gate`, so its
adapter stays beside it (`tests/test_registry.py`); `sdlc.park_line()` is the one wording of the
park for status and the board.

## Tests

- R1 `test_a_busy_code_without_park_exit_is_a_red_gate`
- R2 `test_a_busy_gate_parks_and_records_no_attempt`,
  `test_a_busy_answer_that_changed_the_tree_is_a_failed_attempt`
- R3 `test_busy_payload_is_read_defused_and_cut`, `test_an_until_that_wont_parse_is_noted`
- R1 also `test_a_busy_code_in_the_checkouts_own_factory_toml_is_not_read`,
  `test_busy_of_is_none_unless_the_exit_is_the_configured_one`
- R4 `test_a_repark_keeps_its_deadline`, `test_park_config_out_of_range_warns`
- R5 `test_a_run_that_isnt_busy_ends_the_park`
- R6 `test_verdicts_parks_then_retries_then_stops`
- R7 `test_verdicts_reads_only_files_and_its_clock`
- R8 `test_a_forged_park_never_waits`, `test_a_stale_park_is_passed_over_and_removed`
- R9 `test_a_stop_at_the_deadline_reads_back_as_parked`; `WAYS` and the defaults' pins
  (`test_each_way_on_fits_two_lines_at_phone_width`, `test_config_defaults_and_its_warnings`,
  `test_the_stop_record_says_why_and_reads_as_before`) extended to `parked`
- R10 `test_park_wait_returns_by_its_bound`, `test_park_clear_refuses_a_live_park`
- R11 `tests/test_skills.py` (rules used and present), `test_start_reports_the_park`
- R12 `test_a_gate_slot_wait_ends`, `test_a_gate_past_the_slot_wait_parks_and_a_check_exits_1`
- R13 `test_a_busy_landing_gate_is_a_problem_never_an_eject` (test_land.py)
- R14 `test_check_passes_busy_through_and_writes_nothing`
- R15 `test_autopilot_waits_out_a_park_and_holds_past_its_deadline` (test_autopilot.py)
- R16 `test_a_park_past_its_deadline_needs_the_person` (test_sdlc.py),
  `test_status_shows_a_parked_change_under_building` and
  `test_a_parked_card_sits_at_the_gate_and_moves_to_needs_you_past_its_deadline` (test_board.py),
  `test_both_park_readers_read_a_record_alike` and
  `test_park_records_read_back_what_the_factory_writes` (test_modules.py)
- R17 `test_every_step_has_a_row_and_a_bound`
- R18 `tests/test_feature_map.py` (FEATURES.md), `test_every_step_has_a_row_and_a_bound` (the
  states table), and `checks.md`'s three checks (README `[park]`, REFERENCE's section, AGENTS.md's
  sentence). The prose's wording is the ship review's, not a requirement (round 2's split).

## Rollback

`git revert` undoes all of it. It doesn't undo what lives outside the tree: lines a park appended
to the records ledger (`sdlc-factory-records.jsonl` in the git common dir), which vouch for files
that no longer exist and are harmless; and a `runs/parked.md` left in another change's folder,
which the reverted code never reads (remove it by hand with `rm`). No data is published.
