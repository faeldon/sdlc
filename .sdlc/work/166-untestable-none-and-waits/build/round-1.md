I built both halves of 166 and left them uncommitted. When the builder writes `- UNTESTABLE: none` (or `n/a`, any case, period or not), the run no longer stops on it. The builder and the behaviour reviewer are now told how to wait without `sleep`. I ran only the affected tests by name, not the whole suite; the gate does that next.

**Plan.** I wrote `plan.md`, since the Approach touches more than a couple of files. It settles both open questions:
- **Where "none" is dropped:** in the pattern itself, not where lines are read. Three readers use `UNTESTABLE_RE`: `early_stop()` and the `read_step()` in each module. The existing pin test keeps the two copies agreeing.
- **Where the wait guidance goes:** in the two agent files, not `common.md` or the prompts. `common.md` also reaches agents that have no Bash, and this way no recorded copy in `tests/prompts/*.txt` changes.

**Slice 1: an empty answer isn't an untestable requirement**
- **Fix:** `UNTESTABLE_RE` in `factory.py` and its copy in `scripts/factory_records.py` now refuse `none`, `n/a` and `na`, in any case, with or without a period. My first attempt still matched `none`, because the regex gave up the space and the check passed. Moving the whitespace inside the check fixed it.
- **Tests added:**
  - `test_an_empty_untestable_answer_is_no_requirement`: seven spellings don't stop `verdicts`, the real `R3 needs a live GitHub` still escalates, and lines like `none of R3 can run here` still count.
  - `test_the_step_record_drops_an_empty_untestable_answer`: core's and the factory's `read_step()` agree, so the board and `status` read the same.
  - Both failed first with `(['none'], True) == ([], False)`.
- **Docs:** `builder.md` now says to write no such line when every requirement has a test, and the factory README notes that `none` or `n/a` counts as no requirement.

**Slice 2: waiting without `sleep`**
- **Wording:** `builder.md` and `reviewer-behaviour.md` each gained a paragraph: never run `sleep` to wait; give the command its own timeout, or poll in one bounded loop (example: `for i in $(seq 30); do test -f out.log && break; sleep 2; done`).
- **Checked here:** a bare `sleep` is refused, but a `sleep` inside a bounded loop runs.
- **Why a `for` loop:** the `timeout` command isn't on macOS.
- **Test added:** `test_the_agents_that_wait_never_sleep`, which failed before the paragraphs were added.

**Tests run:** the 7 test files I touched or that check these files passed, 1255 passed and 28 skipped. Ruff reported three formatting problems, all blank lines from my inserts; I fixed them and both ruff checks now pass. After formatting, a final named run of 23 tests passed.

**`plan.md` changes:** the builder's waiting paragraph went into *Then: build it* instead of a new `## Waiting` section. Nothing was left in `notes.md`. As the intent says, I didn't touch the four open `factory.py` nits.

No untestable requirements and no decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py::test_an_empty_untestable_answer_is_no_requirement tests/test_board.py::test_the_step_record_drops_an_empty_untestable_answer
FAILED tests/test_factory.py::test_an_empty_untestable_answer_is_no_requirement
FAILED tests/test_board.py::test_the_step_record_drops_an_empty_untestable_answer
2 failed in 1.00s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py::test_the_agents_that_wait_never_sleep
FAILED tests/test_skills.py::test_the_agents_that_wait_never_sleep - Assertio...
1 failed in 0.15s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py::test_the_agents_that_wait_never_sleep tests/test_skills.py::test_the_builder_leaves_the_whole_suite_to_the_gate tests/test_skills.py::test_the_reviewers_read_the_gate_for_the_whole_suite tests/test_skills.py::test_what_runs_the_change_shows_its_evidence_and_never_runs_checks tests/test_skills.py::test_no_agent_but_the_builder_runs_checks tests/test_skills.py::test_the_script_gates_each_build_before_any_reviewer
6 passed in 0.05s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_board.py tests/test_modules.py tests/test_skills.py tests/test_prompts.py tests/test_defaults.py tests/test_nothing_local.py
1255 passed, 28 skipped in 17.12s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
304 files already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py::test_an_empty_untestable_answer_is_no_requirement tests/test_factory.py::test_an_untestable_requirement_escalates_after_its_round tests/test_board.py::test_the_step_record_drops_an_empty_untestable_answer tests/test_board.py::test_the_step_record_is_a_pinned_copy tests/test_skills.py::test_the_agents_that_wait_never_sleep tests/test_modules.py
23 passed in 3.64s
exit: 0

$ for i in 1 2 3; do test -f /nonexistent-166 && break; sleep 1; done; echo exit $?
exit 0
exit: 0
