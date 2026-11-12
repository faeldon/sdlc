---
id: 049
slug: ship-recommends-fixes
tier: 2
impact: minor
stage: shipped
created: 2026-11-12
updated: 2026-11-12
shipped: 2026-11-12
idea: 2026-10-26-6
depends_on:
serves: [O3]
---

# 049 — Ship's question leads with its recommendation, and a recommended fix is one yes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Ship's WAIT question always ends `(yes / fix a finding first / edit the message)`, hard-coded in
`ship_question()` (`scripts/sdlc.py:6675`), pinned by three assertions in `tests/test_preflight.py`,
and asked exactly as the script prints it.

- **It doesn't say what ship recommends.** Step 3 has ship recommend fixing the nits that are cheap
  and worth it (cost S, value med), but that lives only in the session's prose: `findings.md` has no
  disposition for "fix before commit" (Important is `open` and blocks; a nit is `recorded` or
  `minor`), so the script can't name them. "Fix a finding first" really means "the ones I
  recommended", however many, and the question doesn't say which. It is offered even when nothing
  is recommended, as in 048.
- **Yes is the answer against the recommendation.** When ship recommends a fix, agreeing with it
  is the second option, the fix is a turn of its own, and ship asks all over again: three stops to
  take the recommendation. 048's `Sdlc-Totals` counted 8 stops against a target of 6.
- **A recommended fix counts as a miss.** `metrics.happy()` marks ship `no` whenever the person
  answers anything but yes (2026-10-26-6), so a ship that stopped for a finding its own review
  raised counts the same as a loop that circled. Ship went through first time in 5 of 12 Tier 2
  changes and 4 of 8 Tier 1 in the last window, and those numbers can't say which.

## Outcome

- `findings.md` records which findings ship recommends fixing now, each with the fix it proposes;
  `sdlc.py findings` lists them by id.
- With some recommended, `preflight --question` leads with them: `Fix F2 and F4, then commit this,
  … ? (yes / commit without fixing, recording F2 and F4 as nits / edit the message)`, the second
  option naming the disposition each takes unfixed. With none, `Commit this, … ? (yes / edit the
  message)`.
- A yes to a recommended fix: ship makes the fixes shown, reruns the gate and the review, and
  commits without asking again only when the gate passes, every recommended finding reads `fixed`,
  and nothing new is found; otherwise it stops and asks again.
- `Sdlc-Findings` counts those findings `fixed`. `happy()` counts a ship stopped only to fix its own
  review's findings apart from one rerun for any other reason, and ship's first-time rate counts
  only the second kind.
- **Moves O3:** a ship whose review recommends fixes stops its person once instead of three times,
  and the stops close records at ship drop for those changes.

## Affected

- **Area:** ship's review and WAIT, and the metrics close records.
- **Files & components:** `scripts/sdlc.py` (`ship_question()`, `cmd_ship_question()`,
  `preflight`, `findings_entries()`, `findings_trailer()`, `cmd_ship`'s refusal on an open
  finding), `skills/ship/SKILL.md` (Steps 3–6), `templates/findings.md`, `scripts/metrics.py`
  (`happy()` and whatever reads ship's replies), `guide/review.md` and/or `guide/process.md`,
  `docs/REFERENCE.md`, `AGENTS.md`, and `tests/test_preflight.py`, `tests/test_findings.py`,
  `tests/test_metrics.py`, `tests/test_skills.py`.
- **Downstream:** every host's `/sdlc:ship` and the person answering it; `findings.md` files in
  history, which retro's `_review_at()` and the factory's review read through pinned copies of the
  parsing; `Sdlc-Findings` and `Sdlc-Happy` trailers, which retro and `metrics_summary()` read.
- **Contracts:** a skill's WAIT step, what it approves and when (always Tier 2 here); the trailer
  contract (extend, never redefine); `templates/` is an irreversible path, so `How to recover:`;
  the factory's copies of the findings parsing are pinned to `sdlc.py`'s by test.

## Constraints

- No unseen code commits unchecked: a yes approves only a described fix, and the commit waits for
  the gate and the review on the fixed diff; any surprise stops for a new question.
- History reads as it does now: a `findings.md` or trailer without the new keys is never read as
  "nothing recommended" or as "first time".
- The script still words the question, never the skill; the `test_preflight` pins move to the new
  wordings rather than going.
- Ship never pushes, and still commits only after a yes.

## Open questions

- ~~How does `findings.md` mark a recommended fix: a new disposition, or a line beside it (`Fix: <the
  change>`)? What does it become on "commit without fixing": always `recorded`, or per finding?~~
  Resolved: `Disposition: fix` with a `Fix:` line; unfixed it becomes `recorded`, and only a nit
  can (spec R1, R2, R5)
- ~~Which findings qualify for a fix inside the yes: cost S only? Nits only, or an Important one with
  an obvious one-line fix too? May a fix touch files outside the change's diff?~~ Resolved: a fix of
  cost S within files the diff already changes, Important ones included; `fix all` covers the rest
  and asks again (spec R5–R7, R12)
- ~~Does the clean-rerun commit reuse the approved message exactly, but for the trailer's counts, or
  does any change to the message stop for a new question?~~ Resolved: reused but for the trailer;
  any other change asks again (spec R11)
- ~~How does `happy()` tell "stopped to fix its own findings" from another rerun: `findings.md`'s
  `fixed` entries, the reply's wording, or a marker ship writes? And how does a `Sdlc-Happy` trailer
  from before this read?~~ Resolved: `ship=fixed` from `fixed` entries, more than one ship run and
  no revise reply; old trailers read as before (spec R13, R14)
- ~~Does the factory's review, and its copies of the findings parsing, learn the new field here or
  later?~~ Resolved: the factory parses no findings.md, so nothing changes there
