---
id: 039
slug: factory-evidence-and-replay
tier: 2
impact: minor
stage: shipped
created: 2026-11-04
updated: 2026-11-04
shipped: 2026-11-04
idea: 2026-11-03-12
depends_on:
serves: [O2]
---

# 039 — The factory proves its builds, replays its reviewers, and reviews old code

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The factory's agents report and review on their own word, and only ever the change in front of
them:

- **The builder says it's done; nothing shows it.** Its round report
  (`plugins/factory/agents/builder.md`, "What you return") lists slices, tests and "the gate's
  result" in prose it wrote. Nothing carries the commands it ran or what they printed, so a report
  can claim a green gate that never ran. The post puts showing the output, rather than saying it's
  done, at two to three times better results. No agent runs the change end to end either: the test
  reviewer reads tests, and the change's `checks.md` first runs at `/sdlc:ship`, after every round.
- **A change to a reviewer's prompt or model is a guess.** 037 traces each escaped bug to the
  change that let it in, and that change's diff is in history, but nothing replays the factory's
  reviewers on those diffs to ask whether they'd catch the bug now. A prompt edit or a model swap
  in `factory.toml` can make review worse unseen.
- **Old code is reviewed only when a change trips on it.** 038's `PREEXISTING` lines catch problems
  next to a change, nothing more. Code no change touches, often the paths `[review] sensitive`
  names, is never reviewed until a bug is filed against it.

This takes in seeds 2026-11-03-12, -13 and -14 together, the rest of phase 4.

## Outcome

- Each builder round report carries every command it ran and the tail of its output, and
  `factory.py` refuses a report that claims a gate result without one.
- A behaviour check, a new read-only role apart from the test reviewer, runs each round: the
  change's `checks.md` and the end-to-end path the spec describes, returning what ran and what it
  printed; a failure is a `CHANGE:` like any other, through the verifier.
- Seed 2026-11-03-12 leaves the register when this ships.
- Left for the next change (split at the spec): `factory.py eval` listing the diffs that introduced
  the register's bugs, with a skill replaying the reviewers on each (-13); and an optional factory
  skill reviewing code no change touches, proposing `[bug]` entries behind one WAIT (-14). Their
  agreed designs are written on those seeds at ship.
- **Moves O2:** no change the factory builds reaches a host with work it claimed but didn't do: a
  report's gate result and its checks are shown run, never said.

## Affected

- **Area:** the optional `sdlc-factory` plugin.
- **Files & components:** `plugins/factory/agents/builder.md`, a new behaviour-check agent,
  `plugins/factory/scripts/factory.py` (the report check, the loop's new role, `eval`),
  `plugins/factory/skills/build/SKILL.md`, two new factory skills (eval, the scheduled review),
  `plugins/factory/README.md`, `AGENTS.md`, `docs/REFERENCE.md`, perhaps `scripts/sdlc.py` (what
  eval and the scheduled review read of bugs and history), the factory's and skills' tests.
- **Downstream:** hosts that install `sdlc-factory`; hosts without it see nothing. A host's inbox
  gains `[bug]` entries only through the new skill's WAIT.
- **Contracts:** agents that judge have no `Write`, only the builder edits, nothing commits; one
  WAIT in each skill that writes, narrow `allowed-tools`; the factory's cached copy has no
  `sdlc.py`, so it can't call `inbox-commit` or `retro`; `inbox-commit` is the only code that
  commits the inbox on its own; bugs are filed the way `/sdlc:bug` files them; `accept` is never in
  a skill's `allowed-tools` (`test_no_skill_lets_accept_run_unasked`).

## Constraints

- The behaviour check runs `checks.md` without a person seeing the commands first, which `accept`
  exists to prevent: an agent may have written them. How it runs them must keep that guarantee.
- Nothing the eval or the scheduled review does writes code or commits; the review's bugs reach the
  register through the path `/sdlc:bug` uses, never a second one.
- A replayed diff runs where it can't touch the host's working tree.

## Open questions

- ~~The behaviour check and `accept`: does it run `checks.md` itself (so the build skill must show
  the commands at its WAIT), or only report what `accept` would run, leaving the run to ship?~~
  Resolved: it reads and reports, never runs; ship's `accept` runs them (spec R3).
- ~~How eval replays an old diff: a scratch worktree at the introducing commit's parent with the
  change applied (`git worktree add`), or reviewers given the diff as text? And who scores
  "caught": a match against the bug's `Paths:`, or a judging agent?~~ Resolved for the next
  change: the diff as text with `git show`, caught by path, shown for the person (spec R8).
- ~~How the scheduled review files bugs when the factory's cached copy has no `sdlc.py`: hand its
  proposals to `/sdlc:bug`, write a file `/sdlc:bug` reads, or a narrow `factory.py` write of its
  own?~~ Resolved for the next change: a report `/sdlc:bug` files through `inbox-commit` (spec R8).
- ~~"Scheduled": run only when the person asks, or offered through the harness's routines
  (`/schedule`)? Never unattended past its WAIT.~~ Resolved for the next change: run when asked,
  `/schedule` shown in the README (spec R8).
- ~~Is this one change, or should eval and the scheduled review (both new skills) split from the
  builder's evidence once the spec shows the design?~~ Resolved: split; this change builds -12
  only, the person's call (spec R8).
