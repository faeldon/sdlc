VERDICT: PASS

The change does what its intent says. These are my reads, not the `checks.md` commands.
- The scorecard now ends at `## Hosts`.
- It has no seed or change ids left.
- It has 36 Status lines, and every one begins with `captured` or `not captured:`.
- `.sdlc/SDLC.md` no longer mentions waves, a release loop or `Release due`.
- The CONTRIBUTING.md scorecard row no longer says "the seeds that build it".
- The gate record for round 2 reads `GATE: PASS`.

## Notes
The spec names no end-to-end command, since this is a docs-only change. The nearest path is the gate record and a read of each doc against the Outcome.

`checks.md`, read and not run:
- **The scorecard ends after Hosts:** I expect it to pass. The last `## ` heading is `## Hosts`. I didn't search for the "Seeds to build it", "Waves" and "lists the seeds that build it" strings, but the headings listing shows no such sections.
- **Every Status line is captured or not captured:** I expect it to pass. The count is 36, and none departs from the two forms. The pattern-and-id part is covered by my id grep, which found nothing.
- **This repo releases on Release due:** I expect it to pass. A grep of `.sdlc/SDLC.md` for waves, release loop and `Release due` returned nothing.
- **The contributor docs no longer list the scorecard's seeds:** I expect it to pass. The `docs/CONTRIBUTING.md` row exists and its wording is clean.
- **No seed id or wave change number is left in the scorecard:** I expect it to pass. My `\bS[0-9]+\b|\bR[0-9]+\b` grep found nothing. I did not grep separately for the `(1NN)` and `, 1NN)` change-number forms.

I did not run `tests/test_retro.py`, `test_defaults.py` or the feature map on their own. The gate record covers them.

## Evidence
$ git diff d039b1bf7ef2fcf38bb73e770a3caff4169e31f5...HEAD --stat | head -16
 .sdlc/SDLC.md | 7 -
 (change folder files, docs/CONTRIBUTING.md, docs/RETRO-SCORECARD.md in the full 34-file list)
exit: 0

$ grep -n '^## \|^### ' docs/RETRO-SCORECARD.md | tail -8
408:### Guardrail: lead time … 443:## Insights: the synthesis questions … 463:## Hosts
exit: 0

$ grep -c 'Status:' docs/RETRO-SCORECARD.md
36
exit: 0

$ grep -n 'Status:' docs/RETRO-SCORECARD.md | grep -v -E 'Status:\*\* (captured|not captured: )' | head
(no output)
exit: 0

$ grep -nE '\bS[0-9]+\b|\bR[0-9]+\b' docs/RETRO-SCORECARD.md | head
(no output)
exit: 0

$ grep -n 'waves\|release loop\|Release due' .sdlc/SDLC.md
(no output)
exit: 1

$ grep -n 'RETRO-SCORECARD' docs/CONTRIBUTING.md
209:| `docs/RETRO-SCORECARD.md` | the framework `/sdlc:retro` reports against: its pillars, what each metric means and where it comes from; a reference, read by nothing |
exit: 0

$ head -5 .sdlc/work/226-scorecard-framework-only/build/round-2.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0
