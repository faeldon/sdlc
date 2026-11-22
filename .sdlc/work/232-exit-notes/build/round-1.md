Change 232 is built and left uncommitted for `/sdlc:ship`. A behaviour reply with `exit: 2 (hook refusal; the command did not run)` no longer stops its run, and `exit: nonzero` still does. The tests for the change pass (758 across four files) and lint is clean. The whole suite is left to the gate.

## Slices built
1. **The parser.** `EXIT_RE` in `plugins/factory/scripts/factory.py` is now `^\s*exit:\s*\d+(?:\s.*)?$`: a number, then an optional note after a space. This is a little stricter than the intent's `\d+\b.*`, which would also have read `exit: 2.5` or `exit: 2(x)` as code 2. `read_evidence()` and `is_read()` are unchanged.
2. **The prompts.** `agents/reviewer-behaviour.md` and `agents/builder.md` now say two things in their *Evidence* paragraph:
   - Every command that ran ends `; echo "exit: $?"` and records the number, never a word.
   - A command a hook refused never ran, so it gets no `$ ` line. The reviewer lists it under `## Notes` with the hook's message; the builder says so in its report. The pinned phrase "every command, reads included" is unchanged.

## Tests added
- `tests/test_factory_depth.py::test_an_exit_with_a_note_after_its_code_is_an_exit` (6 cases) runs `verdicts` on a behaviour reply:
  - `exit: 2 (hook refusal; …)`, `exit: 0 # ok` and `exit: 1` raise no problem.
  - `exit: nonzero (task failed)`, `exit: not run (blocked by the guard hook)` and `exit: 2x` still say the exit is missing and stop the run.
  - Before the fix, the two noted exits failed for that reason: "has no `exit:` line".
- `checks.md` has one acceptance check that both prompts carry the hook-refusal and real-code sentences. It passes on the change and fails on the old `builder.md`.

## plan.md
I wrote one because four files are touched. It explains why the regex differs from the intent, and why the reviewer is pointed at `## Notes` rather than a *Not run* section.

## notes.md
- [ ] `scripts/sdlc.py`'s `EVIDENCE_EXIT_RE` (ship's own behaviour check in `findings.md`) is still strict in the same way. That is outside this change's scope and is left for a change of its own.

## Decisions
- DECISION: [default] Should a hook-refused command go under the behaviour reviewer's `## Notes` rather than a new *Not run* section? Going ahead with `## Notes` unless told otherwise.
  - OPTION: `## Notes` — that prompt already sends "anything you couldn't run and why" there; the script doesn't read it
  - OPTION: a new `## Not run` section — easier to scan; one more heading in the prompt, which nothing reads
  - WHY: the prompt already has a home for commands that didn't run
- DECISION: [default] The intent's open question: should `exit: blocked` count as "refused by a hook"? Going ahead with no: listing it outside the evidence is enough.
  - OPTION: no — the evidence still always needs a code; a refused command is never presented as a result
  - OPTION: read `exit: blocked` — fewer stopped runs; a word becomes something the script accepts as evidence, which the intent's constraint rules out
  - WHY: the intent's constraint that an `exit:` with no number still fails

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_factory_depth.py -k exit_with_a_note   (before the regex change)
FAILED …[exit: 2 (hook refusal; the command did not run)-False]
FAILED …[exit: 0 # ok-False]
2 failed, 4 passed, 58 deselected in 4.45s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_depth.py -k exit_with_a_note
6 passed, 58 deselected in 3.83s
exit: 0

$ sh -c "$(sed -n '/^```sh$/,/^```$/p' .sdlc/work/232-exit-notes/checks.md | sed '1d;$d')"; echo "exit: $?"
exit: 0

$ git show HEAD:plugins/factory/agents/builder.md | tr '\n' ' ' | grep -q 'A command a hook refused never ran, so it is no `\$ ` line'; echo "exit: $?"
exit: 1

$ uv run --group dev pytest -q tests/test_factory_depth.py tests/test_land.py tests/test_skills.py tests/test_factory_agent.py -n auto 2>&1 | tail -2; echo "exit: $?"
758 passed in 94.48s (0:01:34)
exit: 0

$ uv run --group dev ruff check plugins/factory/scripts/factory.py tests/test_factory_depth.py && uv run --group dev ruff format --check plugins/factory/scripts/factory.py tests/test_factory_depth.py; echo "exit: $?"
All checks passed!
2 files already formatted
exit: 0

$ cat .sdlc/work/232-exit-notes/notes.md | head -2; echo "exit: $?"
# Notes
exit: 0
