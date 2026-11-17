I've built change 123 to the spec. Read-only commands that show their output no longer stop a passing check for a missing `exit:` line. The full gate passes with 2255 tests, and the work is uncommitted for `/sdlc:ship`.

**Plan.** `plan.md` is written: the files to change, four slices, which test proves each requirement, and rollback (a plain `git revert`; nothing is written outside the repo). The build matched it.

**Slices built**
1. **`is_read()` (R1).** A new function in `factory.py`, next to `EVIDENCE` and `EXIT_RE`, decides whether a command is a read. It takes no outside input and follows the spec's rules. Any command it can't fully see into, or that could write, counts as not a read. Two places are stricter than the spec, which errs strict as intended:
   - `awk` accepts only `-F` and `-v` as options.
   - `shlex` comments are turned off, so `a#b > c` can't hide a write.
2. **`read_evidence()` (R2, R3, R4, R6).** It now notes whether a command printed a line that isn't blank and isn't a fence. A missing `exit:` is reported only if the command is not a read that printed something. The problem message is unchanged, so no caller changed.
3. **Landing fixtures (R5, R7).** `NO_EXIT` now uses `$ uv run pytest -q` with output, so 109's tests still test a real missing exit. The build-mend test's fixture changed the same way, and 119's two replies are rebuilt as fixtures.
4. **Prompts and docs (R8).** `reviewer-behaviour.md` and `builder.md` still ask for `exit: <n>` on every command, but now say a missing one stops the run "unless it is a read that shows its output". The behaviour prompt no longer says "every `$` line gets its `exit:`". The factory README's *Shown, not said* and the factory paragraph in `AGENTS.md` now name `is_read()`.

**Tests added**
- **R1:** `test_a_read_is_only_what_the_script_can_tell_changes_nothing` checks the spec's 7 reads and 16 non-reads (portable).
- **R2:** `test_a_read_showing_its_output_needs_no_exit`, plain and fenced (portable).
- **R3:** `test_a_silent_read_still_needs_its_exit`: a `cmp` with no output before the next `$`, or with only a blank line inside a fence, still needs its exit (portable). This already held before the change and still does.
- **R4:** a new case for `uv run pytest -q | grep passed` in the existing parametrized test, with output and no exit; it still stops. This also already held and still does.
- **R5:** `test_119s_landing_replies_pass`. I checked that with `is_read` forced to `False`, both replies are reported as missing an exit.
- **R6:** `test_a_builders_read_needs_no_exit`: the builder's report goes on to `review`.
- **R7:** `test_no_exit_is_not_a_read`, so `NO_EXIT` can't quietly become a read again (portable).
- **R8:** a new assert in `test_what_runs_the_change_shows_its_evidence_and_never_runs_checks`.

R1, R2, R6 and R8 failed before their code was written. 109's two landing mend tests failed when `read_evidence()` changed, because the old `NO_EXIT` was a `head` command, which now passes; slice 3 fixed that.

**Gate.** `./check.sh` is green: ruff is clean, 2255 passed and 13 skipped, and `claude plugin validate --strict` passed. The portable run had 341 passed. In the spec's by-hand check, 119's two fixtures give no problems, and the same fixtures with `$ uv run pytest -q` swapped in each give one "has no `exit:` line" problem.

**`notes.md`** has two unticked items:
- `file -C` can write a magic file, yet `file` is on the spec's plain-read list.
- A file-descriptor digit before a redirection (the `2` in `2>&1`) is kept as an argument of its command. It can't make a non-read pass, but any rule that counts a program's arguments would see one more.

No decisions raised this round.

## Evidence

$ ./check.sh > /tmp/gate123.log 2>&1; echo "exit: $?"; grep -E "passed|failed|All checks|already formatted" /tmp/gate123.log | grep -v warning
exit: 0
All checks passed!
250 files already formatted
2255 passed, 13 skipped in 57.19s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable
341 passed, 13 skipped, 1914 deselected in 57.88s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k changes_nothing   (before is_read existed)
E       AttributeError: module 'factory_under_test' has no attribute 'is_read'
1 failed, 211 deselected in 0.64s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "needs_no_exit or silent_read or without_its_evidence"   (before read_evidence changed)
FAILED tests/test_factory.py::test_a_read_showing_its_output_needs_no_exit - ...
FAILED tests/test_factory.py::test_a_builders_read_needs_no_exit - AssertionE...
2 failed, 6 passed, 208 deselected in 16.89s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k never_runs_checks   (before the prompt edits)
1 failed, 352 deselected in 0.13s
exit: 1

$ uv run --group dev python /tmp/r5check.py   (R5 fixtures, now and with is_read forced False)
now: [] []
without is_read: ['r: `grep -n "^VERDICT" … ; cmp …` has no `exit:` line'] ['r: `cat .sdlc/work/119-ui-review-folders/plan.md` has no `exit:` line']
exit: 0

$ uv run --group dev python /tmp/r5hand.py   (spec's by-hand check: fixtures, then with `uv run pytest -q` swapped in)
[] ['r: `uv run pytest -q` has no `exit:` line']
[] ['r: `uv run pytest -q` has no `exit:` line']
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
