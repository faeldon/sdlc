VERDICT: PASS

The prompts, the mend text and the tests all do what the intent's Outcome asks. The new tests I ran pass (53 passed).

## Notes
- No `checks.md` exists for this change, so there are no checks to read.
- The builder, resolver and behaviour-reviewer prompts now ask for `exit:` on every command, reads included. The behaviour reviewer's gate-record citation now shows `exit: 0`. `plugins/factory/prompts/mend.md` and the factory README say the same. `is_read()` is unchanged.
- The new test `test_no_agent_prompt_lets_a_read_leave_its_exit_off` checks every agent prompt and the mend prompt. `test_todays_stopped_commands_with_their_exits_read_clean` feeds `read_evidence()` the three commands from the 2026-11-21 stops with `exit: 0` and expects no flags. It also expects each to be flagged without the exit, so the rule did not loosen.
- The test also pins the list of prompts that end with `## Evidence` to the builder, resolver and behaviour reviewer. That answers the intent's open question about the other reviewer prompts: the other agents don't end with it, so they need no change.
- The nit `cmd_accept` recheck (`_unvouched_refusal`) is in `factory.py` and its tests are in `tests/test_land.py`. Nit 2026-11-20-47 is left out under decision D1, which the builder recorded as a default.
- I did not run the full suite. I cite the gate record, which reads `GATE: PASS`.
- The intent's open question about AGENTS.md's wording (the "but a read that shows its output" clause) is still open. The diff doesn't touch it, and it isn't a failure of this change.

## Evidence
$ head -5 .sdlc/work/215-evidence-exits/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ git diff HEAD --stat (and git diff HEAD -- plugins, tests/test_factory_depth.py, tests/test_skills.py)
12 files changed, 94 insertions(+), 19 deletions(-)
exit: 0

$ grep -rniE "owes no|no .exit|read that shows|without .exit" plugins/factory/agents plugins/factory/scripts/factory.py plugins/factory/skills
plugins/factory/scripts/factory.py:1672:            problems.append(f"{where}: `{open_cmd}` has no `exit:` line")
exit: 0

$ uv run --group dev pytest -q tests/test_factory_depth.py tests/test_land.py tests/test_skills.py -k "evidence or exit or mend or unvouched or accept"
53 passed, 574 deselected in 25.73s
exit: 0

$ ls plugins/factory/agents
approver.md arbiter.md builder.md resolver.md reviewer-behaviour.md reviewer-code.md reviewer-security.md reviewer-test.md reviewer-ui.md reviewer-ux.md spec-writer.md
exit: 0
