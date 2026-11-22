VERDICT: PASS

## Notes
- This change has no runtime path, so the closest end-to-end check is `checks.md` read against the files as they stand. The gate record is green.
- Check 1 (the scorecard ends after Hosts): I expect a pass. The last `## ` heading is `## Hosts`, and the "lists the seeds" phrase no longer appears.
- Check 2 (Status lines): I expect a pass. There are 36 Status lines, none that isn't `captured` or `not captured:`, and no seed id or change number within 3 lines after one.
- Check 3 (release block): I expect a pass. `.sdlc/SDLC.md` has no "release follows the waves" text and no "release loop" heading, and no wave line is left.
- Check 4 (CONTRIBUTING row): I expect a pass. The row for `docs/RETRO-SCORECARD.md` is still there and "the seeds that build it" is gone.
- Check 5 (no seed id left): I expect a pass. The grep for `S`, `R` and `(1xx)` ids in the scorecard found nothing.
- I did not rerun the test suite, per the instructions. I cite the gate record instead.
- Non-change files in the diff are 3: `.sdlc/SDLC.md`, `docs/CONTRIBUTING.md` and `docs/RETRO-SCORECARD.md`. The rest of the diff is the change's own `.sdlc/work` records.

## Evidence
$ head -3 .sdlc/work/226-scorecard-framework-only/build/round-2.gate.md
GATE: PASS

## Attempt 1
exit: 0

$ tail -8 .sdlc/work/226-scorecard-framework-only/build/round-2.gate.md
(plugin validation printed only an icon advisory, then:) ✔ Validation passed
exit: 0

$ grep '^## ' docs/RETRO-SCORECARD.md | tail -3
## Trust band: can the numbers be believed?
## Insights: the synthesis questions
## Hosts
exit: 0

$ grep -c '\*\*Status:\*\*' docs/RETRO-SCORECARD.md
36
exit: 0

$ grep -n 'release follows the waves\|^### The release loop' .sdlc/SDLC.md
(no output)
exit: 1

$ grep -n 'the seeds that build it' docs/CONTRIBUTING.md
(no output)
exit: 1

$ grep -nE '\bS[0-9]+\b|\bR[0-9]+\b|\(1[0-9]{2}\)|, 1[0-9]{2}\)' docs/RETRO-SCORECARD.md
(no output)
exit: 1

$ grep '\*\*Status:\*\*' docs/RETRO-SCORECARD.md | grep -vcE '\*\*Status:\*\* (captured|not captured: )'
0
exit: 1

$ grep -A3 '\*\*Status:\*\*' docs/RETRO-SCORECARD.md | grep -E '\bS[0-9]+\b|\bR[0-9]+\b|\b1[0-9]{2}\b' | grep -v '\*\*What'
(no output)
exit: 1

$ git diff e28d4039f22d923bdeb8e0a69aeca5a4bea6785d...HEAD --stat -- . ':!.sdlc/work' | tail
 .sdlc/SDLC.md           |  7 --
 docs/CONTRIBUTING.md    |  2 +-
 docs/RETRO-SCORECARD.md | 239 ++++++---------------------------------------
 62 insertions(+), 186 deletions(-)
exit: 0

$ grep -n 'Release due\|wave' .sdlc/SDLC.md | head
(no output)
exit: 1

$ grep -c 'lists the seeds' docs/RETRO-SCORECARD.md
0
exit: 0
