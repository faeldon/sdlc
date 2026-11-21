VERDICT: PASS

The prompts now ask for `exit:` after every command, reads included. `is_read()` is unchanged. The new tests pass. The gate record for this round is green.

The diff also holds a change the intent doesn't mention. `cmd_accept` now checks the earlier record again after the checks ran, and a test covers it. That test passes too. It traces to nit 2026-11-21-61, which the test's docstring cites; I haven't checked the register.

## Notes
- `checks.md`: none exists for this change, so there was nothing to read.
- No end-to-end path is named. The closest is the two new prompt tests, `test_no_agent_prompt_lets_a_read_leave_its_exit_off` and `test_todays_stopped_commands_with_their_exits_read_clean`. They show the three commands from today's stops read clean once they carry an `exit:`, and each is still flagged without one.
- The builder, resolver and behaviour prompts, `mend.md` and `tests/prompts/*` are all consistent with each other. The README's wording is a little loose but accurate.

## Evidence
$ cat .sdlc/work/215-evidence-exits/build/land-1.gate.md (via grep -n "exit\|GATE\|PASS" … | head -5)
1:GATE: PASS
5:Verdict: PASS
exit: 0

$ git diff 7ca5f0cab2b552870d7df0d29c17ce407dd4e488...HEAD --stat
31 files changed, 562 insertions(+), 19 deletions(-)
exit: 0

$ uv run --group dev pytest -q tests/test_factory_depth.py -k "exit_off or todays_stopped"
2 passed, 56 deselected in 0.03s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k forged_while_accept
1 passed, 95 deselected in 0.76s
exit: 0
