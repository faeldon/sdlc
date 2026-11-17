---
id: 102
slug: sdlc-docstrings
tier: 1
impact: none
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-27
depends_on:
fixes: [2026-11-17-29]
serves: none
---

# 102 — Bring sdlc.py's docstrings up to date

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

AGENTS.md points at docstrings for each rule's detail, and some of `scripts/sdlc.py`'s are wrong:

- **2026-11-17-29:** `_drop_record()`'s docstring "ends 'Why not, or' (scripts/sdlc.py:4186), so a reader following AGENTS.md's pointers into close's docstrings meets half a rule."
- **2026-11-17-27:** "`sdlc.py`'s module docstring, `change_dirs()`, `next_id()`, `claim()` and `cmd_uninstall()` still name the change folder `work/` (its pre-1.4.0 name), and the module docstring lists about half the subcommands (no `base`, `resolve`, `preflight`, `findings`, `checks`, `accept`, `board`, `record`, `drift`, …)."

## Outcome

- `_drop_record()`'s docstring is whole.
- No docstring in `sdlc.py` calls the change folder `work/` except where it means the old `HISTORY_WORK`.
- The module docstring states the module's purpose and points at `--help` (or `sdlc.py -h`) for the subcommands, instead of a list that drifts; or it lists every subcommand, and a test pins the list to the parser.
- `./check.sh` passes; no behaviour changes.
- **Moves O5:** a session reading a docstring for a rule reads it right the first time.

## Affected

- **Area:** `scripts/sdlc.py`'s docstrings only.
- **Files & components:** `scripts/sdlc.py`; a test only if the list is kept.
- **Downstream:** sessions working on the plugin, following AGENTS.md's pointers.
- **Contracts:** none.

## Constraints

- Docstrings only: no code changes.

## Open questions

- ~~Cut the module docstring's subcommand list, or keep it complete and pinned by a test?~~ Resolved: cut; it states the module's purpose and points at `sdlc.py -h` (D1, the person).

## Approach

Finish `_drop_record()`'s sentence from `cmd_close()`'s drop path; replace `work/` with `.sdlc/work/` in the named docstrings; cut the module docstring to its purpose and a pointer to `-h` (the lower-cost answer to the open question).
