VERDICT: PASS

The two docs additions are what the person asked for, and the wording matches the code.

- **First addition (`docs/REFERENCE.md` ~655–660):** it says a `mend` stop being mended reads `mending`, with no `⚠` lines and `→ the factory is mending the <role>: wait for it`, and stays off Needs you until the mend replies or times out. The `→` text matches `scripts/sdlc.py:11003`.
- **Second addition (~675–678):** the Needs-you list has the timed-out mend's text, `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it`. This matches `scripts/sdlc.py:5211`, which prints the time as `since[11:16]`, i.e. HH:MM.

## Notes
- There is no `checks.md` in the change folder, so there are no acceptance checks to read.
- The spec names no separate end-to-end path for this round. The fix is docs only, so I compared the new text with the code that prints it.
- I did not run the suite. The gate record for this round is `build/land-1.gate.md`. The builder reports 1139 tests passing on the nine test files that read `REFERENCE.md`.
- Minor style point, not a CHANGE: the second hunk leaves one over-long line in the Needs-you list (the `parked past its deadline` clause).

## Evidence
$ git diff 3deef3f09f82103d849d7babcb6331d5ab8f0666...HEAD -- docs/REFERENCE.md
(hunks at 655, 670 and 739: the mending paragraph, the Needs-you list's timed-out mend text, and the `runs/step.md` mention)
exit: 0

$ grep -n "since .* with no reply" scripts/sdlc.py scripts/board.py; grep -n "mending the" docs/REFERENCE.md
scripts/sdlc.py:5211:                f"stopped: mending the {mend['role']} since {mend['since'][11:16]} with no reply: "
660:`⚠` lines and `→ the factory is mending the <role>: wait for it`, and stays off Needs you until the mend replies or runs past the agent's 3-hour timeout…
677:for a park past its deadline, and `stopped: mending the <role> since HH:MM with no reply: rerun
exit: 0

$ ls .sdlc/work/233-mending-not-needs-you/
build decision.md decisions.md findings.md intent.md notes.md plan.md reviews runs
exit: 0
