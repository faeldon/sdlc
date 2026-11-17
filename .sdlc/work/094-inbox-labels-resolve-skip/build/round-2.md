I've addressed the one kept change: a mend now really happens once, enforced by the script rather than only by the build skill. The gate passes (1907 tests, exit 0), the work is uncommitted, and `HEAD` is still `95a03ee`.

**code C1, "nothing records a mend":**
- **The record:** when `agent --task mend` files a reply, it appends a `<role> <round>` line to a new file, `runs/mended`. For the builder the round is its report's round; for a reviewer it is the last review round.
- **The stop:** `verdicts` stops treating a role as mendable once that file names it for the round. A second reply that still needs a mend is then a `rerun` stop, and `mend` lists nothing.
- **The refusal:** `agent` refuses a second mend for the same role and round ("code was mended once in round 1: a second is a stop") without starting a session.
- **The builder too:** the same record covers the builder's evidence mend, which had the same gap.

**Tests:**
- `test_a_reviewer_s_preamble_is_mended_by_the_same_reviewer` now goes on past the first mend: a second preamble reads as `rerun`, and the second mend is refused without calling `claude`. It failed first with `('stop', 'mend', ['code']) != ('stop', 'rerun', [])`.
- New `test_the_builder_s_evidence_is_mended_once_a_round` does the same for the builder: mend once, then `rerun`, then a refused second mend.
- In the first test, the "nothing to mend" check now uses `security`. `code` has been mended by that point, so the once-a-round refusal comes first.

**Docs:** AGENTS.md now says each role is mended once a round, recorded in `runs/mended`. That file is the one thing a run writes that `verdicts` reads back. I spelled this out because the same paragraph says `verdicts` "never reads a state file", a sentence about how deep the review runs. The build skill's `stop` step, the `verdicts` docstring and `plan.md` (new step 4, the new test, the new file) are updated to match.

Nothing new in `notes.md`. I raised no new decisions; the three `[default]` ones from round 1 still stand.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "preamble or mended_once" (before the fix)
E       assert ('stop', 'mend', ['code']) == ('stop', 'rerun', [])
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py::test_a_reviewer_s_preamble_is_mended_by_the_same_reviewer tests/test_factory.py::test_the_builder_s_evidence_is_mended_once_a_round
2 passed in 8.18s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py tests/test_board.py tests/test_next_up.py
209 passed in 60.65s (0:01:00)
exit: 0

$ ./check.sh
All checks passed!
196 files already formatted
1907 passed in 58.93s
✔ Validation passed
✔ Validation passed
exit: 0

$ git rev-parse --short HEAD
95a03ee
exit: 0
