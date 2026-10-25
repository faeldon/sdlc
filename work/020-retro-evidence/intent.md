---
id: 020
slug: retro-evidence
tier: 1
impact: none
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea: Evidence for this repo's retrospective
depends_on:
serves: [O4]
---

# 020 — Give this repo's retrospective evidence to score its outcomes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`retro.evidence` is empty in `.sdlc/config.toml`, so the retrospective of 2026-10-24 could score
none of O1–O4 in `.sdlc/PRODUCT.md`: every outcome was carried unscored, and the direction it set
rested on process counts alone. M1 in `.sdlc/DIRECTION.md` ("The retrospective has evidence") has
this seed as its only group.

Two of the measures name GitHub issues: issues filed against setup, `new` or close per release
(O1), and issues reporting lost work or a number given twice (O2). Every issue on the repo so far
is a change's own tracking issue (labelled `sdlc`). None is a reported bug, and no label separates
one from a change issue, so a command written today would count the wrong thing, or nothing.

## Outcome

- `.sdlc/config.toml` sets `retro.evidence` to read-only commands that print counts, never issue
  text or anyone's personal data: issues labelled `bug` and not `sdlc`, per release window (the
  tags), split into setup / `new` / close (O1); issues reporting lost work or a duplicated number
  (O2).
- `sdlc.py retro` from the main checkout shows each command's row with `exit: 0` and no `error`.
- The next retrospective scores at least one outcome from that evidence, which is M1's own test.
  Zero bug issues counts as a reading, not an absence.
- **Moves O4:** the retrospective's direction cites outcome evidence instead of carrying every
  outcome unscored, so the share of direction goals that cite an outcome and its evidence rises
  above zero.
- `./check.sh` passes.

## Affected

- **Area:** this repo's own configuration and the retrospective that reads it. No plugin code
  changes.
- **Files & components:** `.sdlc/config.toml` (`[retro]`); possibly a small read-only script under
  `.sdlc/` if counting per release needs more than a one-liner; `docs/CONTRIBUTING.md` if a label
  convention for reported bugs is introduced.
- **Downstream:** `/sdlc:retro` in this repo, through `_evidence()`; the GitHub repo's labels, if a
  convention is added. Hosts don't read this repo's config, so none is affected.
- **Contracts:** evidence commands run only from `sdlc.py retro`, never from `check`, so the
  offline gate is unchanged. Each gets 60 s and 20,000 characters; one that fails is a row, never
  a failed retrospective.

## Constraints

- **Read-only:** the commands query `gh` and `git` and write nothing.
- **Counts and summaries only:** no issue titles, bodies or authors in the output (REFERENCE's rule
  for evidence).
- **Nothing local:** commands name no other project and no machine path
  (`tests/test_nothing_local.py`).
- **Nothing a host runs:** no file in `scripts/`, which ships in every host's cached copy of the
  plugin.
- **Swappable source:** the bugs register seed will become the better source for O1/O2. These
  commands should be easy to replace then, not a second scheme to keep in step.

## Open questions

- ~~How is an O1 or O2 issue marked?~~ Resolved: triage labels it `bug`, plus `area: setup`,
  `area: new` or `area: close` (O1), or `lost-work` (O2); the labels are created on the repo and
  noted in `docs/CONTRIBUTING.md`.
- ~~Does O3 need a command at all?~~ Resolved: no. Retro's `metrics.groups` already reports
  `target` and `over` per tier.
- ~~Is the release window the `v*` tags' dates, or "since the last retrospective"?~~ Resolved: the
  tags' times, each closing a window, plus `unreleased`, as O1's measure says.
- ~~Does evidence need to say `tests/test_adoption.py` passes?~~ Resolved: no, `./check.sh` runs
  it on every change.

## Approach

Add `evidence = [...]` under `[retro]` in `.sdlc/config.toml`: one `gh issue list` count for
`bug`-labelled, non-`sdlc` issues per release window (bucketed by the `v*` tags' dates) for O1, and
one for O2's lost-work / duplicate-number reports. If bucketing by tag needs logic beyond a
pipeline, put it in a short script under `.sdlc/`. Run `sdlc.py retro` once from the main checkout
to confirm every row has `exit: 0`, and note any label convention in `docs/CONTRIBUTING.md`.
