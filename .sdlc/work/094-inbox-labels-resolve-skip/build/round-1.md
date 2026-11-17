All three fixes are built and uncommitted, and the gate passes: `./check.sh` ran 1906 tests with exit 0. `HEAD` is still `95a03ee`. Three calls are left for you, listed under Decisions; one of them departs from what Outcome 3 says.

I wrote a `plan.md` even though this is Tier 1, because the change touches more than a couple of files.

## Slices

1. **`inbox-commit` names only the entries that changed** (bug 2026-11-17-17). A new `_as_written()` in `scripts/sdlc.py` drops the resolved `after` key before an entry is compared. The `After:` line as written still sits in `fields`, so a real edit to it is still an `Update`. Both comparisons use it: the one in the main checkout and the one from a worktree. `parse_entries()` is unchanged.
   - Test: `test_inbox_commit_retires_an_entry_another_waits_on`. It failed first with `Retire 2026-10-01-1; Update 2026-10-02-1`.
   - It proves the subject and `entries` are `Retire` alone, and that editing the `After:` line is still an `Update`.
   - Open question 1: whitespace behaves as before, since the comparison is still on the parsed lines, which are stripped.

2. **`resolve --continue` skips a step a resolved conflict left empty** (nit 2026-11-17-11). A new `_go_on()` replaces both `git rebase --continue` calls. It runs `git rebase --skip` only when git won't go on, nothing is unmerged, and both the index and the tracked files match `HEAD`. So a step that still holds something is never skipped.
   - Git's default rebase backend already drops such a commit on its own. Only the `apply` backend answers "No changes", which is the stop the nit describes, so the test sets `rebase.backend=apply`.
   - Test: `test_resolve_skips_a_commit_the_base_already_holds`. It failed first with "the rebase won't go on".
   - It proves the emptied commit is skipped, the branch's next commit is kept, and the aside commit is still undone, with the work uncommitted again.

3. **A reviewer's preamble can be mended once** (bug 2026-11-17-18). The changes are in `factory.py`:
   - `preamble()` finds a reply whose verdict comes on a later line.
   - In `loop_state()`, such a reply in the last round counts as mendable, alongside a missing `## Evidence`. `verdicts` gains a `mend` key listing the roles to ask again.
   - `agent --task mend --role <reviewer>` resumes that reviewer's last session with a new prompt (`VERDICT_MEND`) and writes its reply over the old one.
   - The first-line rule and the problem's wording are unchanged, and so is every copy of the parsing elsewhere.
   - I also updated the `WAYS["mend"]` sentence, the `verdicts` docstring, the build skill's `stop` step and the factory paragraph in AGENTS.md.
   - Test: `test_a_reviewer_s_preamble_is_mended_by_the_same_reviewer`. It failed first with `KeyError: 'mend'`.
   - It drives a preamble reply through the stop and the mend, then checks `verdicts` moves on to `approve`. It also checks a mend is refused when the reply already opens with its verdict.
   - `test_skills.py` pinned the old sentence of the `stop` step; I updated it to the new wording, which keeps the same rule.

"Once" is enforced by the build skill, as it already is for the evidence mend. The script keeps no count, so a second preamble reply still reads as mendable, and the skill's rule is what stops the run.

## plan.md and notes.md
- I updated `plan.md` to match what was built: the actual test names, the `test_skills.py` edit, and where "once" is enforced.
- Nothing is left in `notes.md`.

## Decisions

- DECISION: [default] Should a reviewer reply with no `VERDICT:` line anywhere also be mendable, or only one that has its verdict after a preamble? Options: preamble only; any reply without a first-line verdict. Going ahead with preamble only: that is the bug's case, and the existing test (`test_a_stop_names_its_way`) keeps a reply with no verdict at all as `rerun`.
- DECISION: [default] Should the mend also cover a verifier's or approver's reply that doesn't open with its line? Options: reviewers only; all three. Going ahead with reviewers only: the bug is about reviewers, and a malformed decision still stops as before.
- DECISION: [default] If the aside commit itself comes out empty (all the uncommitted work is already on the base), skip it or undo it? Options: skip it; commit it empty and then undo it. Going ahead with skipping it: the result is the same (nothing left to put back) and nothing extra is recorded. This departs from Outcome 3's literal "never skipped", which I read as being about an aside commit that holds work. That case is still undone, and the test checks it.

## Evidence

$ uv run --group dev pytest -q tests/test_bugs.py -k another_waits_on (before the fix)
E         + Retire 2026-10-01-1; Update 2026-10-02-1
1 failed, 52 deselected in 6.32s
exit: 1

$ uv run --group dev pytest -q tests/test_sdlc.py -k already_holds (before the fix)
E       AssertionError: the rebase won't go on: int: "git add/rm <conflicted_files>", then run "git rebase --continue".
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k preamble (before the fix)
E       KeyError: 'mend'
1 failed, 137 deselected in 0.24s
exit: 1

$ uv run --group dev pytest -q tests/test_bugs.py::test_inbox_commit_retires_an_entry_another_waits_on tests/test_sdlc.py::test_resolve_skips_a_commit_the_base_already_holds tests/test_factory.py::test_a_reviewer_s_preamble_is_mended_by_the_same_reviewer tests/test_factory.py::test_a_stop_names_its_way tests/test_skills.py::test_what_runs_the_change_shows_its_evidence_and_never_runs_checks
5 passed in 5.70s
exit: 0

$ ./check.sh
All checks passed!
190 files already formatted
1906 passed in 70.22s (0:01:10)
✔ Validation passed
✔ Validation passed
exit: 0

$ git rev-parse --short HEAD
95a03ee
exit: 0
