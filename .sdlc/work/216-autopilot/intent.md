---
id: 216
slug: autopilot
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T11:56Z
updated: 2026-11-21
shipped: 2026-11-21
idea: 2026-11-21-32
depends_on:
serves: [O6]
origin: self
---

# 216 — Autopilot: the factory runs from seed to landing while the person is away

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Today every factory change waits on its person several times: `/sdlc:intent`'s yes, the build's
yes, each escalated default or look in `/sdlc-factory:decide`, and the landing's yes. Each wait is
right when the person is at the keyboard and the reason a change sits idle when they aren't. This
session alone opened, built and landed eleven changes (206 to 215), and each paused at those gates
for the person to come back, while the register held more seeds the factory could have taken. The
person wants a mode for when they're asleep or away, in their words: no wait conditions, the
supervisor picking from the register, building as soon as dependencies land, landing in batches,
and pushing escalations through on their defaults, with every such call written down for review
later.

What it must not do is just as clear from the seed. It never loosens the waits by hand or in the
factory's own mode; it never counts its own calls as the person's; it never lands a change that
could only be built by breaking a contract, a hard rule or a guard; and it can't run unbounded,
in dollars, hours, the calls it piles up for review, or the risk it lands.

## Outcome

- `/sdlc-factory:autopilot` asks one WAIT, which bounds the run (which seeds or themes, a dollar
  cap, hours, the level), then starts `factory.py autopilot --run` in the background on the landing
  train's model. The script is the scheduler: the queue, the waves, dependencies, the budgets, the
  off switch and the run's state in the git common dir, so a stopped or compacted session loses
  nothing and a rerun resumes it. Each judgment goes to a fresh agent session with no Write, its
  reply filed by the script: which wave is next, an intent's draft, the answer to an escalation.
- It picks compelling seeds (bugs by severity, `Priority: high`, the product doc's outcomes),
  groups them into waves that won't overlap, opens their intents, builds each as soon as what it
  depends on has landed, and lands what is ready in batches, waiting for a nearly-ready change when
  landing them together saves runs and cases.
- No WAIT stops it: an escalated default is taken as the default and a look as seen, recorded as
  `by=autopilot` and `→ decided by autopilot:`, never as the person's, each with its context in an
  escalations file the person reviews later. A call the person disagrees with is fixed forward,
  by a revert or a new seed, never mid-build.
- A change that can only be built by breaking a contract, a hard rule or a guard, or one the
  supervisor judges far simpler if a contract were relaxed, stays under Needs you, unlanded, and
  nothing that depends on it is built.
- Two risk budgets, counted by the script from signals it already detects and never judged by a
  model, weights and limits in the base branch's `.sdlc/factory.toml`: review debt (its unreviewed
  calls, weighted by kind) and change risk (each landed change's `land-check` signals, weighed more
  pushed than local and stacked than not). Reaching either starts nothing new and leaves what is in
  flight at `stage: test`.
- It stops when no compelling seed is left, its dollar cap, hours or a risk budget run out, or the
  person turns it off (between steps, as `train --cancel` does), and writes a summary: how long it
  ran and what it cost, what landed, what is mid-build and where, every escalation and decision,
  each budget and what spent it, and the risks to weigh.
- Autopilot loosens no other WAIT: `--by autopilot` is accepted only while its run lock is held,
  no skill but autopilot's names it (a test pins this), and it adds no `allowed-tools` rule that
  lets another skill's writing command run unasked. `by=person`, `by=auto` and `by=autopilot`
  stay three values.
- **Moves O6:** the factory takes work forward while the person is away, its stops for the
  person shrink to the contract-breaking ones, and every call it made is on record to check.

## Affected

- **Area:** the factory, end to end; core's records of who decided.
- **Files & components:** `plugins/factory/scripts/factory.py` (a new `autopilot` command, its
  state and run lock, beside `cmd_train()` and `_run_loop()`) and `landing.py`; a new
  `plugins/factory/skills/autopilot/`; new judging agents under `plugins/factory/agents/`;
  `plugins/factory/README.md`; `scripts/sdlc.py` where `new`, the trailers and `parse_trailers`
  meet `by=autopilot`; `scripts/metrics.py` and `retro.py`, which count who decided; AGENTS.md,
  REFERENCE.md and FEATURES.md; `tests/test_skills.py` and the factory's tests.
- **Downstream:** every host with the factory enabled; the retrospective, which must count
  autopilot's calls apart from the person's; the board (2026-11-21-34 waits on this).
- **Contracts:** one WAIT per writing skill, and approval per invocation; *Only the named steps
  push*; *Narrow `allowed-tools`*; `Sdlc-Landed` (`by=person`, `by=auto`); intake (`new` opening
  issues); *Writes before a WAIT*; `land.auto`; `[review] sensitive` read from the base branch.

## Constraints

- No other skill's WAIT changes, by hand or in the factory's own mode.
- Autopilot's calls are never recorded as the person's.
- Every budget and weight is read from the base branch, so a change can't loosen the run it's in.
- Nothing names a host or the author's machine, in the run's records or its summary.

## Open questions

- ~~Is this one change, or a short batch its spec lays out (run record and `by=autopilot`; the
  scheduler; escalations and summary; risk budgets)?~~ Resolved: one change, its spec in four
  parts A–D, approved whole
- ~~The commands the harness asks before today (`accept`, `cases`): allowed for the run, or
  skipped?~~ Resolved: `accept` only when every check is read-only; cases never run, and a change
  with either is held (spec R19, R21)
- ~~Does it push and sync issues, or land locally until the person reads the summary?~~ Resolved:
  pushes as `git.push` says, a pushed landing weighed double; no `sync` (spec Design, R26)
- ~~A script-drawn line for "breaks a contract": AGENTS.md, the invariant tests, a *Contracts
  touched* line?~~ Resolved: `[autopilot] guards` paths, `- CONTRACT:`/`- RELAX:` reply lines, and
  an approver's reconsider or gate reason (spec R19, R20)
- ~~An intent opened by `new` with no person's yes: what does its record say?~~ Resolved:
  `opened_by: autopilot` in its frontmatter, the call in `runs/autopilot.md` (spec R12)
- ~~The risk weights and default limits, and how the retrospective checks them later.~~ Resolved:
  debt and risk weights and limits as spec R24–R26 set them, from the base branch; the
  retrospective's overturn rate is left for a later seed
