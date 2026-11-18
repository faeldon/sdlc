---
id: 145
slug: escalations-that-clear
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-47, 2026-11-18-49, 2026-11-18-50]
depends_on: [139, 141]
serves: [O6]
---

# 145 — An escalation the person has dealt with clears without a rebuild

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

When the approver escalates a change, the board and `status` put it in Needs you ("read the
escalation"), and it stays there until a new approver run decides again. Only one kind of
escalation can be cleared without a rebuild today: an open decision or default, which
`/sdlc-factory:decide` records in the ledger (143, 2026-11-18, moved to Ready to ship once D1 was
answered). Any other reason has no way to clear.

On 2026-11-18, 140's approver escalated it for a red `test_nothing_local`, set off by its own
behaviour record. The record was fixed by hand and the test passed, but 140 stayed in Needs you,
its `decision.md` still reading ESCALATE. The only way to Ready was `/sdlc-factory:build 140`, a
whole new round, to change a column. The board can't tell an escalation dealt with from one that
isn't.

The columns themselves mix two ideas (`scripts/board.html`'s `COLUMNS`, `board.py`'s `column()`
and `_seen()`). Plan, Design and Build name a stage of the work; Test and Ready to ship name one
tool's handoff. Test holds, in practice, only a hand-built change being shipped (ship's review
written, or a hand gate green), since a factory change at `test` has a decision and goes to Ready
to ship; Ready to ship holds only factory changes, since a hand change goes from Test straight to
shipped. Ready to close holds both a hand-shipped change waiting on close and a factory landing in
flight. In the person's words (2026-11-18): "test, I believe, is when a manual change is actually
shipping or ready to ship. Ready to ship right now is just for the factory."

A landing shows no progress either. During the first train (140–143, 2026-11-18), 141, 142 and
143 read `ship` as their current step for twelve minutes while they were only waiting to be
stacked on 140, and no card had a bar: a build's card shows elapsed time against the typical
duration of its step (`typical_times()`), but landing steps have no recorded history, so `typical`
is empty. In the person's words: "Should there be a progress bar for the landing, in particular
143, since it's running its cases? … right now it's trying to resolve conflicts so there's really
no indicator."

## Outcome

- The approver's ESCALATE reasons are items the script reads, each of a kind that says how it
  clears: a decision or default, by its answer in `decide` (as now); a red gate or failing check,
  by a green `sdlc.py gate NNN` on the change as it stands; a "look at this" item, by the person's
  acknowledgement in `decide`, recorded in the ledger.
- A change whose every reason is cleared moves to Ready to ship on the board and leaves "What needs
  me" in `status`. A test escalates a change for a red gate, records a green `sdlc.py gate` on its
  fixed tree, and finds it Ready.
- `decision.md` is never rewritten. The landing question still shows each escalation and how it
  was cleared, and `measure` still tells the approver's call from the person's.
- The board's columns name the state of the work, the same for a change built by hand or by the
  factory: **Planned** (intent, nothing built), **Designing** (a Tier 2's spec), **Building** (code
  being written, by hand or in the factory's rounds), **Ready** (built and checked, nothing
  committed: a factory decision READY or cleared, or a hand change whose gate passed and whose
  review is written), **Landing** (committed and on its way to the base branch: shipped and waiting
  on close, or a factory landing or train in flight), and **Needs you**. Test merges into Ready;
  Ready to ship and Ready to close become Ready and Landing. The card's `next:` line still names
  the command for its tool. A test places a hand change and a factory change at each state and
  finds both in the same column.
- A landing card shows its progress as a build's does: elapsed time against the typical duration
  of its current step, from past landings' recorded steps. A step with no history yet, or one that
  is open-ended (a conflict resolution, a paid case run), shows its elapsed time and that it's
  running, never a made-up percentage. A change in a train shows `k of n`, and one waiting its
  turn says what it waits on (`waiting to stack on 140`), never its last finished step. A test
  gives the board a train of three with one stacking and two waiting, and finds each card's step,
  place and wait as said.
- **Moves O6:** a factory change stops the person only for what still needs them; an escalation
  they've dealt with stops being shown as theirs.

## Affected

`plugins/factory/agents/approver.md` (how it words its reasons, so their kind is readable),
`plugins/factory/scripts/factory.py` (`read_decision()`, `ask`, `land-check`'s signals and
`shown`), `plugins/factory/skills/decide/SKILL.md` (acknowledgement items), `scripts/sdlc.py`
(`needs_of()`, the hand gate's record), `scripts/board.py` (`column()`, `_seen()`) and
`scripts/board.html` (`COLUMNS`), `tests/test_board.py`, and the three places `docs/REFERENCE.md`
names the columns. Every host's board, factory or not, and every factory host's status and
landing. It waits on 139, which rewrites the landing's question and signals,
and 141, which rewrites the board's columns for a stopped landing.

## Constraints

- The approver's decision is never edited or replaced; what the person did is recorded beside it,
  in the ledger or the gate record.
- Clearing an escalation never lands anything by itself: the landing still asks, and shows how each
  reason was cleared.
- A gate clears a red-gate reason only on the change as it stands; a later edit makes it stale.
- Only the person acknowledges a "look at this" item, never an agent.

## Open questions

- ~~How does the approver mark each reason's kind: a line per reason, as `- ESCALATED:` is today,
  with a kind?~~ Resolved: one line per reason, `D<n>`, `gate:` or `look:` (spec R1, R2).
- ~~Which reasons can a green gate clear: a red gate only, or any failing test the reviewers named?~~
  Resolved: only those the approver marks `gate`, which the check would show fixed (spec R1, R8).
- ~~Does an acknowledged item need words (what the person checked), or is a plain "seen" enough?~~
  Resolved: `seen` is enough; typed words are kept (spec R12).
- ~~Does a change cleared this way still count as escalated in `measure` and retro's figures? It
  probably should: the approver's call stands.~~ Resolved: yes, `decision.md` is never rewritten
  (spec R14).
- ~~Does `status` group its sections by the same five states, so the board and `status` use one
  vocabulary?~~ Deferred: a seed of its own (2026-11-18), since it reshapes `status` for every host.
- ~~Where do a landing step's durations come from: `runs/land-step.md`'s since-times in landed
  changes' history, read as `typical_times()` reads a build's, or new records?~~ Resolved: a new
  `runs/land-times.jsonl` record (spec R19, R20).
