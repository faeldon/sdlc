VERDICT: PASS

I ran the whole of `tests/test_train.py` and it passes (21 tests). Both findings kept from last round now have tests.

- **R14, second part.** `test_a_close_that_hands_off_runs_under_the_parents_hold` runs a real `uv run` close. It edits `scripts/sdlc.py` in the change, so close hands off to the merged script, and the close must finish within a 600 s timeout. `test_the_handoff_passes_the_hold_and_the_child_takes_no_lock` checks the rest:
  - `_handoff()` passes `LOCK_HELD_ENV` only while the lock is held.
  - A close told its parent holds the lock runs to its end while another thread holds the OS lock.
  - The variable is popped from `os.environ` at the close's entry.
  - No subprocess of the close sees the variable.
- **R8, the other two paths.**
  - `test_failing_acceptance_checks_as_stacked_eject_only_that_change`: change 2's check passes on its own base but fails when stacked on change 1. Only change 2 is ejected, and changes 1 and 3 land.
  - `test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change`: change 2's reply is still unreadable after one mend. Only change 2 is ejected, and changes 1 and 3 land.

I did not break `_handoff()` to confirm the deadlock test fails, so I haven't seen it catch the regression.

## Notes
All three checks in `checks.md` should pass. Each is a `grep` for text in a file, and I ran the matching `grep -c` counts on the same strings. Every count was 1.
- **"The policy doc says close holds the lock from its merge to its Close commit":** expect pass. `AGENTS.md` holds the sentence.
- **"The policy doc says the train stacks through resolve --onto and land no longer runs base":** expect pass. Both phrases are in `AGENTS.md`.
- **"The land skill may run the train":** expect pass. `plugins/factory/skills/land/SKILL.md` has both strings.

The gate record `build/round-2.gate.md` reads `GATE: PASS`. I did not rerun the gate and I did not run `checks.md`.

## Evidence
$ cat .sdlc/work/139-landing-train/build/round-2.gate.md | tail -15; grep -n "LOCK_HELD_ENV\|_inherit_lock\|_lock_depth\|acceptance\|unreadable\|def test_" tests/test_train.py | head -80; git status --short | head
(read; the tail shows "Validation passed", and `tests/test_train.py` lists the R14 and R8 tests above)
exit: 0

$ sed -n 170,300p tests/test_train.py; sed -n 795,875p tests/test_train.py; uv run --group dev pytest tests/test_train.py -q -n auto 2>&1 | tail -5
21 passed in 46.19s
exit: 0

$ head -5 .sdlc/work/139-landing-train/build/round-2.gate.md; grep -n "^## " .sdlc/work/139-landing-train/checks.md
GATE: PASS
exit: 0

$ sed -n 1,40p .sdlc/work/139-landing-train/checks.md
(read; the three checks described above)
exit: 0

$ grep -c "holds \`_main_lock()\` from its merge to that commit" AGENTS.md; grep -c "resolve --onto" AGENTS.md; grep -c "which no longer runs" AGENTS.md; grep -c "factory.py train \*" plugins/factory/skills/land/SKILL.md; grep -c 'factory.py train --begin <NNN…> --by <auto or person>' plugins/factory/skills/land/SKILL.md
1
1
1
1
1
exit: 0
