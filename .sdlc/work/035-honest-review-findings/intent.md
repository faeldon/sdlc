---
id: 035
slug: honest-review-findings
tier: 2
impact: minor
stage: shipped
created: 2026-11-03
updated: 2026-11-03
shipped: 2026-11-03
idea: 2026-11-03-1
depends_on:
serves: none
---

# 035 — Review findings a person can trust

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Ship's review (`guide/review.md`, Step 3 of `skills/ship/SKILL.md`) produces findings that are hard
to check and hard to learn from, in three ways the Claude Code team's account of its own code
review ("How the Claude Code team does code review", Oct 2026) names:

- **A finding needs no evidence.** The guide never asks for a file and line, so a finding can be a
  guess from a function's name; it names one instance, not the class of bug, so the fix covers one
  line; on a change with `fixes:` nothing asks whether the root cause was fixed or a symptom; the
  report has no fixed opening, so "nothing to fix" is buried in prose; and a repo's review doc has
  nowhere to list the paths its review should skip.
- **Old bugs are blamed on the diff.** A bug in code the diff didn't touch is ranked Important or
  Nit like any other: an Important one blocks the commit over something the change didn't cause,
  and either way it is folded into the change's findings and lost once it lands. The post found
  about 59% of what its reviewer kept flagging was code that predated the change.
- **Nobody records what became of a finding.** `Sdlc-Findings` counts findings by rank and pass,
  not whether each was fixed, wrong, intentional or didn't matter. Retro can't tell a review that
  catches bugs from one that makes noise, which is half of what `UNMEASURED` in `scripts/sdlc.py`
  says is unrecorded ("findings caught at ship vs. found later"), and why 2026-10-26-6 can't tell a
  ship stopped by a real finding from one that circled.

This takes in seeds 2026-11-03-1, -2 and -3 together, as phase 1.

## Outcome

- `guide/review.md`'s reporting rules require a file and line as evidence for every finding, the
  bug's class named so the fix covers every instance, a root-cause check on changes with `fixes:`,
  and findings that open with their count and say "nothing to fix" when there is nothing.
  `defaults/REVIEW.md` has a slot for the paths a repo's review skips. `sdlc.py drift` is clean
  after `record`.
- A finding in code the diff didn't change is tagged **Pre-existing**, never blocks the commit, and
  ship proposes it as a `[bug]` entry (with `Severity:` and `Paths:`) behind its one WAIT, the way
  it proposes nits.
- Every finding gets a disposition at ship (`fixed`, `wrong`, `intentional`, `minor`, with a reason
  for any not fixed), and `Sdlc-Findings` gains `preexisting=` and the disposition counts. The
  existing keys keep their meaning, so old trailers parse as before.
- `sdlc.py retro` reports, per pass, how many findings ship raised and what became of them, with a
  test pinning an old trailer and a new one.
- Seeds 2026-11-03-1, -2 and -3 all leave the register when this ships.

## Affected

- **Area:** the review guide, ship, and retro's reading of history.
- **Files & components:** `guide/review.md`, `defaults/REVIEW.md`, `.sdlc/setup.json` (via
  `record`), `skills/ship/SKILL.md` (Steps 3, 4 and 6, and maybe `preflight --question` for the
  bugs clause), `scripts/sdlc.py` (`ship_question()`, retro's findings), `scripts/metrics.py`
  (`parse_trailers`, if the parsing lives there), `docs/REFERENCE.md` (the trailer), and tests in
  `test_skills.py`, `test_retro.py` and `test_defaults.py`.
- **Downstream:** every host's ship, since the guide is read in place; hosts' review docs, through
  `/sdlc:setup`'s drift proposal for the new slot; retro reading every past ship commit's trailer.
- **Contracts:** the metrics trailer format is a contract (extend, never redefine); confirm before
  writing (the new bug entries go behind ship's existing WAIT, not a second one); one WAIT per
  writing skill; ship's question is worded by `preflight --question`, never by hand; `guide/` and
  `defaults/` edits rerun `record`; this repo's `.sdlc/REVIEW.md` holds answers only, so the
  guide's new rules aren't mirrored there.

## Constraints

- Old `Sdlc-Findings` trailers read exactly as before; a missing key is unknown, not zero.
- Ship keeps one WAIT, and an Important finding the diff introduced still blocks the commit.
- The guide stays generic: nothing about this plugin goes into it.
- Pre-existing bug entries are filed in the change's commit, like nits; ship never runs
  `inbox-commit`.

## Open questions

- ~~Who decides a finding is pre-existing: the reviewer reading the diff, or a mechanical check that
  the cited line lies outside the diff's hunks (in `preflight`)?~~ Resolved: the reviewer, by the
  guide's definition, checkable through the `path:line` evidence (spec R4).
- ~~A pre-existing finding that is cheap and in a file the diff edits: offered as "fix it now", the
  way an S nit is, or always a bug entry?~~ Resolved: a bug entry by default; the person can still
  fix it in the change and answer `fixed`.
- ~~Is a disposition asked per finding in the WAIT, or recorded from what the person did ("fix a
  finding first", then a re-ship)? A fixed finding never reaches the commit unless ship remembers
  it across reruns.~~ Resolved: ship writes `findings.md` every run, a named exception like `base`,
  and a rerun marks what the diff no longer shows `fixed` (spec R6–R8).
- ~~Is a dismissed finding's reason kept anywhere but the count, as a commit body paragraph like
  `Retired nits:`?~~ Resolved: in `findings.md`, committed with the change.
- ~~Does retro report precision now, or only once enough trailers carry dispositions?~~ Resolved:
  now, beside `answered`, the changes whose trailers carry dispositions (spec R12–R13).
- ~~How do seeds -2 and -3 leave the register: deleted in the change's commit by ship, or does
  `idea:` take a list?~~ Resolved: deleted in this change's commit, a one-off; `idea:` stays
  single (spec R15).
