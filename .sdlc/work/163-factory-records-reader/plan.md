---
id: 163
slug: factory-records-reader
kind: plan
created: 2026-11-18
updated: 2026-11-19
---

# 163 — One reader in core for the factory's records · plan

> Written by the builder after reading `scripts/sdlc.py` (the hand gate's copies at ~3000–3125,
> the run's records at ~5050–5462, the callers in `check`, `_passes_report`, `SHIP_BRANCHES` and
> `cmd_status`), `scripts/board.py`, `scripts/closing.py` and the pin tests named in the spec.

## Files to change

- `scripts/factory_records.py` (new): every copy of `factory.py`'s record parsing that core
  holds, pure (no `subprocess`, no `sdlc`), named as `factory.py` names them; plus the names R5
  needs so no other file spells a record's name: `DECISION_FILE`, `LEDGER_FILE`,
  `BUILDER_SESSIONS`, `SESSIONS`, `gate_kind()` (`round-`/`land-` `*.gate.md`), `gate_seconds()`.
- `scripts/sdlc.py`: `_load_factory_records()` beside `_load_metrics()`, `factory_records = …`;
  the hand gate's copies (`CLONE_MARK` … `TERM_MARK`, `HAND_DEFUSE`, `HAND_TERMS_FILE`,
  `_hand_login`, `_hand_terms`, `_hand_placeholders`, `HAND_GATE`, `ATTEMPT_VERDICT_RE`,
  `BUILD_RE`, `SECONDS_RE`, `_gate_attempts`) and the run's (`FACTORY_*`, `GARBLED_LEDGER`,
  `_factory_opening`, `factory_*` readers) removed; `_hand_main(root)` keeps the one
  `git worktree list` call `_hand_placeholders` made; every caller reads
  `factory_records.<name>`. `needs_of`, `column`, `seen_stage`, `answered`, `decide_step`,
  `FACTORY_STOP_NEEDS`, `hand_gate`, `hand_build`, `cmd_gate` stay (R4).
- `scripts/board.py`: its copies (lines 52–106, `PAUSES`, `LAND_STOPS`, `read_step`,
  `read_land_step`, `read_land_times`, `cost`, `_factory`, `_reviewed`) removed; reads
  `sdlc.factory_records.<name>`; `history_samples` keeps its git walk and classifies gate files
  with `gate_kind()`, reading seconds with `gate_seconds()`; `_progress` reads the builder's
  session time through `builder_started()`; `_entry`'s `read()` labels from the path constants.
- `scripts/closing.py`: `_factory_files`, `_agent_sessions`, `_agent_models` keep their
  signatures (R9) and hand the module `show`/`listing` callables over the branch
  (`_branch_files()`, closing's own); `measure_change`'s `decision.md` from `DECISION_FILE`.
- `tests/test_modules.py`: the new tests (R1–R6).
- `tests/test_board.py`, `tests/test_metrics.py`, `tests/test_hand_gate.py`, `tests/test_sdlc.py`,
  `tests/test_factory.py`: reads of a moved name repointed only (R7, R8); the two `opening` pins
  merged into `test_board.py`'s, `test_metrics.py`'s dropped.
- `AGENTS.md`: *Modules loaded by path*, *The board*, *The factory* (R11).
- Docstrings of `board.py`, `closing.py` pointing to the module (R11).

## Work order

1. **The module and its load, with the boundary tests.** Write `tests/test_modules.py`'s R1–R6
   tests; see them fail (no module). Create `factory_records.py` by moving every copy verbatim
   (renamed per the spec's table), load it in `sdlc.py`, repoint `sdlc.py`'s callers, delete the
   old copies. Run the moved names' tests in `test_sdlc.py`, `test_metrics.py`,
   `test_hand_gate.py`, `test_factory.py` after repointing their reads.
2. **The board.** Delete its copies, repoint to `sdlc.factory_records`, `history_samples` via
   `gate_kind`/`gate_seconds`. Repoint `test_board.py`; run it whole.
3. **Close.** Replace the parsing in the three adapters with the module's `run_counts`,
   `session_roles`, `session_models` over closing's `show`/`listing`. Run the `_factory_files`
   tests in `test_metrics.py`, `test_archive.py`, `test_factory.py`, `test_hand_gate.py`.
4. **Docs.** AGENTS.md and the docstrings; then the full gate through `factory.py check`.

Departure from the spec's signatures: the module's callables are folder-relative (`show(rel)`
reads `<folder>/<rel>`, `listing(rel)` lists every path under `<folder>/<rel>` relative to the
folder), so `run_counts(show, listing)`, `session_roles(show, listing)`, `session_models(show)`
take no `folder`: the module never builds a repo path.

As built, three more departures:
- R3's test allows one name by hand (`UNRELATED`): `sdlc.py`'s `MOVES_RE` reads the direction
  doc's `**Moves O<n>:**`, not a landing's `MOVES:` line, and keeps its name.
- `test_board.py::test_the_landing_stop_is_read_as_status_reads_it` lost its line pinning
  `sdlc.FACTORY_LAND_STOPS == board.LAND_STOPS`: with one copy it would compare the module with
  itself. R6's test pins `LAND_STOPS`' neighbours against `factory.py`; `LAND_STOPS` has no
  factory twin, and the board's `LAND_AT` test still holds it against `LAND_STEPS`.
- `history_samples` keys its gate lists `round`/`land` (from `gate_kind()`), not `round-`/`land-`.

## Tests

- R1: `test_modules.py::test_factory_records_is_pure_and_loaded_once`.
- R2: `test_modules.py::test_the_board_and_close_read_records_through_sdlc`.
- R3, R4: `test_modules.py::test_the_record_readers_live_in_factory_records`.
- R5: `test_modules.py::test_no_factory_record_is_named_outside_its_reader` (its checker shown to
  report a snippet).
- R6: `test_modules.py::test_every_shared_name_is_the_factorys`.
- R7: the existing behavioural pins, repointed: `test_board.py`'s opening, `read_step`,
  `read_land_step`, `read_land_times`, `cost`; `test_metrics.py`'s reasons/newest_round;
  `test_hand_gate.py::test_the_placeholders_are_the_factorys`.
- R8, R9, R10: every existing test in `test_board.py`, `test_sdlc.py`, `test_hand_gate.py`,
  `test_metrics.py`, `test_archive.py`, `test_factory.py` passing with no expected value changed.
- R11: review; `factory.py check` (the full gate).

## Rollback

`git revert` of the change's commit undoes all of it: the change writes no data, publishes
nothing, and changes no record's format or any trailer. Nothing outside the repo to undo.
