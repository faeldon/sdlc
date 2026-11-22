VERDICT: PASS

The widened `EXIT_RE` and the new prompt sentences do what the intent says. I found nothing to change.

## Notes
- **`exit: <n>` with a note:** `exit: 2 (hook refusal; the command did not run)` and `exit: 0 # ok` now count as exits. `exit: nonzero (task failed)`, `exit: not run (…)` and `exit: 2x` still name the missing exit. The six parametrized cases in `test_an_exit_with_a_note_after_its_code_is_an_exit` pass.
- **Prompts:** both `builder.md` and `reviewer-behaviour.md` now say that a command that ran records its real code via `; echo "exit: $?"`, and that a command a hook refused is no `$ ` line. The behaviour reviewer is told to list it under `## Notes` with the hook's message. The builder is told to say so in its report above the evidence.
- **Not run:** I did not run the whole suite, as the instructions say. I did not read `build/land-1.gate.md` for its exit line, so it is cited only by its tail, which ends `✔ Validation passed`.
- **`checks.md`, one section ("Both prompts say a hook-refused command…"):** I expect it to pass. I read it and did not run it. Once the lines are joined, both files contain the phrase ``A command a hook refused never ran, so it is no `$ ` line``. Both contain `echo "exit: $?"`. The reviewer file contains ``list it under `## Notes` ``.

## Evidence
$ git diff c64aabc9e9f7ea2dd5bfe819ad89bd0aed4d18a2...HEAD -- plugins tests (read; the diff showed the `EXIT_RE` change, both prompt edits and the new test)
exit: 0

$ cat .sdlc/work/232-exit-notes/checks.md
(the single check shown above)
exit: 0

$ tail -5 .sdlc/work/232-exit-notes/build/land-1.gate.md
    ✔ Validation passed
exit: 0

$ uv run --group dev pytest tests/test_factory_depth.py -q -k exit_with_a_note
6 passed, 58 deselected in 1.66s
exit: 0

$ grep -n "exit:" .sdlc/work/232-exit-notes/build/land-1.gate.md | tail -3
(no lines printed)
exit: 0
