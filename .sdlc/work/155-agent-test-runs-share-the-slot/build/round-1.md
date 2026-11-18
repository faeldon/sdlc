I've built 155: there's a new `factory.py check <NNN>` command, the agents' prompts send their full test runs through it, and metrics count it as a test run. Nothing is committed. The full gate passed: 2867 passed, 28 skipped, ruff clean, `claude plugin validate --strict` passed. I ran it through the new `factory.py check 155` instead of a bare `./check.sh`, so that run also tried the command by hand.

**Slices built**
1. **`check` runs the base branch's command (R1, R2, R5).**
   - `cmd_check()` runs the base branch's `[commands] check` in the change's worktree. Output goes straight through and the exit code is the command's. It writes nothing.
   - It refuses with `gate`'s wording when there's no base branch, no check, or no such change.
   - `gate` and `check` both start the command through one new function, `_run_check()`. `gate`'s capture, timeout and record are unchanged.
2. **`check` holds a gate slot and frees it however it ends (R3, R4).** It uses the same `gate_slot()` locks as the gate. Past `GATE_TIMEOUT` it kills the command, says `timed out after <n>s` and exits 1.
3. **The prompts name the command (R6).** `check_line()` gives the full command, `uv run --quiet --script <this factory.py> check <NNN>`. Every builder prompt gets it (build, fix, rework, restart, upgrade, decided, mend), and so does the resolver's `train-resolve` prompt. No reviewer, verifier or approver prompt does.
4. **Metrics count it (R11).** `FACTORY_CHECK_RE` sits next to `HAND_GATE_RE` in both places that regex is matched. `land-check` and `gate` don't count.
5. **Evidence citing the gate record (R10).** This was a test only: `is_read()` already accepted `cat` or `head` of the record, so that test passed the first time I ran it.
6. **Agent instructions (R7–R9).**
   - `builder.md`: each slice runs its own tests by name, the gate covers the whole suite, a full run goes through `check`, and the Evidence example is a named test run.
   - The three reviewer files: the gate record is the whole suite's result, never run the suite another way, run only the named tests a finding rests on. The behaviour check still runs the end-to-end path.
   - `resolver.md`: run the tests the conflict touched, by name, and use `check` for a full run.
7. **Docs (R12).** The factory README covers `check` in the slot paragraph, in a new bullet and in the Mechanism list. I edited the factory sentence in `AGENTS.md` as the spec's Contracts touched section words it, and the docstring names `check`. `checks.md` has one check that greps for the README line.

**Tests added**
- In `tests/test_factory.py`:
  - R1: base branch's command, its exit code.
  - R2: each refusal, nothing run.
  - R3: two checks with one slot never overlap and one says it waited; a check waits for a slot the gate holds.
  - R4: killing `check` frees its slot within 2 s; the timeout.
  - R5: a green check writes nothing and `verdicts` still says `gate`.
  - R6: which prompts name the command.
  - R10: evidence citing the gate record.
- R6 for the resolver: an added assertion in `tests/test_train.py`.
- R11: four rows in `tests/test_metrics.py`.
- R7–R9: three tests in `tests/test_skills.py`.
- Two existing tests checked the end of a builder prompt with `endswith`. Their expected endings now include the check line.

**plan.md:** written before the code. It records two differences from the spec: the R10 test sits in `tests/test_factory.py`, and the builder's landing prompts also name `check`.

**notes.md:** nothing left.

- UNTESTABLE: none.
- DECISION: [default] Also name the `check` command in the builder's landing prompts (`resolve`, `land-fix`), not only in the ones R6 lists? Going ahead with yes.
  - OPTION: yes — the builder is told the same thing every time it's resumed, and `builder.md` refers to "the `check` command your prompt names"; the downside is going past R6's list
  - OPTION: no — exactly R6's list; while landing, the builder has no slotted full run to use
  - WHY: R6 says "every prompt `_task()` sends the builder", and `_task()` sends these two through `_land_task()`.
- DECISION: [default] Put R10's test in `tests/test_factory.py` beside the other `read_evidence()` tests, not in `tests/test_evidence.py`? Going ahead with `tests/test_factory.py`.
  - OPTION: `tests/test_factory.py` — that's where the parser's tests already live; the downside is not matching what the spec names
  - OPTION: `tests/test_evidence.py` — what the spec names, but that file tests the retro's `.sdlc/evidence.py` and doesn't load `factory.py`
  - WHY: the spec named the wrong file.

## Evidence

$ uv run --quiet --script plugins/factory/scripts/factory.py check 155 > /tmp/claude-155-check.log 2>&1
exit: 0

$ grep -E "passed|failed|waiting|All checks|files already" /tmp/claude-155-check.log
All checks passed!
284 files already formatted
2867 passed, 28 skipped in 283.23s (0:04:43)
✔ Validation passed
✔ Validation passed

$ set -o pipefail; uv run --group dev pytest -q tests/test_factory.py tests/test_metrics.py tests/test_skills.py tests/test_train.py -k "check or builders_prompts or gate_record or known_by_its_program or whole_suite or conflicts_tests or resolver_with_every or cheap_nits or persons_words or killed_gate or hand_gates_slot" 2>&1 | tail -1
67 passed, 904 deselected in 39.65s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_train.py tests/test_land.py 2>&1 | tail -15
FAILED tests/test_factory.py::test_rework_hands_the_builder_its_cheap_nits - ...
FAILED tests/test_factory.py::test_the_restart_prompt_carries_the_persons_words
2 failed, 480 passed in 107.05s (0:01:47)
exit: 1

(The two `endswith` tests above, before I extended their expected endings; both pass in the targeted run and the gate.)

$ sh -c "$(sed -n '/^```sh$/,/^```$/p' .sdlc/work/155-agent-test-runs-share-the-slot/checks.md | sed '1d;$d')"
exit: 0

$ uv run --group dev ruff check . --output-format concise
All checks passed!
exit: 0
