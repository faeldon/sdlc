VERDICT: PASS

## Notes
- **End-to-end path:** the spec names no command, so I ran the change's own tests. They cover the three behaviours:
  - A decision's question keeps its continuation lines, and the options and why read under it.
  - The same raise made twice lands once.
  - The read-only list refuses `--der` and `--dereference-recursive=x`, and still passes `--directories=skip` and `--de`.
- **Land description:** it now names the slow gate at the tip and the approver's judgement of changed checks, and its test passes.
- **Old ledgers:** one test covers a ledger written before this change, where only the question's first line was kept. It matches that line, files nothing new and fills the options once.
- **`checks.md`:** this change has none, so there is nothing to read.
- **AGENTS.md wrap (nit 2026-11-19-70):** the diff doesn't touch AGENTS.md. The only line `awk` flagged is line 12, and only because its arrows count as bytes, so it is within the wrap. Nothing is left to fix.
- **Gate:** `round-1.gate.md` records PASS, with 3447 tests passed and plugin validation passed.
- **Not run:** I did not run the whole suite, and I did not run the paid cases.

## Evidence
$ head -8 .sdlc/work/193-ledger-and-landing-fixes/build/round-1.gate.md
GATE: PASS / Verdict: PASS / Command: ./check.sh / Exit: 0
$ grep -n -i "pass\|fail" .sdlc/work/193-ledger-and-landing-fixes/build/round-1.gate.md
62:    3447 passed, 29 skipped in 232.36s (0:03:52)
$ git diff 3e35f35a11620590384001cf3ad4b34f1f9fd68e...HEAD -- plugins tests
(read: the diff of `factory.py`, `landing.py`, the land `SKILL.md` and the tests)
$ uv run --group dev pytest -q tests/test_factory.py::test_a_question_in_sub_bullets_keeps_every_line_and_its_options tests/test_factory.py::test_a_ledger_holding_a_question_s_first_line_is_matched tests/test_factory.py::test_a_decision_reraised_with_the_same_alternatives_lands_once tests/test_skills.py::test_the_land_description_names_what_a_landing_runs
4 passed in 2.08s
exit: 0
$ uv run --group dev pytest -q tests/test_train.py -k read_only
55 passed, 88 deselected in 18.96s
exit: 0
$ ls .sdlc/work/193-ledger-and-landing-fixes/checks.md
ls: No such file or directory
exit: 1
$ sed -n 12p AGENTS.md
stages (intent → spec → plan → build → ship → close), with a person's approval at every stage
exit: 0
