# Decisions

- [x] D1 (builder round 1, default): Is the timeout before an unmended `mend` stop becomes the person's the agent's own? Going ahead with `AGENT_TIMEOUT` (3 hours) unless told otherwise. → decided: the assumed default, confirmed when landing
  - OPTION: `AGENT_TIMEOUT` — no session can outlive it, so a mend past it is surely dead; a crashed supervisor's card waits up to 3 hours
  - OPTION: a fixed shorter figure (say 30 minutes) — a dead mend surfaces sooner; a slow live mend could show under Needs you while it still runs
  - WHY: the intent's constraint that only files and their times decide, and the agent's timeout is the one bound a session can't pass
- [x] D2 (builder round 1, default): Does `agent --task mend` record the mend in `runs/step.md` (with a new `ROLE:` line), not read it from `runs/mended` and the stop's time? Going ahead with `runs/step.md` unless told otherwise. → settled by the approver: The intent's Approach already names `runs/step.md` with `STEP: mend`, and the code reviewer confirmed the diff follows it. The new `ROLE:` line is optional, so the step record gains nothing a reader must have. The alternative, `runs/mended`, is only written after the reply, so it would fail the intent's outcome that the card changes when the supervisor acts.
  - OPTION: `runs/step.md` with `ROLE:` — the card changes the moment the mend starts; the step record gains one optional line
  - OPTION: `runs/mended` plus the stop's time — no new line; `runs/mended` is written only after the reply, so the card would still show Needs you during the mend
  - WHY: the intent's outcome that the card changes when the supervisor acts, not after the reply
- [x] R1 (person, fix): In docs/REFERENCE.md: near lines 655–658, add that a mend stop its supervisor is mending reads mending and → the factory is mending the <role>: wait for it, with no ⚠ lines, and stays off Needs you until the mend replies or times out; near lines 671–674, add the timed-out mend's text to the Needs-you list: stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it.
