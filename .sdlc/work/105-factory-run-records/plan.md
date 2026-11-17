---
id: 105
slug: factory-run-records
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 105 — A factory run's records say what it did · plan

> Written by the factory's builder after reading the code, under the run the person approved.
> Read by the reviewers beside spec.md; updated where the build departed from it.

## Files to change

- `plugins/factory/scripts/factory.py`: `split_draft()` (new, pure), `_task()`'s spec branches
  return `runs/spec-draft.md`, `cmd_agent()` writes the draft and the questions and drops
  `reply`; `cmd_write_spec()` (new) beside `cmd_stage()`, with `_scaffold()` copied from
  `sdlc.py`'s `is_unfilled()` (`PROMPT_RE`, `UNFILLED_THRESHOLD`); `SUPERSEDES_RE`, `SUPERSEDED`,
  `read_ledger()`'s `superseded_by` and `open`, `cmd_decisions()`'s marking and `unmarked`; the
  four `not d["decided"]` readers (`cmd_decisions`, `loop_state`, `land_signals`) to `open`, and
  `_task("decided")` to `decided`; `main()` gains `write-spec`; the docstring's write list.
- `scripts/sdlc.py`: `FACTORY_STEP`, `FACTORY_STEP_RE`, `FACTORY_ROUND_RE`,
  `FACTORY_AGENT_TIMEOUT` beside the other copies; `factory_first_build()` beside
  `factory_stop()`; `cmd_check`'s (`analyze()`'s) plan-template branch asks it.
- `plugins/factory/skills/build/SKILL.md`: Step 1 reads the two `runs/` files; Step 3 runs
  `write-spec` before `stage … design`; new rule for `write-spec`; the files list names both.
- `plugins/factory/skills/spec/SKILL.md`: drafts through `factory.py agent --task spec` in the
  background (revisions through a ticked `R<n> (person, revise)` line), shows the two files,
  writes with `write-spec`; drops `Agent`, keeps `Edit` for striking the intent's questions only,
  gains `Write` for the revise line, and rules for `agent` and `write-spec`.
- `plugins/factory/agents/spec-writer.md`: say the script files the reply, cut at the `---` line.
- `plugins/factory/agents/builder.md`, `reviewer-code.md`, `reviewer-security.md`,
  `reviewer-ui.md`, `reviewer-ux.md`: the `(supersedes D<n>)` form, and that a decided line can't
  be superseded.
- `plugins/factory/agents/approver.md`, `skills/ship/factory.md`, build's Step 4 hand-back: a
  `→ superseded by D<m>` line is no assumption; shown as one line beside its replacement.
- `plugins/factory/README.md`: the file tree gains `runs/spec-draft.md` and
  `runs/spec-questions.md`, and the command list `write-spec`.
- Tests: `tests/test_factory.py` (split, agent spec files, write-spec, supersede and its
  refusals, readers of `open`), `tests/test_sdlc.py` (first-build exemption), `tests/test_board.py`
  and `tests/test_metrics.py` (a superseded line; the new copies pinned), `tests/test_skills.py`
  (no `Edit` of `spec.md`, `write-spec` after the WAIT, builder's syntax).

Reused, not re-derived: `frontmatter()` for tier and stage, `find_change()`, `emit()`,
`read_revision()`, `FENCE_RE`'s shape (the fence tracker needs the marker's character and length,
so it gets its own regex beside it), `factory_stop()`'s never-raise reading for `step.md`.

## Work order

1. **The draft to a file (R1, R2).** Test `split_draft` on a fenced draft holding `---` and a
   nested fence, on no separator, on a preamble; then `agent --task spec` writing both files,
   `spec.md` untouched, `--revise`/`--recheck` overwriting. Code: `split_draft`, `_task`,
   `cmd_agent`.
2. **`write-spec` (R3).** Tests for the byte copy and the three refusals, and the scaffold rule
   pinned to `sdlc.py`'s. Code: `_scaffold`, `cmd_write_spec`, `main`.
