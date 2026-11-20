VERDICT: PASS

The change adds a "release loop" answer to `.sdlc/SDLC.md`. It sits under the same heading the guide uses (`guide/process.md:408`). It says releases follow the waves and don't wait for Release due, and that the release comes once each wave has landed and before the next retrospective. It doesn't restate the guide's Release due rule. The `docs/RETRO-SCORECARD.md` *Waves* section it cites exists. The spec's only end-to-end path is reading the doc, so there was nothing else to run.

## Notes
- `checks.md` has one check, "The process doc says this repo releases once each wave has landed". I expect it to pass: the section under `### The release loop` contains both "wave" and "before the next retrospective" (each grep counted 1 hit). I read it and didn't run it.
- The gate record `build/round-1.gate.md` says `GATE: PASS`. I didn't rerun the gate.

## Evidence
$ git diff main --stat | tail -5
 .sdlc/SDLC.md | 7 +++++++
exit: 0

$ git diff main -- .sdlc/SDLC.md
(adds the 7-line `### The release loop → /sdlc:release, then /sdlc:publish` block)
exit: 0

$ grep -n "release loop" -i guide/process.md .sdlc/SDLC.md
.sdlc/SDLC.md:83:### The release loop → `/sdlc:release`, then `/sdlc:publish`
guide/process.md:408:### The release loop → `/sdlc:release`, then `/sdlc:publish`
exit: 0

$ head -5 .sdlc/work/205-release-cadence/build/round-1.gate.md
GATE: PASS
exit: 0

$ awk '/^### The release loop/{f=1;next} /^#/{f=0} f' .sdlc/SDLC.md | tr '\n' ' ' | grep -c 'wave'
1
exit: 0

$ awk '/^### The release loop/{f=1;next} /^#/{f=0} f' .sdlc/SDLC.md | tr '\n' ' ' | grep -c 'before the next retrospective'
1
exit: 0

$ grep -n "Waves" docs/RETRO-SCORECARD.md | head -3
538:### Waves
exit: 0
