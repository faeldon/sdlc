---
id: 048
slug: architecture-indicators
tier: 2
impact: minor
stage: shipped
created: 2026-11-12
updated: 2026-11-12
shipped: 2026-11-12
idea: 2026-10-24-5
depends_on:
serves: [O4]
---

# 048 — Architecture indicators for the retro loop

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Retro's architecture pass has almost nothing measured to go on. `sdlc.py retro` gives it the
skills' sizes (`prose.skills`) and `rework_common`, the files later changes touched again; the rest
of the pass is a reading of the code. A finding like "`scripts/sdlc.py` does too many jobs" (M9's
2026-11-04-10, moving retro's history readers out of it) rests on that reading, not on evidence of
where changes land and what grows.

And the growth it should catch goes unmeasured. `scripts/sdlc.py` is 8,261 lines and touched by
nearly every change, `scripts/metrics.py` 1,107; the suite and `./check.sh`'s runtime keep growing.
No retrospective has said how fast or where, so the decision to split a file or trim the gate comes
once it already hurts. The last direction doc dropped `tests/test_skills.py` and `.sdlc/setup.json`
as "shared by design", which may be right, but nothing set beside them the files the code shares by
accident.

## Outcome

- `sdlc.py retro` reports, for the window since the last retrospective and computed from git alone
  in any host:
  - **code per change**: lines and files added, changed and deleted per closed change, by tier, and
    split code against tests against docs;
  - **churn hotspots**: the files most changes touch, weighted by size;
  - **co-change**: files that change together;
  - **largest files**: the largest, and how each grew since the last retrospective;
  - **suite and gate**: the test suite's size, and the gate's runtime where it can be read, each
    against the last retrospective.
- A host can name a command for language-specific measures (complexity, dependency cycles), run
  by `retro` the way `retro.evidence` is; with none named, nothing runs.
- `/sdlc:retro`'s architecture pass reads them: each architecture finding cites the indicator behind
  it, and a split is proposed when a hotspot or a growing file says so, not only on a reading.
- **Moves O4:** the next retrospective's architecture findings cite numbers rather than a reading
  of the code, and growth (largest files, the suite, the gate) is a trend against the last
  retrospective that the direction doc can set a goal on.

## Affected

- **Area:** the retro loop: `sdlc.py retro` and the `/sdlc:retro` skill.
- **Files & components:** `scripts/sdlc.py` (`retro()` and its helpers, `load_config()` for the new
  key), `skills/retro/SKILL.md` (the architecture pass), `docs/REFERENCE.md` (the key and the new
  `retro` fields), `guide/process.md` (the retro loop's list of what it counts), probably
  `defaults/config.toml` (the key, commented off), and tests.
- **Downstream:** every host that runs `/sdlc:retro` reads the new fields through the skill; a host
  that sets the new key has its command run by `retro`. Nothing else reads retro's output: release,
  publish and close never do.
- **Contracts:** `retro` stays read-only but for the host's commands, and `_evidence()` is the only
  place one runs today, so the new command goes through it or is named beside it. A new config key
  whose default keeps today's behaviour is additive. `defaults/` is an irreversible path under
  `[review]`, and an edit there reruns `sdlc.py record` so `drift` stays clean.

## Constraints

- Any host, from git alone: no language, build tool or test runner is assumed; whatever needs one
  comes through the host's command.
- `retro`'s output must not grow back toward the 112 KB the last retrospective dropped (M9,
  2026-10-26-8): the indicators are summaries (top N, totals, against-last), never a row per file.
- Retro never runs the gate to time it.
- Out of scope, and kept in the register as a seed of their own: verbosity against complexity,
  per-call tool counts, and the suite's pruning pass. `sdlc.py ship` deletes 2026-10-24-5 when this
  ships, so they need their own seed before then.

## Open questions

- ~~Is co-change worth its cost in a window of a handful of changes (about 7 since 2026-11-04), or
  does it need a longer look-back than the retrospective's boundary?~~ Resolved: hotspots and
  co-change read the last 30 closed changes, past the boundary (spec R5, R6)
- ~~Where can the gate's runtime be read without running it? Nothing records it today: a new trailer
  close writes, the host's command, or left out.~~ Resolved: only from the host's command; git
  gives the suite's size (spec R8, R9)
- ~~How are code, tests and docs told apart in a host the plugin knows nothing about: path
  conventions, a config key, or the host's command?~~ Resolved: path conventions, replaced per kind
  by `retro.test_paths` and `retro.doc_paths` (spec R3)
- ~~Does the new key sit under `[retro]` beside `evidence`, and is it one command or a list?~~
  Resolved: `retro.indicators`, a list, run through `_evidence()` (spec R9)
- ~~Does the new code go into `scripts/sdlc.py`, or wait for 2026-11-04-10 to move retro into a file
  of its own, so this change doesn't grow the hotspot it sets out to measure?~~ Resolved: a new
  `scripts/indicators.py`, loaded by path; `sdlc.py` makes only the git calls (spec R11)
