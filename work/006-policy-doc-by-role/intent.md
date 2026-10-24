---
id: 006
slug: policy-doc-by-role
tier: 1
impact: patch
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea:
depends_on:
serves: none
---

# 006 — Name the policy doc by its role in the process doc

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`defaults/SDLC.md` names the policy doc as `CLAUDE.md` in 8 places (lines 20, 29, 103, 195, 211,
228, 256, 257), but `docs.policy` isn't always `CLAUDE.md`. Setup writes an `AGENTS.md` (imported
by a one-line `CLAUDE.md`) and sets `docs.policy = "AGENTS.md"` when a repo has neither, and
`load_config()` falls back to `AGENTS.md` when that is the only one. Every such host gets a process
doc pointing at a file that holds no invariants. Found on 2026-10-24, resetting this repo's
`.sdlc/SDLC.md` to the default: the reset would have put `CLAUDE.md` back in 8 places, so the copy
keeps `AGENTS.md` by hand. Hard-coding `AGENTS.md` instead would move the error to every host that
already had a `CLAUDE.md`. The rest of the plugin already names it by role: the Retro row
(`defaults/SDLC.md:73`), `templates/intent.md`, `templates/spec.md`, `defaults/REVIEW.md:40`.

## Outcome

- `grep -n 'CLAUDE.md' defaults/SDLC.md` prints only line 20, which names the doc in full in
  `REVIEW.md`'s wording: the policy doc (`[docs] policy`, `CLAUDE.md`, or `AGENTS.md` when that is
  the only one).
- The other 7 say "the policy doc"; line 211 reads "**The policy doc is the standing context**".
- `.sdlc/SDLC.md` carries the same wording in place of its 8 `AGENTS.md`s, so those lines drop out
  of `diff defaults/SDLC.md .sdlc/SDLC.md`.
- `./check.sh` passes.

## Affected

- **Area:** the shipped defaults, and this repo's own process doc.
- **Files & components:** `defaults/SDLC.md`, `.sdlc/SDLC.md`, and `tests/test_playbook.py`, whose
  phrases pinned the two `CLAUDE.md` sentences.
- **Downstream:** every host setup copied the doc into. After an update, `drift` proposes the new
  wording as a `refresh` to hosts that never edited those blocks; a host that edited one keeps its
  text. Nothing `sdlc.py` reads: the doc has no frontmatter keys, and no heading changes.
- **Contracts:** `tests/test_defaults.py`: this repo's copy keeps every default heading in order,
  and the shipped docs keep one shape. Both hold, since no heading changes.

## Constraints

Wording only. No `#` heading or `- **lead**` bullet changes: those are the block keys `drift`
matches on, and a renamed one reads as a removed block and a new one.

## Open questions

- ~~After ship, does this repo's own `drift` come out clean, or do the changed blocks show as
  `conflict` until `sdlc.py record` runs again, so the ship commit should carry a re-recorded
  `.sdlc/setup.json`?~~ Resolved: clean. With both files edited alike, `drift` reports nothing in
  `breaking`, `refresh` or `report`, so `.sdlc/setup.json` stays as it is.

## Approach

Edit the 8 lines in each file, rewrapped to the doc's width: line 20 gets the full name, the rest
"the policy doc". Then run `./check.sh` and `sdlc.py drift`.
