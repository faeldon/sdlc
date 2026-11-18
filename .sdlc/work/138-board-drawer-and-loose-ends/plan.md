# 138 — Plan

> How the intent's Approach is built, written after reading the code: the files it touches, the
> order of the slices, the test or check that proves each outcome, and what a revert leaves.

## Files to change

- `scripts/board.html`: `show()` (`let asking`, a counter it bumps per request, set only when its
  own request is still the newest) and `openDrawer()`'s empty-folder branch (bumps it too, so a
  late response from the last change never paints over "This folder holds no file yet."); and
  `paint()`: a file whose text is `""`, or only whitespace (round 1), shows "This file is empty."
  in the `pre`, and the Raw toggle hides for it, as there is nothing raw to show.
- `tests/test_board.py`: a node harness that runs the page's `h()`, markdown section, drawer
  state, `paint()` and `show()` over the stand-in DOM (`_FAKE_DOM`, given `replaceChildren` and
  `children`), with a `fetch` the test resolves in its own order.
- `plugins/factory/scripts/factory.py`: `spec_question(root, change)` beside `build_question()`, set by
  `cmd_start()` as `question` for `--for spec` with no refusals; `FINDINGS_HEAD` names the landing.
- `plugins/factory/skills/spec/SKILL.md`: Step 2 asks `start`'s `question` literally, as the build
  skill does, and still shows its form as a labelled sample (the dialog tests read it).
- Round 3 (R1, answering D4): the spec question's answers are `yes / revise a requirement`, the
  "rethink the design" option removed from `spec_question()`, the factory spec skill's sample and
  `skills/spec/SKILL.md`'s Step 4 question alike, since nothing said what it did.
- `tests/test_factory.py`: the spec question's test; `test_no_build_question_for_a_refusal_or_a_spec`
  no longer says the spec skill asks its own.
- `templates/findings.md`: the note names the landing beside `carry`; then `sdlc.py record`.
- `skills/triage/SKILL.md`: the `dangling` bullet.
- `scripts/sdlc.py`'s `cmd_intake()` (a departure from the Approach's half sentence): each
  `dangling` issue carries `waits_on_push`, true when a commit the base branch hasn't pushed
  closes it (`unpushed_closes()`, 128's reader), since the skill otherwise can't tell which one
  waits; when those commits can't be read, each is `null` and `dangling_unread` says why, so
  triage offers none on a guess (round 1). `docs/REFERENCE.md` says so. Tested in
  `tests/test_archive.py`. Triage's Step 6 names each issue waiting on the push.
- `.sdlc/work/138-board-drawer-and-loose-ends/checks.md`: the two wording-only outcomes.

Reused: `_FAKE_DOM`, `_nodes()`, `_text()`, `needs_node`, `_page_parts()`; `_run()` and `_change()`
in the factory tests; `test_findings_head_is_the_template` as the pin.

## Work order

1. **The stale response.** Red: the harness asks `a.md` then `b.md`, resolves `b.md` first, then
   `a.md`; `doc` must hold `b.md`. Green: the counter in `show()`.
2. **The empty file.** Red: an `intent.md` whose text is `""` draws a pane holding
   "This file is empty."; Green: `paint()`.
3. **The spec question.** Red: `start … spec` on a Tier 2 at `plan` prints the question with the
   folder's name, and none with a refusal. Green: `spec_question()`, the skill's Step 2.
   Round 3: Red: the test expects `(yes / revise a requirement)`; Green: drop the option from
   `spec_question()` and both skills' questions; check.
4. **The findings note**, template and `FINDINGS_HEAD` together; `sdlc.py record`; check.
5. **Triage's bullet.** Red: intake's `dangling` entry for an issue a closed, unpushed change
   closes says `waits_on_push: true`, and false once the tracking ref holds it. Green: the flag
   in `cmd_intake()`; then the bullet; check.

## Tests

- Outcome 1 (newer file shown): `test_a_stale_response_never_paints_over_the_newer_file`.
- Outcome 2 (empty note): `test_an_empty_file_says_so`, whitespace-only files included.
- Outcome 3 (spec question): `test_start_words_the_spec_question`, and the refusal assertion in
  `test_no_build_question_for_a_refusal_or_a_spec`; R1 by the same test and the check "Neither
  spec gate offers "rethink the design"".
- Outcome 4: `test_findings_head_is_the_template` (pin), `drift` via the gate, and the check
  "The findings note names the landing".
- Outcome 5: `test_intake_says_a_dangling_issue_an_unpushed_commit_closes_waits_on_the_push`,
  `test_intake_never_says_nothing_waits_when_it_can_t_read_the_unpushed_commits`,
  and the check "Triage's dangling bullet waits on the push".

## Rollback

Nothing outside the repo: `git revert` undoes all of it. A revert of the template's note also
needs `sdlc.py record` rerun, or the gate's `drift` check fails.
