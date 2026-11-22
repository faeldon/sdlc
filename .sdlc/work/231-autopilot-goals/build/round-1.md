I built change 231 in eight slices, test first, and left it uncommitted. Every named test set passes. The full gate found one failure: a new test took a `monkeypatch` fixture it never used. I removed it and reran that test and the file, but I haven't rerun the full suite since. The script's gate will run it again.

**Slices**
1. **R1:** a new `direction_open()` in `sdlc.py` reads the direction doc's open goals and milestones. `status --json` prints it as `direction` beside `next_up`, with each milestone's grouped seeds turned into open register ids by `ref_matches()`. Struck items are left out.
2. **R2, R3:** `resolve_goal()` and `goal_scope()` read `--goal` by its form: `G<n>`/`M<n>`, `theme:<name>`, or any other text as a stated goal. `candidates(…, goal)` only drops seeds outside the goal's scope; it never adds any. Guards and holds never read the goal.
3. **R4, R5:** with no goal given, `propose_goal()` proposes the first open milestone that has a candidate, else the theme with the most candidates. It also lists up to three alternatives. `preview_question()` names the goal, and `shown` opens with a `Goal:` block. A `--goal` id the doc doesn't hold open is refused. With no goal to propose, `question` is null and `warnings` says so.
4. **R6, R11 start:** `--goal` is on the CLI. `--begin` refuses without a goal, resolves it again, and writes `state["goal"]` and `state["register"]["start"]`. `register_ids()` skips fenced example lines.
5. **R7, R8:** the planner's brief carries `## Goal` and `Level:`. `read_plan()` replaces `read_wave()` and refuses every case R8 lists. `NONE` is retired.
6. **R9, R10:** a seed the planner leaves (LEAVE) is kept in `state["seeds"]` with its kind and is never offered again. The run never writes the register or the direction doc. The intent brief gets a `Planned: tier <n>, <group>: <why>` line, and the intent-writer's own tier still decides.
7. **R11, R12:** the summary gains `## Goal`, `## The plan` and `## Left for you`, plus the register's count, `filed` and `drained`, and the "grew faster" line under `## The run`. A state from before this change resumes: no goal, nothing narrowed, and the summary says the register wasn't counted.
8. **R13:** I rewrote the skill's Steps 1–3 and description, the `wave` prompt part (and re-recorded `tests/prompts/autopilot-wave.txt`), the planner agent, the README's *Autopilot* section and the autopilot line in `docs/FEATURES.md`. No new `Bash(...)` rule was needed.

**Tests added**, all in `tests/test_autopilot.py`, one per requirement:
- `test_goals_come_from_the_real_status_json` (R1)
- `test_a_goal_is_read_by_its_form` (R2)
- `test_a_goal_only_narrows_the_candidates` (R3)
- `test_the_preview_proposes_a_goal_when_none_is_stated` (R4)
- `test_the_preview_names_a_goal_from_the_direction_doc` (R5)
- `test_the_wave_brief_names_the_goal` (R7)
- `test_the_planner_places_every_candidate` (R8: each bad reply refused for its own stated reason)
- `test_a_seed_the_planner_leaves_is_left_for_the_person` (R9: register and direction doc byte for byte the same)
- `test_the_intent_brief_carries_the_plan` (R10)
- `test_the_summary_says_whether_the_register_grew` (R11)
- `test_a_run_begun_without_a_goal_resumes` (R12)
- `test_the_skill_quotes_the_preview_question` (R13)

I extended `test_autopilot_preview_writes_nothing`, `test_autopilot_begin_refusals` (cases `no goal` and `a closed milestone`), `test_autopilot_begin_writes_the_state_once`, `test_planner_reply_is_checked_by_the_script` and `test_autopilot_end_to_end` (the byte checks). The test stand-in `Steps` now builds plan replies that place every candidate, so the existing loop tests use the new format.

One bug turned up while building: `cited_paths()` stripped a leading dot, so `.gitignore` was never found. It's fixed, and the R9 test covers it.

**Named runs**
- `tests/test_autopilot.py` + `test_skills` + `test_modules` + `test_feature_map` + `test_prompts` + `test_windows` + `test_nothing_local`: 811 passed.
- Full gate: 1 failed, 4043 passed, 29 skipped. The failure is the unused fixture above.
- After the fix, `test_suite_shape.py` + `test_autopilot.py`: 73 passed. Ruff check and format check are clean, and both strict plugin validations pass.

**plan.md:** written before the code. I updated it after the build to add the extra R5 test and the re-recorded golden prompt.

**notes.md:** nothing left in it.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest tests/test_autopilot.py tests/test_skills.py tests/test_modules.py tests/test_feature_map.py tests/test_prompts.py tests/test_windows.py tests/test_nothing_local.py -q -n auto
811 passed in 18.11s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 231
FAILED tests/test_suite_shape.py::test_no_test_takes_a_fixture_it_never_uses
E         test_autopilot.py: test_a_goal_only_narrows_the_candidates: monkeypatch
1 failed, 4043 passed, 29 skipped in 312.90s (0:05:12)
exit: 0

$ uv run --group dev pytest tests/test_suite_shape.py tests/test_autopilot.py -q -n auto
73 passed in 44.79s
exit: 0

$ uv run --group dev ruff check tests/test_autopilot.py
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
344 files already formatted
exit: 0

$ claude plugin validate --strict .
✔ Validation passed
exit: 0

$ claude plugin validate --strict plugins/factory
✔ Validation passed
exit: 0

$ SDLC_RECORD_PROMPTS=1 uv run --group dev pytest tests/test_prompts.py -q -k autopilot-wave
1 passed, 71 deselected in 0.18s
exit: 0

$ grep -n "NONE\|rank order" plugins/factory/README.md plugins/factory/skills/autopilot/SKILL.md plugins/factory/agents/autopilot-planner.md plugins/factory/prompts/autopilot.md
plugins/factory/skills/autopilot/SKILL.md:106:register's ready seeds within the bounds, in rank order; a seed with an `Issue:` line only when
plugins/factory/prompts/autopilot.md:10:You are autopilot's planner, … its candidates in rank order, already narrowed to the goal, …
exit: 0

$ grep -c "^<" .sdlc/work/231-autopilot-goals/plan.md
0
exit: 1
