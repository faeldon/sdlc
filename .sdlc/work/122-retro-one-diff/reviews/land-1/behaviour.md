VERDICT: PASS

The change does what its intent says. `retro` output is unchanged, and the `-U0` diff now runs once per change instead of twice. The gate record is green and I found no failures.

- Diff against main is one code commit (`49227d6`) on top of current main `f4a5084`, so the rebase is clean. It touches `scripts/retro.py` and `tests/test_retro.py`, plus the change's own folder and one intentional removal of seed `2026-11-17-88` from `inbox.md`.
- `_diffs()` builds one `_added_diff()` per change. `_rework()` and `_spend()` read that map. Every index into it comes from the same `changes` list, so there is no KeyError path. The `-U0` arguments are the same strings the old inline calls used.
- End to end, `retro --metrics` on a scratch clone at the change's HEAD and a scratch clone with main's `retro.py` produce byte-identical output (18,929 lines, 51 spend rows, 9 rework entries). I set the host's `retro.evidence` to empty in those clones only, so the real repo's evidence command never ran.
- The new test passes on HEAD and fails on main's `retro.py` (each change's diff runs twice). The full `tests/test_retro.py` passes (122 tests).

## Notes

- **Gate record** (`build/round-1.gate.md`, `build/land-1.gate.md`): both `GATE: PASS` on `./check.sh`. I did not rerun the gate.
- **`test_a_retrospective_reads_each_change_s_diff_once`** (both parametrizations): expected to pass. It counts `diff -U0` calls per change for `retro` and `retro_report` on a two-change fixture. Result: passes on HEAD, fails on main's code with `Counter({'…': 2, …})`.
- **Full `tests/test_retro.py`**: expected to pass. Result: 122 passed.
- **Naming, not a failure:** `intent.md` names the helper `_change_diff()`, but the code calls it `_diffs()`. The intent's Outcome and Approach are met either way.
- **Behaviour note:** `_diffs()` now also computes the `diff-tree` diff for a change with no base, which `_rework()` skips. `_spend()` already read that diff, so the extra git call is not new. Output is unchanged.
- **No `checks.md`:** this is Tier 1, so there are no acceptance checks to read.

## Evidence

$ git log --oneline -5 && git merge-base HEAD main && git rev-parse main
  Output: `49227d6 Retro reads each change's diff once` (HEAD); merge-base and main both `f4a50848…`
  exit: 0

$ git diff main...HEAD -- scripts/retro.py tests/test_retro.py
  Output tail: `+    getattr(sdlc.retro, run)(root, cfg, date(2026, 10, 24))` / `+    assert len(diffs) == 2 and set(diffs.values()) == {1}, diffs`
  exit: 0

$ git status --short
  Output: `?? .sdlc/work/122-retro-one-diff/build/land-1.gate.md`, `?? .sdlc/work/122-retro-one-diff/runs/reviewer-behaviour.sessions`
  exit: 0

$ head -5 .sdlc/work/122-retro-one-diff/build/round-1.gate.md
  Output: `GATE: PASS` / `Verdict: PASS` / `Command: ./check.sh` / `Exit: 0`
  exit: 0

$ head -5 .sdlc/work/122-retro-one-diff/build/land-1.gate.md
  Output: `GATE: PASS` / `Verdict: PASS` / `Command: ./check.sh` / `Build: 49227d67df6e01f6` / `Exit: 0`
  exit: 0

$ cat .sdlc/work/122-retro-one-diff/intent.md
  Output tail: `## Approach` / `Read each change's -U0 diff once in retro(), keyed by the change, and hand it to both` / `_rework() and _spend(). Pin the call count with a test that wraps sdlc._git.`
  exit: 0

$ cat .sdlc/work/122-retro-one-diff/decision.md
  Output head: `DECISION: READY` / `Each change in a retrospective now gets one git diff -U0 instead of two…`
  exit: 0

$ sed -n 800,850p scripts/retro.py
  Output: `_rework` loop over `changes`, `diff = diffs[rec["name"]]` after the `if not base: continue` guard
  exit: 0

$ grep -n "def _added_diff" -A8 scripts/retro.py
  Output: `_added_diff` uses `diff -U0 --no-renames base sha` with a base, `diff-tree -U0 -p` without
  exit: 0

$ grep -n "^\[retro" -A6 .sdlc/config.toml
  Output: `[retro]` / `evidence = ["uv run --quiet --script .sdlc/evidence.py"]`
  exit: 0

$ git clone -q --local --branch main <worktree> /tmp/r122.uU3k/A && git -C A fetch -q <worktree> 122-retro-one-diff:refs/heads/hand && git -C A checkout -q hand; cp -R A B; cp main's scripts/retro.py into B; sed evidence = [] in both config.toml
  Output: scratch clones A (change HEAD `49227d6`) and B (main's `retro.py`), both with `evidence = []`
  exit: 0

$ (in A) PYTHONDONTWRITEBYTECODE=1 uv run --quiet --script scripts/sdlc.py retro --metrics > outA.txt
  Output tail: JSON ending `"recorded": true, "why": null` `}` `}` `]` `}` `}`
  exit: 0

$ (in B) PYTHONDONTWRITEBYTECODE=1 uv run --quiet --script scripts/sdlc.py retro --metrics > outB.txt
  Output: 18929 lines each; `cmp outA.txt outB.txt` identical
  exit: 0

$ python3 -I -c "<load outA.txt; print keys, spend rows, rework length>"
  Output: `spend keys: ['changes', 'outliers', 'recorded', 'tiers', 'tools', 'unrecorded', 'why']`, `spend rows: 51`, `rework type: list len: 9`
  exit: 0

$ (in worktree) PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest tests/test_retro.py -q -p no:cacheprovider -k "diff_once or rework or spend or question"
  Output tail: `10 passed, 112 deselected in 6.66s`
  exit: 0

$ (in B, main's retro.py) PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest tests/test_retro.py -q -p no:cacheprovider -k diff_once
  Output tail: `E AssertionError: Counter({'5330c75': 2, '9c7fd23': 2})` / `2 failed, 120 deselected in 16.54s`
  exit: 1

$ (in worktree) PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest tests/test_retro.py -q -p no:cacheprovider
  Output tail: `122 passed in 59.90s`
  exit: 0

$ rm -rf /tmp/r122.uU3k && ls -d /tmp/r122.*
  Output: `removed`; then no matches
  exit: 1
