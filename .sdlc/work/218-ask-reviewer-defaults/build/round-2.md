Round 2 is built. The person's answer to D2 was "autopilot holds such a change", and it now does. Before it answers a change's open defaults and lands it, autopilot holds the change if one of those defaults came from a reviewer or the approver and no later builder round says it built it. The named tests pass (688 across four files) and ruff is clean. I didn't run the full gate; the script runs it next. Nothing is committed and `HEAD` is still `3bafdfd`.

**Slices built**
1. **Round 2, the D2 hold:**
   - `unbuilt_defaults(folder, lines)` in `factory.py` now takes the ledger lines to check. `cmd_ask()` passes the defaults the person kept, so `ask` works as in round 1.
   - `hold_causes()` in `autopilot.py` passes the open lines that `finish()` would answer. While any of them is unbuilt, the change is held with the cause "a reviewer's or the approver's default no build made: D<n>".
   - The function stays in `factory.py` because both scripts call it.
2. **Docs:**
   - The factory README's *What it holds* paragraph and the autopilot skill's hold paragraph now name the new hold.
   - I fixed F1 (README lines past the wrap width) and rewrapped that paragraph, which already ran past 100 columns.
   - I added the comment F2 asked for at `unbuilt_defaults()`: a `source` that names no round reads as round 0.

**Tests added**
- `test_held_change_and_its_dependents_never_land[unbuilt]`: a change with a security reviewer's open default and no `- BUILT:` line is held, and the change that depends on it never builds. It failed first, `assert 'landed' == 'held'`, which is 216's gap.
- `test_a_reviewer_s_default_a_later_build_made_lands`: the same default with a round-2 `- BUILT: D1` line is answered as autopilot and lands, so the hold doesn't catch what a build made. It passed before the hold existed, as expected: nothing held anything yet.

**Named runs**
- The two new tests: 2 passed.
- `test_autopilot.py`, `test_factory_decisions.py`, `test_modules.py` and `test_skills.py`: 688 passed.
- `test_feature_map.py` and `test_nothing_local.py`: 17 passed.
- I also named `tests/test_factory.py` in one run, but that file doesn't exist, so no tests ran there.

**plan.md:** added slice 4 (the D2 hold), the `autopilot.py` and autopilot skill edits under *Files to change*, and the two tests under *Tests*.

**notes.md:** doesn't exist; nothing left.

**Decisions:** none raised this round. D1 is settled and D2 is answered.

- UNTESTABLE: none

## Evidence

$ cat .sdlc/work/218-ask-reviewer-defaults/decision-1.md .sdlc/work/218-ask-reviewer-defaults/decisions.md
(D2 → decided: autopilot holds such a change)
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py -k "unbuilt or reviewer_s_default"
E       assert 'landed' == 'held'
FAILED tests/test_autopilot.py::test_held_change_and_its_dependents_never_land[unbuilt]
1 failed, 1 passed, 54 deselected in 2.48s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py tests/test_factory_decisions.py -n auto
156 passed in 21.33s
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py -k "unbuilt or reviewer_s_default"
2 passed, 54 deselected in 1.54s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_autopilot.py tests/test_factory_decisions.py tests/test_modules.py tests/test_skills.py
688 passed in 10.58s
exit: 0

$ uv run --group dev ruff check plugins/factory/scripts tests/test_autopilot.py && uv run --group dev ruff format --check plugins/factory/scripts tests/test_autopilot.py
All checks passed!
5 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_feature_map.py tests/test_nothing_local.py tests/test_factory.py
no tests ran in 0.58s
exit: 4

$ uv run --group dev pytest -q -n auto tests/test_feature_map.py tests/test_nothing_local.py
17 passed in 1.08s
exit: 0

$ git log --oneline -1
3bafdfd Close 216-autopilot
exit: 0
