DECISION: READY

**Why.** All nine nits are dealt with: seven are fixed and two are retired, each with a reason both reviewers checked. Round 1 is `VERDICT: PASS` from both the code and behaviour reviewers. The builder's `./check.sh` passed (2549 passed, 18 skipped) and the round-1 gate is green. Nothing changes behaviour: the edits are reflows, docstrings, a test rename, one skill sentence and stronger test assertions. Nothing suggests the intent was wrong. The only things left are minor and written down: three unticked items in `notes.md` and one recorded nit.

**Open items**
- No CHANGE is unresolved.
- F1 is recorded but still open, raised by the code reviewer: the new "unverified" case in `tests/test_factory.py` checks only `stuck == []`. It could also check `next == "rework"`, as the cases next to it do. This is minor and not blocking.

**Decisions to confirm**
- None. No `decisions.md` exists, no blocking line is unticked, and the prompt names no open defaults.

**For the person at ship**
1. **The `REASK` constant** in `test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word`, and the new missing-`verified.md` case in `test_a_change_kept_twice_escalates_before_the_rounds_run_out`. These are the only test logic that changed. The builder says the new case fails if the `and prev["verified"]` guard is removed, but it fails with a `TypeError` rather than an assertion. It still covers that branch.
2. **The `approve` bullet in `plugins/factory/skills/build/SKILL.md`.** It now says `exhausted` also covers a `stuck` or `untestable` stop. Check this matches what `factory.py` tells the approver.
3. **The `AGENTS.md` and triage reflows.** These should be quick: the builder's word-by-word diff against `HEAD` shows the wording is unchanged.
4. **`tests/test_archive.py`.** This file isn't in the intent's Affected list. Only a docstring changed there, and `plan.md` explains why.

**Release impact**
- IMPACT: patch — the build skill's wording and the shipped `AGENTS.md` and triage text read better, and nobody holding the last release has to do anything differently or gains a new ability.

**Undone items**
- UNDONE: `AGENTS.md` has other lines past 100 columns (12, 29, 34, the *Writes before a WAIT* paragraph at 109-110, 223, 232-233, 238, 255, 276, 314), outside 2026-11-18-25's scope. → seed: Reflow AGENTS.md's remaining lines past 100 columns
- UNDONE: `tests/test_factory.py`'s `test_a_server_that_fails_on_its_own_is_started_once` docstring cites "111 C1", another review-only label no reader can resolve. → seed: Replace the "111 C1" review label in test_a_server_that_fails_on_its_own_is_started_once with the rule it pins
- UNDONE: `plugins/factory/agents/reviewer-code.md:94` and `reviewer-ux.md:67`, the `supersedes` sentence, are single long lines. → seed: Wrap the supersedes sentence in reviewer-code.md and reviewer-ux.md

**How to recover**
- The prompt names no irreversible paths. `plan.md`'s Rollback is a `git revert`, and nothing is written outside the repo.
