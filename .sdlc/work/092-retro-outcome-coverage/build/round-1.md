I built all of R1–R10 and left it uncommitted for `/sdlc:ship`. The gate passes with 1916 tests.

I went beyond the spec in one place: R1 only reads a goal's first line, but this repo's G6–G8 wrap onto a second, indented line, and their `(O…)` is on that line. Read that way, the spec's own Verification fails: `retro` listed G6–G8 as uncited. So an open goal's indented continuation lines are now read for its citation. Its `title` still holds only the first line, and a struck goal's wrapped lines are never read, since they belong to its reason. With that, `retro` on this repo lists M10–M15 as uncited (`why: none`) and leaves G6–G8 out, which is what the spec expects. `plan.md` records this.

**Slices built**
1. **Goal citations (R1, R3).** `CITES_RE` and `_goal_cites()` in `doc_items()`, including the wrapped-goal reading above. Every item now has a `serves` list, and nothing reaches `problems`.
2. **Milestone `Serves:` line (R2, R4).** `SERVES_RE` takes the first line under a milestone only. The "first line" check uses a local set, so the items gain no extra key.
3. **`product.uncited` (R5).** `_uncited()` in `retro.py`. `why` is `none`, `closed` or `unknown`. The spec leaves two cases open, and I made a call on each:
   - A milestone citing only a goal that cites nothing counts as `none`.
   - Citations that mix a struck outcome with an unknown id count as `unknown`.
4. **`product.none_themes` (R6, R7).** `_none_themes()` reads each change's seeds from the register as it stood at the change's base, with one `git show` per base. A change counts under `(no theme)` only when none of its seeds has a theme. `NONE_THEME_RECURS = 3`.
5. **Template (R8).** `templates/direction.md`: the example's G1 now ends `(O1)`, M1 has `Serves: G1`, and the note and prompts ask for both.
6. **Skill and docs (R9, R10).** Step 0 and passes 4 and 5 of `skills/retro/SKILL.md`, and the goals-and-milestones paragraph in `docs/REFERENCE.md`. The WAIT question is unchanged.

**Tests added**
- **R1:** `test_a_goal_cites_the_outcomes_at_the_end_of_its_line`, which covers the wrapped, struck and wrong-kind cases.
- **R2:** `test_a_milestone_cites_on_its_serves_line`.
- **R3:** `test_citations_never_add_a_problem` (3 cases) and `test_retro_commit_takes_an_uncited_goal`.
- **R4:** `test_next_up_is_the_same_with_and_without_serves_lines`.
- **R5:** `test_retro_names_goals_and_milestones_that_reach_no_open_outcome`.
- **R6:** `test_none_changes_are_grouped_by_their_seeds_themes`. The seeds are deleted in each change's ship commit, so reading today's register would fail it.
- **R7:** `test_a_theme_recurs_at_three_none_changes` (3 cases).
- **R8:** `test_the_templates_example_parses_to_its_ids` now checks `serves`.
- **R9:** `test_the_retro_skill_names_the_coverage_fields`.

The R3 and R4 tests passed from the start, so they guard existing behaviour rather than prove new code. All the others failed first for the expected reason: a missing key, or `[]` for the wrapped goal.

Nothing was left in `notes.md`.

- DECISION: [default] Should a wrapped goal's indented continuation lines be read for its `(O…)` citation, which goes beyond R1's "end of its title"? Options: read them; read the first line only. Going ahead with reading them: without it the spec's Verification fails on this repo's own G6–G8.
- DECISION: [default] How should the two `why` cases the spec leaves open read? Going ahead with `none` for a milestone that cites only a goal citing nothing (it reaches no outcome at all), and `unknown` for a struck outcome mixed with an unknown id (the likely typo is the more useful thing to show).

## Evidence

$ ./check.sh
All checks passed!
191 files already formatted
1916 passed in 80.51s (0:01:20)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py tests/test_next_up.py tests/test_skills.py -k "cites or serves_line or citations_never or uncited_goal or reach_no_open or seeds_themes or recurs_at or templates_example or with_and_without_serves or coverage_fields"
15 passed, 474 deselected in 8.61s
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py tests/test_next_up.py tests/test_skills.py -k "cites or serves or citations or uncited or none_ or recurs or coverage or templates_example"   (before the code: red)
FAILED tests/test_retro.py::test_a_goal_cites_the_outcomes_at_the_end_of_its_line
FAILED tests/test_retro.py::test_none_changes_are_grouped_by_their_seeds_themes - KeyError: 'none_themes'
8 failed, 9 passed in 5.61s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k reach_no_open   (before the code: red)
FAILED tests/test_retro.py::test_retro_names_goals_and_milestones_that_reach_no_open_outcome
1 failed, 117 deselected in 13.21s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k cites_the_outcomes   (wrapped goal, before its code: red)
E       AssertionError: assert [] == ['O2', 'O5']
exit: 1

$ uv run --quiet --script scripts/sdlc.py retro | python3 -c '…print uncited ids and why…'
[('M10', 'none'), ('M11', 'none'), ('M12', 'none'), ('M13', 'none'), ('M14', 'none'), ('M15', 'none')]
exit: 0
