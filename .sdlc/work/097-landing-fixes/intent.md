---
id: 097
slug: landing-fixes
tier: 2
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
fixes: [2026-11-17-31, 2026-11-17-32, 2026-11-17-33, 2026-11-17-34]
serves: [O3, O6]
---

# 097 — Fix four bugs in the factory's landing

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Four bugs in the factory's landing (`plugins/factory/scripts/factory.py`), all hit on 2026-11-17:

- **2026-11-17-31:** "`cmd_land_close()` reads `git status --porcelain` through `_git()`, which strips its output, so the first line loses its leading space: ` M .sdlc/work/NNN-slug/runs/costs.jsonl` is read as `sdlc/work/…`, outside the change's folder, and the close is refused." Worked around four times that day by staging the folder first.
- **2026-11-17-32:** "`factory.py land` runs `sdlc.py ship` without the skill's nit step, and `inbox-commit` refuses to remove a nit at all (`RETIRE_REASONS["nit"]` is empty)." 094 took in nit 2026-11-17-11, landed, and left it open.
- **2026-11-17-33:** a landing's record (`build/land-<n>.gate.md`, `reviews/land-<n>/`, `runs/land-resolved`) stays uncommitted until `land --close`, so when `main` moves before the close a second `land` is refused ("has commits of its own and uncommitted work, so it can't rebase"); 095's record was amended by hand.
- **2026-11-17-34:** 095's conflict resolved by `sdlc.py resolve` before its build let its first batch pass itself, while the resolution its builder made at landing made the next ask. "A resolution the reviewers never saw should count, one they reviewed need not."

## Outcome

- `land --close` reads the porcelain status unstripped (or `-z`), and a test with a modified (` M`) first path in the change's folder closes.
- A landing retires the nits the change's intent or spec names by id, as `/sdlc:ship` does: they leave the register in the change's commit, with a `Retired nits:` paragraph; a test lands a change that took one in.
- `land` amends the landing's own record into the change's commit before it rebases, so a second `land` after `main` moved rebases; a test runs two landings with `main` moving between.
- `land-check` counts a resolution as a signal exactly when no reviewer saw it, read from the change's files, and its tests pin both cases.
- **Moves O6:** a factory change lands without a person repairing the landing by hand.
- **Moves O3:** none of the four hand steps of 2026-11-17 is needed.

## Affected

- **Area:** sdlc-factory's landing.
- **Files & components:** `plugins/factory/scripts/factory.py` (`cmd_land_close()`, `cmd_land()`, `land-check`), `tests/test_land.py`; `scripts/sdlc.py` only if retiring a nit needs `ship` to take the ids.
- **Downstream:** every `/sdlc-factory:land`; the `Close` commit's trailers.
- **Contracts:** landing commits only through `sdlc`'s own `ship`, `base` and `close`; `factory.py` never imports `sdlc.py`; `Sdlc-Landed: by=auto` only when no change carries a signal.

## Constraints

- A landing still never forces, never merges `main` into a branch, never stashes.
- A nit is retired only when the change names it by id; never inferred from the diff.

## Open questions

- ~~Does 2026-11-17-34 change when the landing asks (a WAIT's "when", which the process doc makes Tier 2)? If so, promote this change or split 34 off.~~ Resolved: yes; 097 was promoted to Tier 2 (D1, the person) and its spec covers all four bugs. A reviewed landing resolution closes in the same batch, behind `land --close`'s guard; the false signal of spec R13 is accepted (the person, at the run's question).
- ~~Retire nits through `sdlc.py ship` (a `--retire` flag) or in `factory.py` before it calls ship?~~ Resolved: in `factory.py`, after ship succeeds and before the commit; a nit counts as named only in the intent's Approach or the spec's Requirements (spec R6–R9; the narrowing, the person).

## Approach

Fix the parse in `cmd_land_close()`; amend the record before `base` in `cmd_land()`; read the nit ids from the intent's Approach and the spec, and retire them in the commit as ship does; define the signal in `land-check` from `conflicts.md` and the land reviews. One test per bug in `tests/test_land.py`.
