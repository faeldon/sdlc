# Build report: 105, round 1

I built all of R1–R11, test first. The repo gate passes: 2034 tests, ruff clean, plugin validation passes. Nothing is committed.

## Slices built

1. **The draft goes to a file (R1, R2).** `split_draft()` cuts the reply at the last bare `---` outside a fenced block. A fence only closes on the same character, at least as long. `agent --task spec` now writes `runs/spec-draft.md` byte for byte, and writes `runs/spec-questions.md` when the reply has questions. Its JSON gives `to`, `questions` and `preamble`, and no longer includes `reply`. `--revise` and `--recheck` overwrite both files. A reply with no separator removes the old questions file.
2. **`write-spec` (R3).** A new command that copies the draft into `spec.md` with `shutil.copyfile`. It refuses, writing nothing, when there is no draft, when the change isn't Tier 2 at `stage: plan`, or when `spec.md` is no longer the scaffold. The scaffold rule is a copy of `sdlc.py`'s, pinned by a test.
3. **The skills (R4).** `/sdlc-factory:build` and `/sdlc-factory:spec` now read the two `runs/` files and copy the spec with `write-spec` after the yes. The spec skill drafts through `factory.py agent` in the background, with revisions as `R<n>` lines. It no longer has the `Agent` tool and gains `Write`. I also updated `spec-writer.md` and the factory README.
4. **Superseded defaults (R5–R7).** A default written as `(supersedes D<n>)` ticks D<n> with `→ superseded by D<m>`, and changes no other line. The new line's text leaves the prefix out, and a rerun changes nothing. In five cases nothing is marked and the new default is listed under `unmarked` with the reason: the target doesn't exist, isn't a default, is decided, is already superseded, or is the new line itself. `read_ledger()` gains `superseded_by` and `open`. `pending`, `assumed` and the landing's open-decision signal now read `open`. `--decision` refuses a superseded line.
5. **Board and metrics (R8).** I added a test for each and made no code change: because the superseded line is ticked, their existing patterns already handle it. Both tests passed the first time they ran; that is what R8 asks for, so neither went red first.
6. **Agent docs (R9).** `builder.md` and the code, security, ui and ux reviewers now say how to write `(supersedes D<n>)`, and that a `→ decided:` line can't be superseded. The approver, ship's `factory.md` and build's hand-back say a superseded line is not an assumption and is shown beside the default that replaced it.
7. **The first-build exemption (R10, R11).** `factory_first_build()` in `sdlc.py` checks four conditions:
   - `runs/builder.sessions` was written less than 3 hours ago;
   - there is no `build/round-*.md`;
   - there is no `runs/stopped.md`;
   - `runs/step.md` is absent, or reads `STEP: build` with round empty or 1.

   When all hold, `check` leaves out the "plan.md is still the template at stage: build" problem and nothing else. The new copies (`FACTORY_STEP`, `FACTORY_STEP_RE`, `FACTORY_ROUND_RE`, `FACTORY_AGENT_TIMEOUT`) are pinned to `factory.py`'s.

## Tests added

| Requirement | Test |
|---|---|
| R1 | `test_the_spec_draft_is_written_whole_to_runs`; the revise test now also checks the draft is overwritten |
| R2 | `test_split_draft_cuts_at_the_last_separator_outside_a_fence`, `test_split_draft_without_a_separator_keeps_the_whole_draft` (6 cases) |
| R3 | `test_write_spec_copies_the_draft_byte_for_byte`, `test_write_spec_refuses_and_writes_nothing` (4 cases), `test_the_scaffold_rule_is_sdlc_s_own` |
| R4 | `test_the_spec_draft_reaches_spec_md_only_through_write_spec` (both skills); `test_judging_agents_return_text_the_skill_writes` now expects `write-spec` |
| R5 | `test_a_default_supersedes_an_earlier_one_once`, `test_a_default_can_supersede_one_raised_in_the_same_pass` |
| R6 | `test_a_supersede_that_can_t_apply_marks_nothing` (5 cases) |
| R7 | `test_a_superseded_default_is_neither_assumed_nor_a_signal_nor_a_decision` |
| R8 | `test_a_superseded_default_is_not_assumed_on_the_board`, `test_a_superseded_default_is_counted_but_not_open` |
| R9 | `test_agents_say_how_a_default_supersedes` |
| R10 | `test_check_leaves_out_the_template_plan_during_a_live_first_build` (3 cases), `test_the_template_plan_shows_once_the_first_build_is_not_live` (6 cases), `test_a_live_first_build_hides_no_other_problem` |
| R11 | `test_sdlcs_copies_of_the_factorys_patterns_match_its_own`, extended |

## plan.md

I wrote it before any code, and added an **As built** section listing where the build departed from the spec's design:
- The fence tracker has its own regex, `FENCE_MARK_RE`, rather than reusing `FENCE_RE`, because closing a fence needs the opening marker's character and length.
- The draft keeps the blank line before the separator, so it stays byte for byte.
- `decisions` also prints `superseded`, the ids it marked in that pass.
- `write-spec` reports every refusal at once, and treats a missing `spec.md` as not the scaffold.
- The factory README's "Decisions that are yours" section now explains superseding.

## notes.md

Nothing added. `.sdlc/work/inbox.md` was already modified (the seeds marked `[building]`) before I started; I didn't touch it.

## Decisions

None raised.

## Evidence

$ ./check.sh
All checks passed!
207 files already formatted
2034 passed in 61.05s (0:01:01)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k "spec_draft or split_draft or write_spec or scaffold_rule or supersede or superseded or decisions"
24 passed, 155 deselected in 2.36s
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py -k "first_build or template_plan"
10 passed, 204 deselected in 0.53s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py tests/test_metrics.py -k "supersed or copies"
3 passed, 158 deselected in 0.27s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py
347 passed in 0.33s
exit: 0

$ uv run --group dev pytest -q -m portable
240 passed, 1794 deselected in 67.54s (0:01:07)
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py write-spec 105
"refusals": ["no runs/spec-draft.md: run agent --task spec first", "write-spec is for a Tier 2 change at stage: plan, not tier 2 at stage: build", "spec.md is no longer the scaffold: a person's text is never written over"]
exit: 1
