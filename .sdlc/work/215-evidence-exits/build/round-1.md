I've built 215 and left it uncommitted. All three agent prompts that end with `## Evidence` now ask for `exit:` after every command, reads included. The script's own rule is unchanged. The affected test files pass (701 tests) and ruff is clean. I didn't run the full gate; that's the script's next step.

**Slices**
1. **Prompts.** `builder.md`, `resolver.md` and `reviewer-behaviour.md` say "every command, reads included (`cat`, `head`, `ls`)". The "unless it is a read that shows its output" clause is gone. The behaviour reviewer's gate-record citation now reads `` `$ cat …/round-N.gate.md`, the lines it printed, and `exit: 0` `` instead of "which a read owes no `exit:`". The mend prompt (`prompts/mend.md` `## evidence`) now adds "an exit: line after every command, reads included". Its three saved copies in `tests/prompts/` are updated to match. The factory README's *Shown, not said* says agents are asked for every exit, while the script still accepts a read without one. I also reworded the `READS` comment in `factory.py`. `is_read()` and `read_evidence()` are unchanged.
2. **Evidence reader.** This is only a test: it pins the existing behaviour.
3. **Accept re-check (nit 2026-11-20-61).** The gate already re-checks its record after the run; `cmd_accept()` didn't. It now checks again that `build/land-accept.md` is still vouched after `sdlc.py accept` runs, before it reads the earlier record, as `cmd_gate()` does.

**Tests**
- `test_no_agent_prompt_lets_a_read_leave_its_exit_off` (`tests/test_factory_depth.py`): no agent prompt or mend prompt has the old exemption wording. The three prompts with `## Evidence` (exactly those three) ask for every command's exit, and the gate-record citation shows `exit: 0`. I saw it fail first, on `builder.md`'s "unless it is a read".
- `test_todays_stopped_commands_with_their_exits_read_clean`: today's three stopped commands pass with their `exit:` lines and are still flagged without them, so the rule hasn't loosened. It passed the first time it ran, since the reader already behaved this way.
- `test_a_record_forged_while_accept_ran_is_never_appended_to` (`tests/test_land.py`): a check that rewrites the accept record while it runs gets a refusal, and the record and ledger are left untouched. I saw it fail first: the forged record was appended to.
- `tests/test_skills.py::test_what_runs_the_change_shows_its_evidence_and_never_runs_checks` was asserting the old exemption wording (123 R8). It now asserts "every command, reads included".

**`plan.md`** is written. Since drafting it I added the `test_skills.py` edit and the reason nit 47 isn't built.

**`notes.md`** answers the intent's two open questions:
- AGENTS.md stays as it is, because it describes the script's rule.
- Only these three prompts have an `## Evidence` section. The other reviewers' `Evidence:` is a field on each finding, which `read_evidence()` never reads.

It also has one unticked follow-up for nit 47, done properly.

- DECISION: [default] Leave nit 2026-11-20-47 (`intent_closes()` from the fork point) out of this change. Going ahead unless told otherwise.
  - OPTION: leave it out, keep the follow-up in notes.md — no change to the bar; a build can still remove its own `closes:` line
  - OPTION: read the fork point and the working copy together — never loosens anything, but in a factory run the fork point never holds `intent.md`, so it does nothing
  - OPTION: record the approved `closes:` in the records ledger at `start` — actually fixes it; new mechanism, more than an S nit
  - WHY: the change's folder isn't tracked until ship commits it, so a read at the fork point finds no `closes:`. Using that alone would let every change carry a `- CONFIRM:` default to the landing, even one its intent says may not.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_factory_depth.py -k "lets_a_read or stopped_commands"
FAILED tests/test_factory_depth.py::test_no_agent_prompt_lets_a_read_leave_its_exit_off
1 failed, 1 passed, 56 deselected in 0.39s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_depth.py -k "lets_a_read or stopped_commands"
2 passed, 56 deselected in 0.05s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k forged_while_accept
E       assert (0 == 1)
1 failed, 95 deselected in 1.20s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "accept"
7 passed, 89 deselected in 6.38s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k test_what_runs_the_change_shows
1 passed, 472 deselected in 0.15s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_depth.py tests/test_land.py tests/test_skills.py tests/test_prompts.py tests/test_records_ledger.py -n auto
701 passed in 44.74s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
333 files already formatted
exit: 0
