---
id: 142
slug: pay-down-todays-nits
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 142 — Pay down the nits today's landings left · plan

> Written after reading each nit's site: the line numbers the entries cite have moved since they
> were filed, so each is located by its text.

## Files to change

- `AGENTS.md`: reflow the *Closing* paragraph's long lines (the `_close_commit()` sentence) and
  *The register* paragraph's long line (`ship` refuses … `drop` a held entry), wording unchanged
  (2026-11-18-25).
- `skills/triage/SKILL.md`: the Step 6 paragraph is now line 220, one 168-character line; rewrap it
  near 100 (2026-11-18-29).
- `scripts/sdlc.py`: nothing. The `out["dangling"]` comprehension landed without its
  `# fmt: skip` (138's final diff has none), so 2026-11-18-28 is already done: retired with that
  reason.
- `tests/test_board.py`: `test_an_empty_file_says_so`'s "(138 C2)" becomes the rule it pins
  (2026-11-18-30).
- `tests/test_archive.py`: the same nit's other label, "138 C1", is here, in
  `test_intake_never_says_nothing_waits_when_it_can_t_read_the_unpushed_commits`; say the rule
  (2026-11-18-30). Not in the intent's Affected list; a docstring only.
- `tests/test_factory.py`:
  - rename `test_no_build_question_for_a_refusal_or_a_spec` to
    `test_no_build_question_for_a_refusal_or_a_tier_1_spec` (2026-11-18-31);
  - in `test_a_change_kept_twice_escalates_before_the_rounds_run_out`, a case where round 1 has
    no `verified.md`: round 2 keeping the same change is then not `stuck` (2026-11-18-37);
  - in `test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word`, assert every
    reviewer's `## Later rounds` holds the same re-raise sentence, not just "word for word"
    (2026-11-18-35);
  - in `test_readme_names_the_light_reviewers_and_models`, a comment that the README's table of
    changes 124, 125, 129 and 131 is checked by hand against each one's `Close` commit
    (2026-11-18-36, retired as not testable).
- `plugins/factory/skills/build/SKILL.md`: the `approve` bullet's `exhausted` sentence gains that
  it is also set by a `stuck` or `untestable` stop, and the approver is told which
  (2026-11-18-34).
- `plugins/factory/agents/reviewer-ux.md`: read against the other five, its re-raise sentence
  already matches word for word once the wrap is ignored; no edit. The test above pins it, which
  is what retires 2026-11-18-35.

## Work order

1. Tests first: the no-`verified.md` case, the shared re-raise sentence, the rename, the R6
   comment. Run them; the R3 case is mutation-checked by dropping `and prev["verified"]` from
   `early_stop()` for one run, and the sentence check against a temporarily altered copy.
2. Docstrings in `tests/test_board.py` and `tests/test_archive.py`.
3. Prose: `AGENTS.md`, `skills/triage/SKILL.md`, the factory's build skill.
4. `./check.sh`.

## Tests

- 2026-11-18-37: the new case in `test_a_change_kept_twice_escalates_before_the_rounds_run_out`.
- 2026-11-18-35: the strengthened assertion in
  `test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word`.
- 2026-11-18-31: the renamed test still passes.
- The rest are prose and docstrings; `./check.sh` (ruff, the skills' tests) covers them.

## Rollback

`git revert` undoes all of it; nothing is written outside the repo.
