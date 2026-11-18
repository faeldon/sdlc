The conflict in `tests/test_metrics.py` was already resolved when I opened it, so I made no edits. The file has no conflict markers, it keeps everything both changes added, and the full gate passes on the stacked tree.

Both changes had only added code at the end of the file, after `test_a_close_from_before_tool_lines_is_unrecorded`, which is why stacking them conflicted. The file now has 145's tests followed by 146's, separated by the usual two blank lines.

**What 145 (an escalation the person has dealt with clears without a rebuild) keeps:**
- Four new assertions in `test_sdlcs_copies_of_the_factorys_patterns_match_its_own` (about line 1199). They check that `sdlc.py`'s copies of `REASON_RE`, `LOOK_SOURCE_RE`, `REASON_KINDS` and `DECIDED` match `factory.py`'s.
- `test_a_cleared_escalation_still_measures_as_escalate` (requirement R14).
- `test_sdlcs_reasons_and_newest_round_are_the_factorys`.

**What 146 (measure how factory agents work, not only how long) keeps:**
- Everything from the `# ---- how an agent worked` divider on, unchanged:
  - the helpers `said`, `_role_events`, `_role_line`, `ONE_OF_EACH`, `BEHAVIOURS` and `WORKTREE`;
  - the tests for shell edits, test runs, background commands, behaviour counts, broken builds, `Sdlc-Calls`, `model=`, `behaviour=failed`, no text in the trailers, and old trailers still parsing (R1–R8 and R10–R12).

The file's 173 tests pass, ruff check and the format check are clean on it, and the full gate (`./check.sh`) passes: 2809 passed, 28 skipped, and the plugin validation passed.

## Evidence

$ grep -n '<<<<<<<\|>>>>>>>' tests/test_metrics.py; wc -l tests/test_metrics.py
    1784 tests/test_metrics.py
exit: 0

$ grep -n 'FACTORY_DECIDED\|def test_a_cleared_escalation\|def test_sdlcs_reasons_and_newest\|how an agent worked\|def test_a_close_from_before_behaviours\|def test_a_close_from_before_tool_lines' tests/test_metrics.py
1203:    assert sdlc.FACTORY_DECIDED == factory.DECIDED
1409:def test_a_close_from_before_tool_lines_is_unrecorded() -> None:
1420:def test_a_cleared_escalation_still_measures_as_escalate(tmp_path: Path) -> None:
1458:def test_sdlcs_reasons_and_newest_round_are_the_factorys(tmp_path: Path) -> None:
1488:# ---------------------------------------------------------------- how an agent worked
1761:def test_a_close_from_before_behaviours_parses_as_before() -> None:
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_metrics.py
173 passed in 7.60s
exit: 0

$ uv run --group dev ruff check tests/test_metrics.py && uv run --group dev ruff format --check tests/test_metrics.py
All checks passed!
1 file already formatted
exit: 0

$ ./check.sh
2809 passed, 28 skipped in 95.11s (0:01:35)
✔ Validation passed
✔ Validation passed
exit: 0
