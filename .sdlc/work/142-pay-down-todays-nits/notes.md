# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## How each nit was paid

- 2026-11-18-25: *Closing* and *The register* reflowed at 100 columns, wording unchanged.
- 2026-11-18-28: retired, already done: the `out["dangling"]` comprehension landed in 138 without
  a `# fmt: skip` (138's diff to `scripts/sdlc.py` has none), so there is nothing to remove.
- 2026-11-18-29: triage's Step 6 rewrapped, wording unchanged.
- 2026-11-18-30: the "138 C2" label dropped from `tests/test_board.py`, and the other one, "138 C1",
  which is in `tests/test_archive.py`, dropped too. Each docstring already states its rule.
- 2026-11-18-31: renamed to `test_no_build_question_for_a_refusal_or_a_tier_1_spec`.
- 2026-11-18-34: the build skill's `approve` bullet says `exhausted` also covers a `stuck` or
  `untestable` stop, and that the approver is told which.
- 2026-11-18-35: `reviewer-ux.md`'s sentence already matched the other five word for word; the
  difference in diff size was only the wrap. It needed no edit; the test now asserts the whole
  sentence in every reviewer instead of the words "word for word".
- 2026-11-18-36: retired as not testable, with a comment in
  `test_readme_names_the_light_reviewers_and_models`.
- 2026-11-18-37: the missing-`verified.md` case added to
  `test_a_change_kept_twice_escalates_before_the_rounds_run_out`.

## Left undone

- [x] `AGENTS.md` has other lines past 100 columns (12, 29, 34, the *Writes before a WAIT* → seed: 2026-11-18-53
  paragraph at 109-110, 223, 232-233, 238, 255, 276, 314), outside 2026-11-18-25's scope.
- [x] `tests/test_factory.py`'s `test_a_server_that_fails_on_its_own_is_started_once` docstring → seed: 2026-11-18-54
  cites "111 C1", another review-only label no reader can resolve.
- [x] `plugins/factory/agents/reviewer-code.md:94` and `reviewer-ux.md:67`, the `supersedes` → seed: 2026-11-18-55
  sentence, are single long lines.
