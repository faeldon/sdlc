The retrospective's approval dialog now asks a second question, a 1–4 rating of how working with the process felt, plus an optional line. The committed report records both under `## Experience`, and the next retrospective reads the last rating back as a trend. The full gate passes (3534 passed, 29 skipped, ruff clean, plugin validate OK), and nothing is committed.

## What was built
I wrote `plan.md` first, then built in seven slices:
1. **Reading the answer** (R4): `experience_answer()` pulls a rating and a line out of the person's answer, e.g. "2 the reviews dragged" gives rating 2 and that line.
2. **The report section** (R5, R6, R10): `_experience_text()`, `_experience_trend()`, the new `## Experience` / `{{experience}}` in `templates/retro.md`, and `render_report(experience=…)`. `retro --report` previews a draft if one exists. With no answer the section says `NOT_RATED`.
3. **The commit** (R5, R7, R8): `retro-commit` handles the new draft, `.sdlc/retros/<date>.experience.md`, the same way it handles the insights draft. It refuses a draft with no `Answer:` line before writing anything, renders it into the report, never commits it, and deletes it only after the commit succeeds.
4. **Reading back** (R9): `_last_rows()` gains `experience`, read from the same lookup of the last report that `report_figures()` already does. `retro` prints `experience: {last}`.
5. **Metrics** (R11): a test pinning that a two-question dialog's reply is the first answer. There's no metrics code change, so it passed the first time it ran.
6. **The skill** (R1–R3, R12): Step 0 names `experience`. Step 2's Direction pass treats it as a hint, never a finding on its own. Step 5 asks the rating in the same dialog call, after the approval, and the rating never approves. Step 6 writes the answer word for word. Step 7 says whether a rating was recorded.
7. **Docs** (R13, R15): an *Experience* paragraph in REFERENCE.md, `{{experience}}` listed as optional, the experience draft added to PROCESS.md's retro node and AGENTS.md, and `sdlc.py record` re-run. `drift` reports nothing to refresh or break.

## Tests added
- **`tests/test_retro.py`:**
  - `test_an_experience_answer_reads_its_rating_and_line` (11 cases, R4)
  - `test_retro_commit_renders_the_rating_and_removes_its_draft` (R5)
  - `test_a_rating_with_no_line_says_so` (R5)
  - `test_the_experience_says_not_rated_without_a_draft` (R6)
  - `test_retro_commit_refuses_an_experience_draft_without_an_answer` (R7)
  - `test_a_failed_commit_leaves_the_experience_draft_for_a_rerun` (R8)
  - `test_the_next_retro_reads_the_last_rating_back`, `test_the_experience_trend_needs_both_ratings` and `test_a_report_without_the_table_reads_back_as_no_last` (R9)
  - `test_experience_is_not_a_template_read` and `test_an_override_without_experience_still_renders` (R10)
  - `test_reference_names_the_rating_and_its_draft` (R13)
  - `test_reference_and_step_0_name_the_aim_keys` (R14). It passed when first run, because both docs already name the keys; it now guards them.
- **`tests/test_skills.py`:** `test_the_retro_wait_asks_the_rating_second_in_its_dialog` (R1–R3) and `test_the_retro_skill_reads_the_last_rating` (R12).
- **`tests/test_metrics.py`:** `test_a_two_question_gate_reads_its_approval_from_the_first_answer` (2 cases, R11).
- **Existing tests changed:** `SECTIONS` gains `Experience`. `test_render_report_takes_the_figures_whole` pins `render_report`'s arguments, so it now includes `experience`, as the spec's design requires.

The new script and skill tests failed before the code existed, for the expected reason: the functions and text weren't there yet.

## Changes to `plan.md`
It now lists `_last_experience()` and the updated signature test.

## Left in `notes.md`
- [ ] The spec asks for one by-hand check before ship: read a real `/sdlc:retro` transcript with the two-question dialog and confirm the approval's answer comes first. R11 only tests the transcript shape the code reads, not what Claude Code actually records.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_retro.py -k "experience or rating or aim_keys or sections_come or without_insights"   (before the code)
26 failed, 2 passed, 253 deselected in 3.76s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k "rating" tests/test_metrics.py::test_a_two_question_gate_reads_its_approval_from_the_first_answer   (before the skill edit)
2 failed, 425 deselected in 0.26s
exit: 1

$ uv run --quiet --script scripts/sdlc.py record
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift
"breaking": [], "refresh": [], "report": []
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_skills.py tests/test_metrics.py tests/test_feature_map.py tests/test_defaults.py tests/test_modules.py
1080 passed in 24.01s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
328 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 190
All checks passed!
3534 passed, 29 skipped in 171.03s (0:02:51)
✔ Validation passed
exit: 0
