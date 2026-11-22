VERDICT: CHANGES

- CHANGE: [context] docs/REFERENCE.md:655-658: It says a factory run its supervisor stopped reads `stopped` in place of `quiet`, with each problem on a `⚠` line and the step that moves it on under its title. That is no longer true for a `mend` stop that is being mended. `_change_lines()` now prints `mending, ` in place of `stopped, `, and a single `→ the factory is mending the <role>: wait for it` line with no `⚠` problem lines. Add a sentence after it: a `mend` stop its supervisor is mending reads `mending` and `→ the factory is mending the <role>: wait for it`, and stays off Needs you until the mend replies or the agent's 3-hour timeout passes.
- CHANGE: [context] docs/REFERENCE.md:671-674: The list of `build` stop texts under `■ Needs you` omits the new need that `needs_of()` produces: `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it`. This is a mend left past the agent's timeout. Add it to the list. The line you edited at about 742 only covers the board's step track.

## Notes
- NIT: docs/REFERENCE.md:672: the `stopped: rerun to ask an agent again` text is now shown only after a mend is not running. A short "(a mend not being run by the supervisor)" would help. {docs S low}
- Done well: the factory README's stop table and `runs/step.md` layout, the `factory.py` and `board.py` docstrings, and the REFERENCE board paragraph all describe the `STEP: mend` and `ROLE:` records and the 3-hour timeout consistently.
- Read: the diff (docs, scripts and the factory), `intent.md`, and REFERENCE.md lines 650–680 and 735–745. I did not read CONTRIBUTING.md or `AGENTS.md` in detail. A grep for the mend stop text found nothing stale in them. Nothing was run beyond reads and greps.
