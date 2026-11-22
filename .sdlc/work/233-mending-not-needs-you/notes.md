# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Build

- The intent's two open questions are taken as defaults in the round's report: the timeout is
  the agent's own (`AGENT_TIMEOUT`, 3 hours), and the mend is written to `runs/step.md` with a new
  `ROLE:` line, as the Approach says.
- "Newer than the stop" comes from the order the records are written in, not from file times:
  every `verdicts --record` writes `runs/step.md` over, so a `STEP: mend` there was written after
  the stop beside it.
- A mend whose session fails puts `runs/step.md` back, so a dead mend never reads as one running.
