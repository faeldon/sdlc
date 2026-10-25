---
id: 021
slug: rework-shared-files
tier: 1
impact: patch
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea: Rework ignores shared docs and the setup record
depends_on:
serves: [O4]
---

# 021 — Rework ignores shared docs and the setup record

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The first retrospective (2026-10-24) listed 12 rework pairs, and none of them was real. All 12
closed on the same day, and every one was matched only on `defaults/SDLC.md` or
`.sdlc/setup.json`. Nearly every change in this repo edits those two files. `defaults/SDLC.md` is
the default process doc, which `.sdlc/SDLC.md` mirrors. `.sdlc/setup.json` is rewritten by
`sdlc.py record` whenever a change edits `defaults/`. None of the pairs was a follow-up fix, so
the number the process doc tells you to watch for rework only showed how this repo works.

`retro()` in `scripts/sdlc.py` already leaves some files out: a change's own `work/` folder,
`docs.context`, `docs.process` and `docs.policy`. These are the docs that ship's context pass
edits on every change. The list is fixed, though, and it misses whatever else a host's changes
all touch. In this repo that means the defaults behind the process docs and the setup record. A
host has its own equivalents: a changelog, a lockfile, a shared registry.

## Outcome

- If `retro` were run again over the window of the 2026-10-24 retrospective, it would not report
  the 12 same-day pairs that rest only on `defaults/SDLC.md` or `.sdlc/setup.json`.
- A pair two changes really share is still reported: a later change editing an earlier one's code
  or tests within `REWORK_DAYS`.
- A test in `tests/test_sdlc.py` pins both. A file most changes touch doesn't make a pair, and a
  shared code file still does.
- **Moves O4:** the rework a retrospective cites as evidence is follow-up work, so direction set
  from it rests on a real signal rather than this repo's housekeeping.

## Affected

- **Area:** the retrospective's rework count.
- **Files & components:** `retro()` in `scripts/sdlc.py` (the `touched` sets and the
  `every_change` exclusion), `tests/test_sdlc.py`, and possibly the rework line in
  `.sdlc/SDLC.md` / `defaults/SDLC.md` if what "rework" counts needs restating.
- **Downstream:** `/sdlc:retro`, which reads `rework` from `sdlc.py retro` and proposes direction
  from it. Nothing else reads it: close's `Sdlc-Rework` trailer is a separate measure inside a
  single change.
- **Contracts:** none if the exclusion is computed. A new config key would change what `sdlc.py`
  reads in a host, which makes this Tier 2.

## Constraints

- Retro stays read-only, apart from its evidence commands.
- Dropped changes go through the same filter, so "work picked up after a drop" isn't drowned out
  either.
- This change doesn't touch how a change's files are read. That's the separate M3 seed "A
  change's size counts every commit on its branch", which changes the same `touched` input.
- Nothing names this repo's own files in code. Whatever is left out, a host has to get the same
  treatment for its own files.

## Open questions

- ~~Which files stop counting?~~ Resolved: computed. Any file touched by more than a share of
  the window's changes, with no config key and no named files. Measured on this repo, that also
  leaves out `scripts/sdlc.py` (10 of 14 changes in the current window). That's right: its 45
  pairs were no more follow-up fixes than the docs' were.
- ~~If computed, what threshold, and is there a minimum?~~ Resolved: more than a third of the
  window's changes, closed and dropped together, once the window holds six. Below six, the two
  changes of any pair would already be more than a third, so nothing could pair. The minimum is
  derived from the share (`window * REWORK_COMMON_SHARE >= 2`), not a second constant.
- ~~Should retro report what it left out?~~ Resolved: yes. It's reported as `rework_common`, each
  file with how many changes touched it, which `/sdlc:retro` names in its process and
  architecture passes.

## Approach

`retro()` counts each file across the window's `touched` sets. Once the window holds six changes,
a file in more than a third of them is common and is subtracted from every pair, in both the
closed→closed and dropped→closed loops. The existing `every_change` exclusion stays. Tests in
`tests/test_retro.py` cover a six-change window where one file is common and two code pairs
survive, and a five-change window where every shared file still pairs. The Rework bullet in
`defaults/SDLC.md` and `.sdlc/SDLC.md`, `docs/REFERENCE.md` and the retro skill say what's left
out.
