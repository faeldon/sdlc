---
id: 065
slug: pay-down-style-and-cost-nits
tier: 1
impact: none
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea:
depends_on:
serves: none
---

# 065 — Pay down the style and cost nits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two open `[nit]` entries, each the only open entry in its theme, both cost S:

- **2026-10-24-8** `[style]` (`tests/test_defaults.py:319`): `RECORD_CLEARS` is built as a set
  from two unpacked tuples, `{*("added", …), *("new", …)}`, where one plain set literal says the
  same thing and reads plainer. It was raised by 009-drift-message's cost pass 23 days ago.
- **2026-11-04-13** `[cost]` (`.github/workflows/check.yml`): the workflow triggers on a bare
  `on: push`, so GitHub runs it for every ref pushed. `/sdlc:publish` pushes `main` and then the
  release tag (`cmd_publish` pushes `refs/heads/<trunk>` then `refs/tags/<tag>`), so each publish
  runs the Linux and Windows jobs twice on the same commit. The second run is CI minutes and
  noise, with nothing new checked. It was raised by 041-windows-lock's cost pass 12 days ago.

## Outcome

- `RECORD_CLEARS` is one set literal with the same ten members. The test that reads it behaves
  identically, and `./check.sh` passes.
- `check.yml` runs on branch pushes only, so a tag push no longer starts a run.
  `workflow_dispatch` stays, so a branch can still be checked by hand, as the file's header
  comment says.
- `/sdlc:ship` retires both nits in its `Retired nits:` paragraph.

## Affected

- **Area:** the test suite and the CI workflow.
- **Files & components:** `tests/test_defaults.py` (`RECORD_CLEARS`), and
  `.github/workflows/check.yml`'s `on:` block plus its header comment if it changes meaning.
- **Downstream:** no host reads either file. CI is this repo's own gate off the author's machine.
  `.github/workflows/` is in `[review] sensitive`, so ship gives the diff the fresh-context review.
- **Contracts:** `test_the_gate_and_ci_never_run_the_skills_cases` reads the workflow, and must
  still pass. CI's Windows job still runs only the `portable` tests.

## Constraints

- A publish must still run CI once, on the commit it pushes. Filtering out tag pushes must not
  leave the release commit unchecked.
- No job, step or test selection in the workflow changes: only its trigger.
- `RECORD_CLEARS` keeps exactly the same members. A typo there would silently weaken the drift
  test.

## Open questions

- ~~Should `on: push` be filtered to all branches (`branches: ['**']`) or to `main` alone? All
  branches keeps today's behaviour of checking a pushed change branch. `main` alone saves more but
  checks a branch only by hand.~~ Resolved: all branches. The nit asks only that the tag run go.
- ~~Is a CI run worth having on the tag anyway, as the record of exactly what was released? The
  tag points at the commit the branch push already checked, so the answer is probably no.~~
  Resolved: no. The branch push already checked the commit the tag names.

## Approach

Replace the two unpacked tuples in `RECORD_CLEARS` with one set literal of the same ten strings.
Add a `branches:` filter to `check.yml`'s `push` trigger. With `branches` given and no `tags`,
GitHub skips tag pushes. Keep `workflow_dispatch`, and update the header comment if it now says
something false. It takes in nits 2026-10-24-8 and 2026-11-04-13, which ship retires.