3. **Skills read the files and write with `write-spec` (R4).** Test in `test_skills.py`; edit
   both skills, the spec-writer and the README.
4. **Supersede (R5, R6, R7).** Tests: the D2/D4 shape (same pass, and across passes), idempotent
   rerun, each refusal case, a superseded default absent from `assumed`, from the landing's
   signals, and refused as `--decision`. Code: `SUPERSEDES_RE`, `read_ledger`, `cmd_decisions`,
   the readers.
5. **Board and metrics read it right unchanged (R8).** Tests only; no code change expected.
6. **Agent docs (R9).** Test that `builder.md` holds the syntax; edit the agents, approver, ship's
   `factory.md`, build's hand-back.
7. **First-build exemption (R10, R11).** Tests in `test_sdlc.py` for each condition and that
   other problems still show; pin the copies in `test_metrics.py`. Code: copies,
   `factory_first_build`, the check branch.

Each slice ends with its tests green and `./check.sh` run.

## Tests

- R1: `test_the_spec_draft_is_written_whole_to_runs` (agent writes both files, spec.md untouched,
  no `reply`); the revise test checks both are overwritten.
- R2: `test_split_draft_*` — a fenced block with `---` and a nested longer fence, no separator,
  a preamble.
- R3: `test_write_spec_copies_the_draft_byte_for_byte`, `test_write_spec_refuses_*` (no draft,
  wrong tier/stage, spec.md not the scaffold); `test_the_scaffold_rule_is_sdlc_s_own`.
- R4: `test_the_spec_draft_reaches_spec_md_only_through_write_spec` in `test_skills.py`; the
  existing rule/command tests cover the new rules.
- R5: `test_a_default_supersedes_an_earlier_one_once`.
- R6: `test_a_supersede_that_can_t_apply_marks_nothing` (parametrized over the five cases).
- R7: `test_a_superseded_default_is_neither_assumed_nor_a_landing_signal_nor_a_decision`.
- R8: `test_a_superseded_default_is_not_assumed_on_the_board` (test_board.py),
  `test_a_superseded_default_is_not_open_in_the_metrics` (test_metrics.py).
- R9: `test_agents_say_how_a_default_supersedes` in test_skills.py.
- R10: `test_check_leaves_out_the_template_plan_during_a_live_first_build` and its
  parametrized negatives (report written, stop recorded, stale session, other step), plus other
  problems still shown.
- R11: `test_sdlcs_copies_of_the_factorys_patterns_match_its_own` extended.

## As built

Where the build departed from the spec's design or the plan above:

- The fence tracker uses its own `FENCE_MARK_RE` (`^ {0,3}(`{3,}|~{3,})(.*)$`) rather than
  `FENCE_RE`: closing a fence needs the opening marker's character and length, and CommonMark's
  rules that a closing line carries nothing after its marker and a backtick fence's info string
  holds no backtick. `FENCE_RE` is left as it is for `slice`.
- `agent --task spec` writes the questions file only when the reply has a separator, and removes
  an old one when it has none, so a revision never shows the last draft's questions beside a new
  draft. The draft is kept byte for byte, its blank line before the separator included; a newline
  is added only when a file wouldn't end with one.
- `decisions` also prints `superseded`, the ids it marked this pass, beside `unmarked`.
- `write-spec` reports every refusal at once, and treats a missing `spec.md` as not the scaffold.
- The factory README's *Decisions that are yours* says how a default supersedes another.
- R8's two tests pass without a code change, which is what R8 asks: they pin that ticking the
  superseded line keeps the board's and metrics' unedited readers right.

## Rollback

`git revert` undoes everything: the change writes only uncommitted run records
(`runs/spec-draft.md`, `runs/spec-questions.md`) in a change's own folder and, through
`decisions`, ticks a superseded line in a change's own `decisions.md`. A ledger line marked
`→ superseded by D<m>` before a revert reads, after it, as a decided line whose answer is empty:
untick it by hand (`- [x]` → `- [ ]`, drop the suffix) in any change still open.
