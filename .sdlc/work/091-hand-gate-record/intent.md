---
id: 091
slug: hand-gate-record
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on: [087]
reworks: [080]
serves: [O3]
---

# 091 — A gate run by hand leaves a record the board and status read

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A change built by hand has no record of its gate. On 2026-11-17, 087 was built and `./check.sh`
passed (1,877 tests, 39 s), but the board kept its card in **Build** until someone set `stage: test`
by hand: 080's inference moves a manual card to Test only once ship's review has written
`findings.md`, and the gate leaves nothing in the folder to read. Only the factory's `factory.py
gate` writes a record (`build/round-<N>.gate.md`: its verdict, the build hash it judged, its exit,
its output's tail). So "built, gate green, waiting for ship" isn't a state the board or
`/sdlc:status` can show for a change built by hand, and the person asks. The same gap leaves 088's
progress indicator with no gate step for one.

## Outcome

- **Moves O3:** a change built by hand shows "built, gate green" on the board once its gate passes,
  so the person sees it's ready to ship without asking.
- An `sdlc.py` command runs the base branch's `commands.check` for a change, from its checkout, and
  writes the attempt into the change's folder in the factory's record shape: verdict, command, a
  hash of the build it judged, exit, seconds, whether the tree changed, and the output's tail with
  087's placeholders. A test pins the shape and the placeholder logic to `factory.py`'s.
- The board reads it: a manual change whose latest record is green on the build as it now stands
  shows in **Test** (or wherever 086 and 088 settle it) with `/sdlc:ship` next; a record whose build
  has since changed counts for nothing, so a later edit sends the card back to Build. Pinned by
  tests.
- `/sdlc:status`'s line says the gate is green (or red) for such a change; pinned by a test.
- `./check.sh` passes.

## Affected

- **Area:** the gate for a change built by hand, and the board and status that read it.
- **Files & components:** `scripts/sdlc.py` (the new command, its record reader, status's line),
  `scripts/board.py` (`_seen()`, `next_action()`, `column()`), tests in `tests/test_sdlc.py` or
  `tests/test_board.py`, perhaps `skills/ship/SKILL.md` (if ship's Step 1 runs the gate through it,
  so its record lands with the change), and `docs/REFERENCE.md`.
- **Downstream:** the board and `/sdlc:status`; `/sdlc:ship`, which commits the change's folder,
  the record included; close's `measure`, if it should count hand gates as it counts `gate_fail`;
  088's progress indicator; hosts, which get the command.
- **Contracts:** the command writes, so it's never in `ALLOW_RULES` or a skill's `allowed-tools`
  unasked, and a skill that runs it names it; *the scripts run on Windows*; the factory's copies
  pinned by test, here the other way round (the core copying the factory's record shape); *nothing
  about a project or a workspace*; the metrics trailer contract, if a hand gate is counted.

## Constraints

- The board still writes nothing and never runs a command: only the person's command writes the
  record.
- A record says nothing of a build it didn't judge: the hash ties it to exactly what was gated.
- The factory's gate record and this one never disagree in shape, so 088 and the board read both
  alike.
- Nothing about a factory change's gate changes.

## Open questions

- ~~Where does the record live, and how is a hand build hashed: `build/gate.md`, and a hash of the
  branch's diff against the base plus the uncommitted tree outside the change's own folder, or
  `build/round-1.gate.md` reused?~~ Resolved: `build/gate.md`; the hash is the merge-base plus the
  contents of every path the branch touched, committed, uncommitted and untracked, outside the
  change's folder (spec R3, R6).
- ~~Does `/sdlc:ship`'s Step 1 run the gate through this command, so the record always lands with the
  change, or is it the person's step after building?~~ Resolved: the person's step; ship's Step 1
  is unchanged, since the command writes and would prompt on every ship (R13).
- ~~A column state "built, gate green", apart from Test, which 080 gave "ship's review has run", or
  is Test it?~~ Resolved: Test, with a `gate green` badge (R8, R10).
- ~~Does close's `measure` count hand gates (`Sdlc-*`), or stay factory-only?~~ Resolved: no new
  trailer; `metrics.py` counts a run of `sdlc.py gate` as a `check` event, as it does
  `commands.check` (R12).
