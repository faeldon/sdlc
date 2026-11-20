# Notes

## The files idea 2026-11-18-90 named

Retro, rerun from this worktree on 2026-11-20 (lookback `162-lead-time` to
`195-designing-while-specified`), no longer names any of them:

- **`tests/fixtures/board/changes/012-draft-publish/` (seven files): kept.** It dropped out of the
  lookback (last touched by 2e47d27), but it can't drift silently either way:
  `test_the_board_fixture_stops_as_the_factory_writes` and
  `test_the_board_fixture_lands_as_the_factory_writes` (`tests/test_board.py`) compare its
  records byte for byte with what `factory.py` writes now, and
  `test_the_board_fixture_shows_every_card_state` builds the board from it. The UI reviewers'
  screenshots read it, so it stays.
- **`tests/test_config_resolution.py`: kept.** Touched since, by d61f024 (more than 50 files, so
  retro's drift ignores it). It runs `config` itself; nothing in it pins an older shape.
- **`tests/test_indicators.py`: kept.** Touched since (b2bf06f), and every function in
  `indicators.py`'s docstring list has a test there.
- **`tests/test_adoption.py`: kept.** 191 (6655e20) reworked it.

## The current list, taken in turn

- **`skills/spec/SKILL.md`: misread, fixed.** The conventions count any `spec` directory as tests;
  here `skills/spec/` (and `evals/spec/`) is the spec skill. `.sdlc/config.toml` now sets
  `retro.test_paths = ["tests/"]`; with it the drift list no longer names the file (shown in the
  build report's evidence). Retro reads the main checkout's config, so its own run shows this
  only once the change lands.
- **`tests/test_hand_gate.py`: rewritten in one place.** 187 added `command` and `summary` to
  `hand_gate()`, tested only through the board's card (`test_board.py`, 187 R19). The reader's
  own test, `test_hand_gate_reads_none_current_and_stale`, now asserts both, so the record's
  reader names every field its docstring lists. Once this lands the file is fresh.
- **`tests/fixtures/land-record-cases.json`: kept on purpose.** It is the shared case table
  `test_the_land_record_readers_are_pinned_copies` runs both readers over; it changes only when
  the record's shape does, and the test fails the moment the two readers disagree.
- **`tests/fixtures/close-output.json`: kept on purpose.** A golden of close's output, compared
  exactly (`tests/test_archive.py`, 172); a change that moves close's output fails it.
- **`tests/prompts/land-fix.txt`: kept on purpose.** A golden of the land-fix prompt, compared
  exactly by `tests/test_prompts.py` (164), whose own test refuses a recorded copy no case renders.
- **`tests/test_function_heat.py`: kept.** Its subject, `.sdlc/function-heat.py`, hasn't changed
  since 177 (304dcd8). It drifts only because 177 also touched `retro.py` and `sdlc.py`, which
  most changes touch.
- **`tests/test_metrics.py`: kept.** Its subject is `metrics.py`; it names `retro.py` nowhere. It
  drifts because 179 touched it beside `retro.py`, and its later edit, d61f024, is over 50 files.

No test was deleted, so no assertion had to move.

## Follow-ups

- [x] Retro's `tests.drifted` takes a test's code to be every code file its last change touched, → seed: 2026-11-20-18
  so a test edited beside `sdlc.py` or `retro.py` drifts for good (`test_metrics.py`,
  `test_function_heat.py`), and an exact golden (`close-output.json`, `land-fix.txt`,
  `land-record-cases.json`) is named though it can't drift silently. A narrower notion of a
  test's code (the files it loads, or a host's list of goldens) would make the list worth acting on.
