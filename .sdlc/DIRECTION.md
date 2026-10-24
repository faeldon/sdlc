# Direction

> Rewritten by `/sdlc:retro` each time it runs; history keeps every earlier version. It says where
> the repo is headed, not what is being built: the changes are in `work/`, the seeds in
> `work/ideas.md`.
>
> Every goal and milestone has an id that carries from one retrospective to the next, and ends
> done, dropped or revised, never silently gone: `sdlc.py retro-commit` refuses a doc that drops
> an open one. The forms, which `sdlc.py retro` reads:
>
> ```
> - G1. No one loses a draft
> - ~~G2. Drafts shared between accounts~~ Dropped: nobody has asked for it
>
> ### M1. Drafts reopen where they were left
>
> What's true when it's done.
>
> Groups: 006, "Reopen drafts from the list"
>
> ### ~~M2. Drafts sync every hour~~ Revised → M3: on every save, not on a timer
>
> ### M3. Drafts sync on every save
>
> Groups: 009
> ```
>
> A struck item stays for one more retrospective, then may go.

## Since the last retrospective

First retrospective: no goals or milestones were open.

## Where we are

Six changes closed and shipped in v1.1.0, published today: the test triage rule, a shim registry,
acceptance checks rerun at ship, setup refresh and uninstall, a ship-time base step, and the policy
doc named by its role. Five of the six serve no product outcome, and the retrospective has no
evidence to score any: the loop measures itself well and the product not at all. Every change stops
its person three to seven times the two-stop target.

## Goals

- G1. Each retrospective scores the product's outcomes from evidence, not from process counts
  alone (O4)
- G2. A change stops its person as often as O3 says it should, with the target and the gates
  agreeing on what that is (O3)
- G3. The loop's own numbers can be trusted: rework, size and ship's findings say what happened

## Milestones

### M1. The retrospective has evidence

`retro.evidence` names commands that print the measures O1–O3 name (issues by label per release,
the stops close records), and the next retrospective scores at least one outcome from them.

Groups: "Evidence for this repo's retrospective"

### M2. The stop target and the gates agree

O3's target and `metrics.stop_allowance` match the WAITs a change actually passes, and the median
Tier 1 change meets it.

Groups: 007, "Ship does its own landing edits"

### M3. The loop's numbers are honest

Rework counts follow-up fixes, not shared docs; a change's size is its whole branch; a ship's
unfixed nits are carried like undone items; this repo's gate fails when its setup record drifts.

Groups: "Rework ignores shared docs and the setup record", "A change's size counts every commit on its branch", "Carry a ship's unfixed nits forward", "This repo's gate fails when its setup record drifts"

## Next major release

None planned: nothing above changes what a host has to do.

## Dropped findings

- `scripts/sdlc.py` at 4,928 lines, touched by three of six changes: a duplicate of the seed
  "Architecture indicators for the retro loop", which measures churn before anything is split.
- Ship's low first-time rate: 004's ship-time base already answers the stale-base cause; the
  others were one-off.
- Tier mix of four Tier 2 to two Tier 1: each Tier 2 was forced by an always-Tier-2 rule, and six
  changes is too few to redraw the tiers. Recheck next time.
- A session runs the skill text it started with after a change edits that skill: `AGENTS.md`
  already says edits take effect in the next session.
- Findings caught at ship versus found later stays unmeasured: too few changes yet, and carrying
  nits forward (M3) covers today's gap.
