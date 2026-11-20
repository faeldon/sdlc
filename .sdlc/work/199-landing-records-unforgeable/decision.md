DECISION: ESCALATE

## Why
All four reviewers return PASS in round 1. The gate is green (3556 tests passed), and R1–R10 each have a test. The decision is ESCALATE only because D3 and D5 are about scope, which the approver may not settle. This change also touches a sensitive path, `plugins/factory/scripts/landing.py`, so no default can be carried with CONFIRM.

## Open items
- Security reviewer, Medium: the README, REFERENCE.md and land SKILL.md say an agent in the worktree "can't forge" a record. The builder and resolver have Bash and can write into the git common dir. The docs should say the change stops Edit/Write and stray writes, not a determined agent with a shell.
- Security reviewer, Medium: `cmd_gate()` in `factory.py` and in `sdlc.py` checks the record before the slot wait and the run, but doesn't re-check `earlier` when it reads it afterwards. A file swapped in during that gap would have its forged attempts vouched.
- Code reviewer, nit: a one-line comment is needed where `_vouch()` mixes `closing._unlock` with the local `_try_lock`.
- Code reviewer, nit: the spec's `tests/conftest.py` helper isn't in the diff, and the gate is green anyway.
- Test reviewer, nit: the two-writer test is 400 locked appends and covers only `factory.py`'s writer, not core's copy.
- Security reviewer, Low: `vouched()` reads with `read_text`, which turns a lone `\r` into `\n`. A genuine record containing one would read back as unvouched, so it would be refused wrongly rather than let a forgery through.

## Decisions to confirm
- SETTLED: D1: spec R7 says `sdlc.py gate`, `factory.py gate` and `factory.py accept` all refuse an unvouched record, and the approved spec's *Contracts touched* names the hand gate and the AGENTS.md sentence it changes.
- SETTLED: D2: spec R3 and R7 and the spec's "Left for you" answer refuse in-flight records until each is removed and rerun, and *Alternatives rejected* rules out a one-time vouch command because it would reopen the hole.
- ESCALATED: D3: leaving `build/land-<n>.checks.md` unprotected is a scope call, and a forged `CHECKS: HARMLESS` lets a changed `checks.md` run unattended under `train --run`.
  - OPTION: leave it out and file a seed — within the intent's scope, but the hole stays open until the seed lands.
  - OPTION: add it — closes the hole now, with one more writer and one more reader beyond the approved requirements.
  - WHY: the intent names only the gate, build and accept records.
- SETTLED: D4: it duplicates D2, and spec R3 and R7 plus *Alternatives rejected* answer it the same way: refuse until removed and rerun.
- ESCALATED: D5: it duplicates D3 and is a scope call only the person can make. I recommend the same answer: leave it out and carry it as a seed, since the security reviewer judged it the same class of hole.
  - OPTION: leave it out and file a seed — within the intent's scope.
  - OPTION: add it — closes the hole now, with one more writer and one more reader.
  - WHY: the intent names only the gate, build and accept records.

## Every other reason I escalate for
- ESCALATED: look: `plugins/factory/scripts/landing.py` (`land_verdict()`, `_read_gates()`, `_read_builds()`) — this is a sensitive path and it is the code that decides what reaches `main`, so a person should confirm each unvouched record ends in `stop`, never `mend` or `pass`.

## For the person at ship
- Read the diff of `landing.py` and `factory.py` first: `vouched()`, `cmd_gate()`, `cmd_accept()`, `forged_records()` and the refusal in `cmd_land()`.
- The approved spec's *Contracts touched* covers the new core write: `sdlc.py gate` now appends the hand gate's line to the records ledger. This is the first file core writes for the factory to read, and the AGENTS.md sentence is updated.
- No other published interface is touched beyond what the spec approved.
- Decide whether the README overstatement and the re-check gap above should be fixed before landing.

- IMPACT: minor — a landing now refuses records the script didn't write, and in-flight changes must remove old records and rerun their gate or checks.

## Undone items
`notes.md` doesn't exist, so there are no unticked `- [ ]` items to dispose of.
