VERDICT: PASS

The spec names no command to run, so the end-to-end path is a read of the diff. The change adds one block to `.sdlc/SDLC.md`, and it does what the Outcome asks.

- **Heading:** the block sits under `### The release loop → /sdlc:release, then /sdlc:publish`, the same heading the guide has at `guide/process.md:408`.
- **Content:** it says this repo releases once each wave has landed, and before the next retrospective, rather than when Release due shows. It gives the reason in two sentences and doesn't restate the guide's Release due rule.
- **Reference:** it cites `docs/RETRO-SCORECARD.md`, *Waves*, and that section exists at line 538.
- **Gate:** the round-1 gate record reads PASS, and the land gate shows 3561 passed, 29 skipped.

## Notes
- **checks.md, "The process doc says this repo releases once each wave has landed":** I expect it to pass. Its awk takes the lines under the `### The release loop` heading up to the next `#` line. That text contains "wave", and "before the next retrospective" sits on a single line, so both greps match.
- I did not run the check, as instructed.

## Evidence
$ git diff 140aff72ef1f31dc2aad51c100104cd97b80fd9b...HEAD -- .sdlc/SDLC.md
(diff adds the `### The release loop → /sdlc:release, then /sdlc:publish` block with 7 lines)
exit: 0

$ head -5 .sdlc/work/205-release-cadence/build/round-1.gate.md
GATE: PASS
exit: 0

$ grep -n "passed" .sdlc/work/205-release-cadence/build/land-1.gate.md
62:    3561 passed, 29 skipped in 405.03s (0:06:45)
exit: 0

$ grep -n "^### The release loop" guide/process.md .sdlc/SDLC.md
guide/process.md:408:### The release loop → `/sdlc:release`, then `/sdlc:publish`
.sdlc/SDLC.md:83:### The release loop → `/sdlc:release`, then `/sdlc:publish`
exit: 0

$ grep -n "Waves" docs/RETRO-SCORECARD.md
538:### Waves
exit: 0
