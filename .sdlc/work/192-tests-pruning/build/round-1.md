I went through all of retro's drifted tests and changed two files. Of the ten files the idea named, retro no longer lists any. On the current list, one entry was a misread and one test had a real gap; the other five are kept, with the reasons in `notes.md`. Nothing is committed, and I haven't run the whole suite; the gate will.

**Changes**
- **A file wrongly counted as a test.** `skills/spec/SKILL.md` was listed because the rule for spotting tests treats any `spec` folder as a test folder. Here that folder is the spec skill. `.sdlc/config.toml` now sets `retro.test_paths = ["tests/"]`. With that config, retro's drift list no longer names the file. `retro` reads the main checkout's config, so its own run shows this only after the change lands.
- **A gap in `tests/test_hand_gate.py`.** Change 187 added `command` and `summary` to `hand_gate()`, and only the board's tests checked them. `test_hand_gate_reads_none_current_and_stale` now asserts both. It failed with `command` taken out of `hand_gate()`, and passes with the code restored.

**Kept, unchanged**
- **The ten named files:**
  - The board fixture `012-draft-publish` has fallen out of retro's 30-change lookback. Three board tests compare it exactly with what the factory writes now, so it can't drift without failing.
  - `test_config_resolution.py`, `test_indicators.py` and `test_adoption.py` have been edited since the idea was filed. Every function in `indicators.py` has a test.
- **Three exact-match files:** `land-record-cases.json`, `close-output.json` and `tests/prompts/land-fix.txt`. Each is compared exactly by its test (the last by `test_prompts.py`), so any drift fails the gate.
- **`test_function_heat.py`:** the script it tests hasn't changed since 177.
- **`test_metrics.py`:** it tests `metrics.py` and never mentions `retro.py`, which is the file that moved.

No test was deleted, so no assertion had to move.

**Files written**
- `plan.md`: written, though this is Tier 1.
- `checks.md`: one acceptance check, that the config holds `test_paths = ["tests/"]`.
- `notes.md`: the reason for each file, plus one unticked follow-up. Retro counts a test's code as every code file its last change touched, so tests edited alongside `sdlc.py` and the exact-match files keep showing up. A narrower rule would make the list worth acting on.

- DECISION: [default] Set this repo's `retro.test_paths` to `["tests/"]` alone, leaving `evals/` out? Going ahead with `["tests/"]` unless told otherwise.
  - OPTION: `["tests/"]` — fixes the `spec` misread; `evals/` files count as they do today (code or docs, by suffix); evals' drift goes unreported
  - OPTION: `["tests/", "evals/"]` — the skills' cases count as tests too; it shifts retro's totals and file counts by kind well beyond fixing the misread
  - WHY: the smallest setting that fixes the misread, leaving every other path counted as it is now

- UNTESTABLE: none

## Evidence

$ uv run --quiet --script scripts/sdlc.py retro > /tmp/retro192.json (drifted list read from it)
tests.drifted: land-record-cases.json (19), close-output.json (7), test_function_heat.py (6), test_hand_gate.py (6), skills/spec/SKILL.md (4), tests/prompts/land-fix.txt (4), test_metrics.py (4)
exit: 0

$ uv run --group dev pytest -q tests/test_hand_gate.py::test_hand_gate_reads_none_current_and_stale   (with `command` removed from hand_gate(), restored after)
FAILED tests/test_hand_gate.py::test_hand_gate_reads_none_current_and_stale
1 failed in 0.67s
exit: 1

$ uv run --group dev pytest -q tests/test_hand_gate.py
49 passed in 14.09s
exit: 0

$ uv run --group dev python /tmp/drift192.py "$PWD"   (retro's pruning pass with this worktree's config)
test_paths ['tests/']
19 tests/fixtures/land-record-cases.json
7 tests/fixtures/close-output.json
6 tests/test_function_heat.py
6 tests/test_hand_gate.py
4 tests/prompts/land-fix.txt
4 tests/test_metrics.py
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_config_resolution.py tests/test_retro.py tests/test_defaults.py tests/test_nothing_local.py
397 passed in 26.37s
exit: 0

$ uv run --group dev pytest -q tests/test_prompts.py
63 passed in 4.32s
exit: 0

$ uv run --group dev ruff check tests/test_hand_gate.py && uv run --group dev ruff format --check tests/test_hand_gate.py
All checks passed!
1 file already formatted
exit: 0

$ sh -c "<checks.md's sh block>"
exit: 0
