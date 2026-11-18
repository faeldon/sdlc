---
id: 150
slug: pay-down-batch-nits
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-53, 2026-11-18-54, 2026-11-18-55, 2026-11-18-57]
depends_on: [145]
serves: none
---

# 150 — Pay down the nits and loose ends this batch left

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The 2026-11-18 batch (140–147) left four seeds and nine nits, each small enough that a change of
its own would cost more than the fix. The seeds: -53, "`AGENTS.md` has other lines past 100 columns
(12, 29, 34, the *Writes before a WAIT* paragraph at 109-110, 223, 232-233, 238, 255, 276, 314)";
-54, "`test_a_server_that_fails_on_its_own_is_started_once` docstring cites "111 C1", another
review-only label no reader can resolve"; -55, "`reviewer-code.md:94` and `reviewer-ux.md:67`, the
`supersedes` sentence, are single long lines"; -57, a hand-built change that touches `[ui] paths`
ships with `UI review: skipped`, since ship uses only screenshots `factory.py shots` left and
nothing tells the person to take them (the person, 2026-11-18: "fold -57 into 150 as a pointer").
The nits the reviewers raised on 140–144: two docs
lines in ship's pass files, the `replies[-1]` fallback, `stop_text`'s types, `needs_of`'s
hand-built `reading`, the "unverified" test's single assert, `_own_folder`'s backtracking, an
over-long README line, and quoted `.sdlc/terms.local` terms.

## Outcome

- Each seed and nit is fixed, and `/sdlc:ship` retires the nits and close the seeds.
- `./check.sh` passes, and no line touched runs past 100 columns.
- For -57, `preflight`'s `passes.ui.why`, with `sdlc-factory` enabled and no screenshots, names
  the command that takes them (`factory.py shots NNN`); ship never runs it. A test reads that line.
- For -72, a test files a reply quoting a term from a fixture `terms.local` and finds it written as
  a placeholder.

## Affected

AGENTS.md, `plugins/factory/agents/reviewer-code.md` and `reviewer-ux.md`,
`plugins/factory/README.md`, `plugins/factory/scripts/factory.py`, `scripts/sdlc.py` (`needs_of`'s
caller in `status`), `skills/ship/behaviour.md`, `security.md` and `ui.md`, `tests/test_factory.py`, and for -57
`scripts/sdlc.py`'s `_passes_report()` and `tests/test_sdlc.py`.
No behaviour changes but -72's. It waits on 145, which rewrites `needs_of`.

## Constraints

- No rewording beyond what each entry asks; AGENTS.md's reflow changes line breaks only.
- -57 is a pointer only: ship never starts a server or takes a screenshot itself.
- -72 reads `terms.local` from the main checkout, as `test_nothing_local` does, and never quotes a
  term in what it prints.

## Open questions

- For -72, does the placeholder name the term's kind, or is a generic `<term>` enough?

## Approach

Reflow AGENTS.md (-53) and wrap the two agents' sentences (-55); replace "111 C1" with the rule it
pins (-54); in `_passes_report()`, when the factory is enabled and a UI pass has no shots, end its
`why` with the `factory.py shots NNN` command, and say the same in `skills/ship/ui.md` (-57). Nits taken in: 2026-11-18-56 (also assert `next == "rework"`), 2026-11-18-58 ("a factory
run, whose own reviewers ran", in the three pass files), 2026-11-18-59 ("a deep diff"),
2026-11-18-48 (a comment on `replies[-1]`), 2026-11-18-51 (`list[str] | tuple = ()`), 2026-11-18-52
(a comment, or build the `reading` through `needs_of`'s own reader), 2026-11-18-62 (tighten
`_own_folder`'s lookahead so `*` can't be backtracked off), 2026-11-18-63 (rewrap the README
paragraph), 2026-11-18-72 (`_defused()` also reads the main checkout's `terms.local` and writes each
match as a placeholder; `sdlc.py`'s copy the same, pinned).
