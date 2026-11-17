I built change 125 and left it uncommitted for you to review at `/sdlc:ship`. `factory.py start --for build` now prints the build gate's `question`, worded by the script, and the build skill's Step 1 opens with the change's own words before the run's machinery. The full gate passes: 2350 passed, 13 skipped, exit 0.

## What was built

1. **The question in its plain form.** A new `build_question(start, check, sensitive)` in `factory.py` sits next to `land_question()`. It takes values and reads nothing itself. `cmd_start` sets `question` from it for a build run with no refusals, and sets it to `null` otherwise. The question uses the base branch's `[commands] check` and `[review] sensitive`, read the way `depth()` and `gate` read them, so the change's own copy of the config is ignored.
2. **The clauses.** The gate clause names the command, or reads `, with no gate configured` when there is none. The light-depth bracket appears only when there is a sensitive list. The UI clause appears only when `[ui]` sets `serve`, `shoot` and `paths`. A small helper, `_listed()`, joins reviewer names as a sentence and says `no reviewer` for an empty list, which the config allows.
3. **All four forms.** No spec draft, a spec draft, a restart and an upgraded run (the intent named three; the skill actually held four). Each test compares the whole sentence, word for word, with the template the skill used to hold.
4. **The skill.** Step 0 now mentions `question`. Step 1 opens with the intent quoted, never summarised: title, Problem and Outcome, plus Approach for a Tier 1, or just the title for a restart or upgraded run. Step 2 asks `start`'s `question` exactly as printed. The restart and upgraded templates and the "leave out…" rules are gone.

## Tests added
- **`tests/test_factory.py`:** 15 new test runs (some tests run several cases). They cover:
  - each of the four forms, compared in full
  - the gate clause, checked against the base branch's config even after the change's own copy is edited
  - the light-depth bracket
  - the UI clause, with all three settings present and with each one missing
  - `question` being `null` for a refused run, for `--for spec`, and for a change with no worktree of its own
  - `_listed()`

  All but one failed first, on the missing `question` key or the empty-list case. The no-worktree check was added after the fix, so I never saw it fail.
- **`tests/test_skills.py`:** two existing tests pinned the old template sentences and leave-out rules. They now check that Step 2 asks `start`'s `question` and that the script holds the no-gate wording.
- **`checks.md`:** two acceptance checks, one that Step 1 opens with the quoted intent and one that Step 2 asks the script's question with the hand-filled forms gone. Both pass now, and both fail against the old skill text.

## `plan.md` and `notes.md`
`plan.md` was written before any code. One update since: the skill still shows the question's fullest plain form as a reference, because the skill tests require every gate step to show a question with its answers, the same way `land` does. The test-file change and `_listed()` are also recorded there.

Two items are left unticked in `notes.md`:
- `/sdlc-factory:spec`'s gate question is still worded in the skill. Its only placeholder is the folder name, so I left it out of scope.
- The script writes `1 round` where the old template would have read `1 rounds`. Only a repo with a round limit of 1 would see it.

The commit is unchanged at `6d8905f`.

- DECISION: [default] Show all of Problem and Outcome, with no length cap or pointer to the file? Options: in full; up to a length with a pointer. Going ahead with in full: the intent says quote it, never summarise it, and cutting it short would be a summary.
- DECISION: [default] For a restart or an upgraded run, show only the intent's title? Options: title only; title, Problem and Outcome. Going ahead with title only: the approver's reasons or the spec draft that follow already say what the change is for.
- DECISION: [default] Keep the question's fullest plain form in Step 2 as a reference, as `land`'s Step 2 does, instead of removing every template sentence? Options: keep the one reference form; remove all forms and loosen `test_every_gate_offers_two_to_four_answers` for this skill. Going ahead with keeping it: the skill tells the model to ask the script's question as printed, and the only form a model filled in by hand that remains is this reference.
- DECISION: [default] Leave `/sdlc-factory:spec`'s gate question as it is in this change? Options: leave it; move it to the script too. Going ahead with leaving it: its only placeholder is the folder name, and it is noted in `notes.md`.

## Evidence

$ uv run --group dev pytest tests/test_factory.py -q -k "build_question"   (before the code)
10 failed, 253 deselected in 7.12s   (KeyError: 'question')
exit: 1

$ uv run --group dev pytest tests/test_factory.py -q -k "lists_reviewers"   (before the empty-list guard)
1 failed, 3 passed, 263 deselected in 0.29s
exit: 1

$ uv run --group dev pytest tests/test_skills.py tests/test_factory.py -q -n auto
621 passed in 8.49s
exit: 0

$ sh -c "<checks.md block 1>"; sh -c "<checks.md block 2>"   (from the worktree root)
check 1 exit: 0
check 2 exit: 0
exit: 0

$ (the same two blocks, run against `git show HEAD:plugins/factory/skills/build/SKILL.md` in a scratch dir)
old check 1 exit: 1
old check 2 exit: 1
exit: 1

$ ./check.sh
All checks passed!
2350 passed, 13 skipped in 54.42s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0

$ git rev-parse --short HEAD
6d8905f
exit: 0
