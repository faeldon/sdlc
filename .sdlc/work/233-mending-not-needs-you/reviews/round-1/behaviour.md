VERDICT: PASS

The change does what the intent's Outcome and Approach say. I ran the focused tests rather than the path itself. `agent --task mend` writes `runs/step.md`, `needs_of()` reads it, and `status` and the board show "mending". I did not run the mend end to end. The change has no `spec.md`, because it is Tier 1.

## Notes
- **Mend under way:**
  - `agent --task mend` calls `_record_mend()` before the session starts. It writes `STEP: mend`, `ROLE:` and `SINCE:`.
  - `factory_records.mending()` reads that record.
  - `needs_of()` adds no need while `mend_running()` is true: the stop's way is `mend` and `now` is before `since` plus the agent's own timeout.
  - `status` marks the change "mending," and the board keeps the card in Building.
- **Mend left past its timeout:** `needs_of()` adds "stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build <id> if no session runs it", so it matches the Outcome's example.
- **Mend used up:** the way becomes `rerun`, so `FACTORY_STOP_NEEDS` applies and the stop reaches Needs you at once.
- **Failed mend session:** `_unrecord_mend()` restores the previous `step.md`, so no card says "mending" while nothing runs.
- **Open questions:** the code answers both. The timeout is the agent's own (`AGENT_TIMEOUT`). `agent --task mend` writes `runs/step.md`.
- **Constraints:** no reader guesses whether a session is alive. Only the files and their times decide.
- **`checks.md`:** none exists for this change, so there is nothing to read.
- **Whole suite:** the gate record `build/round-1.gate.md` says `GATE: PASS`, `Command: ./check.sh`, `Exit: 0`. I did not rerun it.
- **Not run:** I did not run a real mend session, since that needs a paid agent call.

## Evidence
$ cd .sdlc/work/233-mending-not-needs-you && ls; head -80 intent.md; tail -15 build/round-1.gate.md; cat checks.md; git log --oneline -3; git diff --stat HEAD~1 | tail -15; echo "exit: $?"
(Output: the folder listing, the intent, the gate record's tail ending `✔ Validation passed`, `checks.md: No such file or directory`, and a 12-file diff stat.)
exit: 0

$ head -8 .sdlc/work/233-mending-not-needs-you/build/round-1.gate.md
GATE: PASS / ## Attempt 1 / Verdict: PASS / Command: ./check.sh / Build: c4ed8895d784d9b3 / Exit: 0
exit: 0

$ git diff HEAD -- scripts/sdlc.py scripts/factory_records.py   # shows mend_running(), needs_of(), mending(), status
exit: 0

$ git diff HEAD -- plugins/factory/scripts/factory.py   # shows _record_mend(), _unrecord_mend(), and cmd_agent's call
exit: 0

$ uv run --group dev pytest -q tests/test_board.py tests/test_factory_agent.py tests/test_modules.py tests/test_sdlc.py -k "mend"
15 passed, 756 deselected in 18.52s
exit: 0
