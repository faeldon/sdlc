DECISION: READY

**Why.** All of R1–R14 is built, and every test the spec names is in `tests/test_factory.py` or `tests/test_board.py`. The builder also added two more: `test_restart_refuses_to_overwrite_an_archive` and `test_restart_refuses_what_start_refuses`. The script's gate passed on its first attempt with 1923 tests. The one round's code review is `VERDICT: PASS` with no Critical or Required findings, and nothing in it suggests the spec was wrong. The new writes stay inside the change's own folder. The one rename never overwrites a file, keeps the old decision byte for byte, and only runs after the person's yes. No decision is waiting on the person, so this is ready.

**Open items.** No CHANGE lines are open. These are only the reviewer's optional notes (reviewer: code):
- The very long artifacts-list line in `plugins/factory/skills/build/SKILL.md` needs re-wrapping (code, optional).
- If a restart was cut short, rerunning `restart` with different `--words` silently keeps the old words. It could warn or refuse instead (code, optional).
- `restart_state()` returns the whole decision as `reasons`, so the skill has to pull out the first reason itself (code, nit).

**Decisions to confirm.** None. There is no `decisions.md`, and the builder raised no decisions.

**For the person at ship:**
- **The new round code in `factory.py`.** `loop_state()` has a new restart branch at about lines 1221 and 1281. Check that it comes after the problems and pending-decisions checks, and that `exhausted`, `rework` and `limit` are counted from round R. Then check `depth()` / `_rounds_at_depth()`, which now count each round from its own restart. This loop logic decides every factory run, not just restarted ones.
- **The new `restart` command (`cmd_restart()`, about line 1596).** It writes the record, then renames, then sets the stage. Confirm the "won't overwrite an archive" refusal comes before any write.
- **The restart prompt in `_task("build")` (about line 1826).** It quotes the escalation's reasons and the person's words. Make sure the words never reach a command line, only their id `R<k>`.
- **The reviewer didn't check the tests one by one.** Their notes say they read the test files only through the gate passing, not each test against its requirement. Spot-check R7, R8 and R10. The builder showed R7's and R8's tests failing when its fix was undone. R6's code is there, but the plan's "As built" note says R6 "passed as pins", which contradicts that report. Check that `test_the_restart_prompt_carries_the_escalation` really reads the new prompt.
- **Not part of this change.** `.sdlc/work/inbox.md` had a conflict that was resolved (`conflicts.md`), and the builder found an inbox edit already in the tree when it started. Make sure the inbox change on the branch is meant to be there. The resolved conflict also keeps `land`'s auto-pass off for this change.

- IMPACT: minor — factory users can now send an escalated change back for another build (a new `factory.py restart` command and a third wording of build's question), and nothing that already worked changes.
