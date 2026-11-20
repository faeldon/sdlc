# Plan

> Tier 1: the intent's Approach is the spec. This plan records what the rerun found and what was
> built from it; `notes.md` has each file's reason.

## Files to change

- `.sdlc/config.toml`: `retro.test_paths = ["tests/"]`, so `skills/spec/` stops counting as tests
  (`retro._kind()` reads it through `sdlc.risk_paths()`, nothing new).
- `tests/test_hand_gate.py`: `test_hand_gate_reads_none_current_and_stale` asserts `hand_gate()`'s
  `command` and `summary`.
- `notes.md`: the reason for every file, named or current.

## Work order

1. Rerun retro's drift list (`retro._lookback()`, `indicators.drifted_tests()`) and read each file
   against its code.
2. The hand gate reader's test: seen failing with `command` removed from `hand_gate()`, then green.
3. The config setting, with its acceptance check in `checks.md`; the drift list rerun with it.

## Tests

- `tests/test_hand_gate.py::test_hand_gate_reads_none_current_and_stale`: the reader returns the
  last attempt's command and summary.
- `checks.md`: the config holds `test_paths = ["tests/"]`.

## Rollback

`git revert` undoes all of it; nothing is written outside the repo.
