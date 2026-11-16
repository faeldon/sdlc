# 060 — Rework as a declared fix, with surviving lines as the cross-check · notes

## This repo's window (19 changes since the retrospective of 2026-11-04)

- Before: 50 file pairs under `rework`, none a fix anyone declared.
- After: 3 `rework` links, all through fixed bugs' `Introduced by:` (050 → 015 and 047, 052 →
  050), and 26 `rework_questions`, 12 of them more than two lines. Some are real follow-ups no one
  declared (059 → 048: the hotspot nit 059 took in), which is what the questions are for.

## Departures from the spec

- **`.sdlc/setup.json` is left out of the blame** beside the register: `record` rewrites it, so a
  later change replacing its lines is the script's doing, not a fix. The first run listed it in two
  questions.
- **A link to the change itself is dropped**: a bug whose `Introduced by:` names the change that
  fixed it says nothing about rework.
- **The retro skill's architecture pass** now weighs hotspots and coupled pairs alone; the sentence
  that read `rework_common` as "a file most changes had to touch" now reads the hotspots for it.
