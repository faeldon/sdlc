I've resolved the conflict in `tests/test_metrics.py`, but the full gate still fails: 1 test fails, 2805 pass and 28 are skipped. That failure comes from change 144's own run records, not from this file.

**The resolution.** Both sides only added new tests at the end of the file, after `test_a_close_from_before_tool_lines_is_unrecorded`, and none of them overlap. I kept everything from both sides, removed the conflict markers and put the usual two blank lines between them:
- **145 (the side I'm stacking onto):** kept `test_a_cleared_escalation_still_measures_as_escalate` and `test_sdlcs_reasons_and_newest_round_are_the_factorys` unchanged.
- **146 (this change):** kept the whole `# --- how an agent worked` section after them, unchanged. Those are its tests for how agents work: tool calls and errors, word counts, per-role runs and tokens, and the trailer round-trips.
- **144 and 147** have no lines in this file's conflict.

The file passes ruff check and ruff format, and all 173 of its tests pass.

**The red gate.** The failing test is `tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden`. All 12 lines it flags are in `.sdlc/work/144-factory-records-and-models/`: `entries.md`, `reviews/round-1/behaviour.md` and `reviews/round-1/code.md`. They are short folder paths like `work/<144>*-x` and `.sdlc/work/<144>/`, written while reviewing 144's path-rewriting. The folder comes from 144, lower in the train. Neither this change nor this file wrote it, and I was told to edit only the conflicted file, so I didn't touch it. The tip of the train will hit the same failure. 144's records need rewording, or the test needs to allow a change folder's own review records.

- DECISION: [blocking] How should the train get past the forbidden-text test failing on 144's review records? Recommend rewording 144's records.
  - OPTION: reword 144's `entries.md` and `reviews/round-1/*.md` so they don't use those short paths — the smallest fix, and the test stays as strict as it is; it rewrites what a review recorded
  - OPTION: let the test skip a change folder's `reviews/` and `entries.md` — review records are left as written; a forbidden name could then get into the repo through a review
  - WHY: the test is a rule for the whole repo, and only one change's records break it

## Evidence

$ uv run --group dev ruff format --check tests/test_metrics.py
1 file already formatted

$ uv run --group dev ruff check tests/test_metrics.py
All checks passed!

$ uv run --group dev pytest -q -n auto tests/test_metrics.py
173 passed in 1.20s
exit: 0

$ uv run --group dev pytest -q tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden
E       AssertionError: assert ['.sdlc/work/...x/build', ...] == []
E         Left contains 12 more items, first extra item: '.sdlc/work/144-factory-records-and-models/entries.md:9: ## [2026-11-18-62] [nit] `work/<008>*x` is rewritten to ...'
FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden

$ set -o pipefail; ./check.sh 2>&1 | tail -3
FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden - A...
1 failed, 2805 passed, 28 skipped in 87.45s (0:01:27)
exit: 1
