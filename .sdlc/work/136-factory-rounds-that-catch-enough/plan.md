---
id: 136
slug: factory-rounds-that-catch-enough
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 136 — Factory rounds that catch what the landing catches, and stop early on a fault no round can fix · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `light_reviewers()`: add `behaviour` (either tier) beside `test` (Tier 2), each only when the
    full depth holds it, behind `chosen`. `depth()`'s `beyond` already subtracts this list: reuse.
  - `model_for()`: drop the `haiku` branch; `FIXED_MODELS`' comment says sonnet at both depths.
  - `UNTESTABLE_RE` (new regex), and in `loop_state()`: `stuck` (kept `(role, change)` pairs
    also kept in round N-1, N-1 ≥ `first`) and `untestable` (lines of `build/round-<last>.md`),
    both computed from round files only; `exhausted` widened by them before `read_decision()`;
    the `rework` branch skipped when either is set.
  - `_task()`: `review` adds the word-for-word sentence for an undone kept change; `approve` names
    the repeated changes or the untestable lines and asks for the next step under
    `## Reconsider the approach`.
  - `cmd_verdicts()`'s docstring: the two new fields.
- `plugins/factory/agents/reviewer-{code,security,test,behaviour,ui,ux}.md`: the "Later rounds"
  paragraph says to raise an undone kept change again word for word.
- `plugins/factory/agents/builder.md`: `- UNTESTABLE: <requirement>: <why>`, when it's for, and
  that it never replaces a test the builder chose not to write.
- `plugins/factory/agents/approver.md`: the early stop is a form of "the rounds ran out".
- `plugins/factory/README.md`: the model rule (sonnet for every scaled reviewer), the light depth's
  reviewers, the early stop, and a *Why these defaults* note with the evidence table (R6).
- `scripts/retro.py`: `_landing_catches()` beside `_review_sources()`, its result in the bugs
  block as `landing_catches`, and `_sources_text()` (via `render_report()`) printing
  `Landing catches: k of n factory-reviewed changes`.
- `tests/test_factory.py`: new tests R1–R5, R7, R9, R10; existing light/model/question tests
  updated to the new defaults.
- `tests/test_retro.py`: R8's test.
- `tests/test_bugs.py`: the empty bugs block now holds `landing_catches` (found by the gate).
- `plugins/factory/skills/build/SKILL.md`: its sentence on the light depth's reviewers and the
  models, which named haiku.
- `docs/REFERENCE.md`: `landing_catches` beside `review_sources` in the retro's bugs block.
- `read_decision()`'s refusal now says the run can't converge for any of the three reasons, not
  only that the rounds ran out.
- `scripts/retro.py` gains `import re` for `LANDING_CLASS_RE`.

As built, `stuck` and `untestable` come from one helper, `early_stop()`, which `loop_state()` calls
beside `exhausted`; no test in `tests/test_skills.py` needed a change.

## Evidence read (R6)

From each change's `Close` commit's first parent (`git show <sha>:.sdlc/work/<name>/…`), its
`runs/costs.jsonl` (role → model) and its reviews:

| Change | Tier | Depth | Build rounds | Reviewers (model) in the rounds | What the landing kept | Catchable in a build round by |
|---|---|---|---|---|---|---|
| 124 | 1 | light | 2 | code, ui, ux (haiku) | ui: heading outranks the drawer title; ux: unlabelled checkbox (land-2, both on haiku) | ui and ux, already there: the model, sonnet |
| 125 | 1 | light | 1 | code (haiku) | behaviour: "no gate configured" with no base branch read (haiku) | behaviour, absent from light: R1, on sonnet (R2) |
| 129 | 2 | light | 1 | code, test (sonnet) | test: no test for the nit rule the landing's rebase added | none: the code it named came with the rebase |
| 131 | 1 | light | 1 | code (haiku) | nothing kept; a red landing gate from a machine path (135) | none: not a review miss |

So: R1 (behaviour) answers 125, R2 (sonnet) answers 124, and nothing in 129 asks for `test` in a
Tier 1's light rounds, which stays out (the spec's rejected alternative holds).

## Work order

1. **R2 models.** Rewrite `test_each_role_runs_on_its_model`'s `("code", 1, "light")` case to
   `sonnet` and `test_the_ui_reviewers_scale_like_the_others` to set `haiku` explicitly; see them
   fail; drop the branch. Gate.
2. **R1 light reviewers.** New `test_a_light_round_includes_the_behaviour_reviewer` and
   `test_the_behaviour_reviewer_never_deepens_a_light_run`; update the existing light tests'
   expectations (`["code"]` → `["code", "behaviour"]`, Tier 2 `["code", "test", "behaviour"]` in
   `REVIEWERS` order: `code, test, behaviour`); change `light_reviewers()`. Then R10: update the
   build question test's parenthesis to `code and behaviour`. Gate.
3. **R9.** `test_a_host_s_own_depth_and_models_are_kept`: a factory.toml setting `rounds`,
   `[light] reviewers`/`rounds` and `[models]` gives exactly the values set in `start`'s output.
4. **R3 + R7 stuck.** `test_a_change_kept_twice_escalates_before_the_rounds_run_out` on a 3-round
   run; then `loop_state()`'s `stuck`; then the approve prompt test
   (`test_an_early_escalation_names_its_reason_to_the_approver`, stuck half) and `_task()`.
5. **R5 + R7 untestable.** `test_an_untestable_requirement_escalates_after_its_round`; then
   `UNTESTABLE_RE` and `untestable`; the approve prompt's untestable half; `builder.md`.
6. **R4.** `test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word`; `_task()`'s
   review branch; the six reviewer prompts.
7. **R8.** `test_retro_counts_a_landing_catch_once_per_change`; `_landing_catches()` and its line.
8. **R6.** README: rules, early stop, *Why these defaults* with the table above;
   `test_readme_names_the_light_reviewers_and_models` comparing the README's sentence with
   `light_reviewers()` and `model_for()` for a Tier 1 light run.
9. `./check.sh`.

## Tests

- R1: `test_a_light_round_includes_the_behaviour_reviewer`,
  `test_the_behaviour_reviewer_never_deepens_a_light_run`, `test_a_set_light_list_is_kept_at_either_tier`
  (existing, unchanged), `test_a_tier_2_light_round_includes_the_test_reviewer` (updated lists).
- R2: `test_each_role_runs_on_its_model` (rewritten case), `test_the_ui_reviewers_scale_like_the_others`.
- R3: `test_a_change_kept_twice_escalates_before_the_rounds_run_out` (also `READY` refused, and a
  restart between the two rounds doesn't count them as consecutive).
- R4: `test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word`.
- R5: `test_an_untestable_requirement_escalates_after_its_round`.
- R6: `test_readme_names_the_light_reviewers_and_models`.
- R7: `test_an_early_escalation_names_its_reason_to_the_approver`.
- R8: `test_retro_counts_a_landing_catch_once_per_change` (tests/test_retro.py).
- R9: `test_a_host_s_own_depth_and_models_are_kept`.
- R10: `test_the_build_question_names_the_base_branch_s_gate_and_light_depth` (updated).

## Rollback

`git revert` undoes all of it: the change writes no data, publishes nothing and adds no state
file. A run already under way when it lands picks up `behaviour` at its next `verdicts` (one more
agent run, no lost work); reverting mid-run likewise just drops it again. `stuck`/`untestable`
only widen `exhausted`, so a decision written under them (an ESCALATE with its section) still
reads after a revert.
