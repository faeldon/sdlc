VERDICT: CHANGES

- CHANGE: [context] AGENTS.md:138: The *Retrospectives* paragraph says retro "runs the host's `retro.evidence` and `retro.indicators` (`_evidence()`, the only place they run)". `retro.test_times` now runs through `_evidence()` too, so the sentence is false. The spec says to fix it at ship, but the diff leaves it stale. Edit it to "runs the host's `retro.evidence`, `retro.indicators` and `retro.test_times` (`_evidence()`, the only place they run)".

## Notes
- I walked R1–R12 against the diff and each has code and a named test. These pass: 929 tests across the indicators, retro, skills, sdlc, config-resolution and defaults files, plus `ruff check` and `ruff format --check`.
- `retro_report()` never calls `retro()`, `_tests()` or `_times()`. Only `retro()` reaches them, so R2's "history only" report holds.
- Not run: `claude plugin validate --strict`, and the manual real-fixture check from the spec's *Verification*. My `./check.sh` call was moved to the background, and its output file only held the earlier grep results.
- NIT: scripts/retro.py:182: `_times()` returns an `ok` state with `median: None` when every case is skipped or untimed. The skill's prose doesn't say what `slow` does then. It is harmless, since `slow` is empty.
- NIT: scripts/indicators.py:441: `drifted_tests` writes its `last` key as `kind(path) == "tests"`. A path that is both under `skip` and a test is already dropped by `_files`, so this is fine. A comment saying so would help.
- Done well: `_lookback()` is read once and shared by the architecture and pruning passes, so there is no second 30-change walk. A truncated report is a failure, never a partial read. The deviations from the spec (zero `time` reads as untimed, `present` None counts every file as present) are recorded in the plan.
