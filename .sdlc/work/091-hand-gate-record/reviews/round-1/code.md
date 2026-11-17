VERDICT: PASS

## Notes

- **Requirements:** I found code for R1 to R15 and a matching test for each. The spec's tests for them are in `tests/test_hand_gate.py` (405 lines) and `test_board.py` / `test_metrics.py`. I read the diff closely but did not go through every test body. One spot check I made: `cmd_gate` reads the check from `_config_at(home, refs/heads/<trunk>)`, as R1 requires, and the base branch name always arrives through `trunk`.
- **Optional:** `HAND_GATE_RE` in `scripts/metrics.py` matches `scripts/sdlc.py gate` anywhere in a Bash command. That includes a `grep` or `echo` that merely mentions it, and it would then count as a `check` event. The practical risk is low. You could anchor the pattern to the command's start, or after `uv run … --script`.
- **Optional:** `_hand_hash` hashes the fork, so a rebase makes the record stale, as the spec intends. `hand_build` returns a hash even when `merge-base` fails (`fork` is None and the path list is empty). In that case every unreadable state hashes the same. `cmd_gate` runs after `trunk_refusal`, so this is unlikely in practice.
- **Optional:** `board.html`'s badge shows only when `gate.current` is true. This matches R10 as the spec words it ("gate green or gate red"), and a stale record shows no badge, which is consistent with status. I'm noting it only because R10's "every manual card carries `gate`" could be read as showing a stale badge. I read the spec as intending the current-only reading.
- **D1 (default decision):** the by-hand steps can't run on 091 itself, because its folder holds `runs/`. The fixture tests cover the same steps, so I accept the default.
- **Done well:**
  - The tree-changed check and the build hash share one walk of the paths, so the record names exactly the build it judged.
  - A malformed record returns `problems` and `current: false` rather than raising.
  - The `_seen()` order puts `findings.md` first, then the gate, then the stage, which preserves 080's inference.
  - The factory's readers are untouched.
- **Ran:** `./check.sh`. ruff check passed, ruff format passed, 1937 tests passed and plugin validation passed. The factory plugin's missing-icon warning is not an error and is not from this change.
