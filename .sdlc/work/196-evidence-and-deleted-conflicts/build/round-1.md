I've fixed both bugs and both nits and left them uncommitted for `/sdlc:ship`. I didn't run the whole suite after my last edits, so the gate's run is the first full check. Before the last restructuring, a run of the eight affected test files gave 798 passed and one failure, which I then fixed. 189's rerun and 194's landing are outcomes of the real runs and haven't been tried; the tests rebuild their cases (189's report, a train like 193 then 194).

## Slices built

1. **Evidence reads that print headings (bug 2026-11-20-17).** In `read_evidence()`, a `## ` line now ends the Evidence section only when no command is open (after its `exit:`). It also ends it after a blank line, unless the open command is a read that has already printed. Any other `## ` line counts as that command's output.
   - 189's report now reads clean, and the commands after its read are still checked.
   - The rule stays strict: a command that isn't a read still can't find its `exit:` under a later section. One existing test proved this and still passes.
2. **A file one side deleted, in a train (bug 2026-11-20-14).**
   - **The crash:** `resolve --continue` read every conflicted file, so a file the resolver deleted raised `FileNotFoundError`. It now skips a deleted file, and `git add` stages the deletion.
   - **The second stop:** with only the crash fixed, 194 would still have stopped. Its resolver had put 193's tests into `tests/test_factory_decisions.py`, a file outside the conflict, which `--continue` refuses.
   - **New `deleted_sides()` in `factory.py`:** it finds each such conflict with `git ls-files --unmerged`. It covers either way round: this change deleted the file, or the change it's stacked on did. It notes:
     - which side deleted the file;
     - where the surviving text is (`:2:` or `:3:`);
     - the `git diff` that shows what the other side changed;
     - the commit that did the deleting, and the files that commit added or changed (`moved`).
   - **What the resolver is told:** the `train-resolve` prompt gains a `## deleted` part listing all of that, and `agents/resolver.md` gains one rule for it.
   - **What `--continue` accepts:** edits to the `moved` files as well as the conflicted ones. It stages the edited ones and adds them to `runs/land-resolved`, so the landing review still sees them. An edit to any other file is still refused.
3. **The prompt fixture:** a new pinned prompt, `tests/prompts/train-resolve-deleted.txt`.
4. **The nits.**
   - 2026-11-20-8: an earlier decision is matched by its alternatives only when it has two or more options.
   - 2026-11-20-9: the threshold is now a named constant, `GREP_FOLLOWS_MIN = 3`, compared with the characters after `--`. Behaviour is unchanged.

To avoid giving 194 another conflict of the same kind, I put the new tests in new files or in files its split doesn't touch, never in `tests/test_factory.py`.

## Tests added and what they prove

- `tests/test_evidence_headings.py` (4 tests):
  - 189's report shape owes no `exit:`.
  - The commands after that read are still checked.
  - A heading after an `exit:` ends the section.
  - A read that printed nothing before a later section still owes its `exit:`.
- `tests/test_train.py`:
  - `test_a_modify_delete_conflict_reaches_the_resolver_and_lands[UD/DU]`: either way round, the conflict reaches the resolver with the deletion named. `--continue` takes the deletion and the carried edit, the marker names both files, and the train lands.
  - `test_a_modify_delete_resolution_outside_the_moved_files_is_refused`.
  - `_ready()` gained a `gone=` argument so a fixture can delete a file.
- `tests/test_prompts.py`: the new `train-resolve-deleted` case.
- `tests/test_decision_alternatives.py`: two decisions that share one option are filed as two.
- `checks.md`: two acceptance checks for the resolver's rule and the named threshold. Both pass under `sdlc.py accept`.

I saw each new test fail first, for the reason expected. One aside: when the moved file's content matched the deleted one exactly, git detected a rename and merged with no conflict at all. So the fixture makes the new file differ, as a split does.

## plan.md

Written first. After that I updated it twice:
- `deleted_sides()` moved from `landing.py` to `factory.py`, because `test_modules.py` requires a function the script calls to live in the script. It now reads stages with `git ls-files -u` rather than landing's status parser.
- The evidence rule now matches what was built.

## notes.md

- [ ] The builder's `resolve` task gets no `deleted` part. The landing loop only runs `train-resolve`, and the builder's resolve prompt says to run no git command. `--continue` accepts a deleted-file resolution from either task.

- DECISION: [default] How does the resolver say where a deleted file's content went? (the intent's open question) Going ahead with this: the script lists the files the deleting commit added or changed, the resolver picks among them, and only those files pass `--continue` beyond the conflict's own.
  - OPTION: the deleting commit's added or changed files, resolver's judgment — handles a split like 194's, and the edits stay fenced and are re-reviewed; the resolver may touch more files than the conflict lists
  - OPTION: only a rename git detects — tighter; a split is rarely detected, so 194 still couldn't land unattended
  - OPTION: the resolver names the destination in its reply — most flexible; the script can't check prose, which breaks the rule that the script decides what may change
  - WHY: the intent's outcome needs 194 to land unattended, and the constraint needs the script to decide which files may change.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_evidence_headings.py
FAILED tests/test_evidence_headings.py::test_a_read_printing_headings_owes_no_exit
FAILED tests/test_evidence_headings.py::test_the_commands_after_a_read_printing_headings_are_still_checked
2 failed, 2 passed in 0.56s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "modify_delete"
E       FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/.../host/.claude/worktrees/002-second/old.txt'
3 failed, 143 deselected in 10.49s
exit: 1

$ uv run --group dev pytest -q tests/test_decision_alternatives.py
E       AssertionError: assert [] == ['D2']
1 failed in 0.06s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_land.py tests/test_train.py tests/test_prompts.py tests/test_evidence_headings.py tests/test_decision_alternatives.py tests/test_modules.py tests/test_skills.py tests/test_windows.py
FAILED tests/test_modules.py::test_the_line_between_script_and_module_holds[landing]
1 failed, 798 passed, 1 skipped in 528.79s (0:08:48)
exit: 1

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_modules.py tests/test_prompts.py tests/test_evidence_headings.py tests/test_decision_alternatives.py tests/test_windows.py "tests/test_train.py::test_a_modify_delete_conflict_reaches_the_resolver_and_lands" "tests/test_train.py::test_a_modify_delete_resolution_outside_the_moved_files_is_refused" "tests/test_train.py::test_a_resolution_outside_its_files_is_refused" "tests/test_train.py::test_a_train_conflict_goes_to_the_resolver_with_every_change"
151 passed in 14.10s
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_land.py tests/test_train.py tests/test_resolve.py -k "resol or conflict or grep or read_only"
83 passed in 37.40s
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 196
  "passed": true,
  "problems": []
}
exit: 0
