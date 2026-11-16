---
id: 068
slug: retro-module
tier: 2
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-04-10
depends_on:
serves: [O5]
---

# 068 — Move retro's history readers out of sdlc.py

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`scripts/sdlc.py` is 9,481 lines. At the 2026-11-04 retrospective it was 7,729, so it has grown by
1,752 in two weeks. 22 of the last 27 changes had to touch it, and it changed together with
`docs/REFERENCE.md` 19 times.

Its retro section runs from `retrospectives()` to `cmd_retro_commit()`, roughly 1,650 lines. It
holds `prose_metrics`, `doc_items`, `_evidence`, `metrics_summary`, `process_views`,
`render_report`, `retro_report`, `_rework`, `retro`, `_architecture`, `bugs_retro`, `_review_at`
and `register_drift`.

That code is read-only and called almost only by `retro` and `retro-commit`; `status` and
`release` read `retro_due` and `metrics_summary`. Yet every change to retro is reviewed inside the
whole file: the fresh reviewer and ship's own correctness pass search 9,500 lines to check a diff
that touches one concern. This window's Tier 2 ship stage took a median 9 agent minutes and read
9.6M cache tokens, and fresh reviews feel slow.

The 2026-11-04 retrospective proposed this split, and the 2026-11-17 one raised it to high as M14's
first step.

## Outcome

Retro's history readers live in `scripts/retro.py`. It is loaded by path, the way `metrics.py` and
`indicators.py` are, and is never imported as a module. `sdlc.py` keeps the walks it shares with
release and close: `closed_changes()`, `dropped_changes()` and `_change_base()`.

- `sdlc.py retro`, `retro --report` and `retro-commit` print and commit exactly what they do today.
  The existing retro, bugs and nits tests pass unchanged, apart from where they load each function
  from.
- `scripts/sdlc.py` shrinks by roughly the retro section's size, and `./check.sh` passes, the
  Windows-portable tests included.
- **Moves O5:** a change to retro reads `scripts/retro.py` and its tests rather than searching
  `sdlc.py`. The next Tier 2 changes to retro ship below this window's medians of 9.6M cache tokens
  and 9 agent minutes in ship. `sdlc.py` shrinks by retro's lines, and fewer of the next window's
  changes have to touch it.

## Affected

- **Area:** the retro loop's mechanism in `scripts/`.
- **Files & components:** `scripts/sdlc.py` (edited) and `scripts/retro.py` (new). The tests that
  reach retro's functions through `sdlc.`: `tests/test_retro.py` (15 references),
  `tests/test_bugs.py` (11), `tests/test_nits.py` (2) and `tests/test_windows.py` (1). The
  Architecture map in `AGENTS.md`, and the Retrospectives section of `docs/REFERENCE.md`.
- **Downstream:**
  - the retro skill, through `sdlc.py retro` and `retro-commit`, whose commands don't change;
  - `status` and `release`, through `retro_due` and the metrics summary;
  - hosts, which run the same commands from the plugin's cache, so the new file ships in the
    plugin's folder as `metrics.py` does.

  It waits on no open change and reworks none: the code was always meant to move once it grew.
- **Contracts:** load-by-path for the scripts; the Windows invariants; the guards against naming
  `main` in a git call and against a literal work path; `retro-commit`'s refusals; the PEP 723
  block.

## Constraints

- **Loaded by path, never imported.** `uv run --script` and the tests put different directories
  on `sys.path`, which is why `metrics.py` and `indicators.py` are loaded this way. `retro.py` must
  be found the same way from a host's cached copy.
- **The Windows invariants hold in the new file:** no top-level `fcntl` or `msvcrt`,
  `encoding="utf-8"` on every text `subprocess.run`, `newline="\n"` on every text write, and
  `as_posix()` on every repo path shown or compared.
- **The static guards cover `retro.py` too.** `test_no_git_call_names_main_itself` and
  `test_no_literal_work_path_in_the_script` must reach it, so the new file doesn't become a place
  those rules no longer reach.
- **`retro-commit`'s refusals stay exactly as strict.** It still commits only the direction doc,
  the register, the product doc and the report.
- **Output is unchanged.** The JSON's shape, the report's text and the commands' flags are a
  contract with the retro skill and with hosts.
- **The PEP 723 dependencies stay in `sdlc.py`'s block.** A second script that needs its own
  `uv run --script` header is a design decision, not a side effect.

## Open questions

- ~~How does `retro.py` reach the git calls and the shared walks?~~ Resolved: `sdlc.py` loads it by
  path and gives it a live view of its own globals as `retro.sdlc`, so retro calls `sdlc.<name>`
  and a test's stand-in reaches it; it isn't pure like `metrics.py` (spec R4, Design).
- ~~Do `retro_due` and `metrics_summary` stay in `sdlc.py`?~~ Resolved: `retro_due` stays with
  status's `next_up` and the doc readers; `metrics_summary` moves, since only retro calls it (R1,
  R2).
- ~~Should the tests reach retro's functions through a loaded `retro` module, or through `sdlc`
  re-exporting them?~~ Resolved: through `sdlc.retro.<name>`, with no re-export (R7).
- ~~Do `bugs_retro` and `_review_at` belong with retro?~~ Resolved: yes; only `retro()` calls them,
  and `/sdlc:bug` and triage use `bug_entries` and `cmd_bugs`, which stay (R1).
- ~~Does the guard in `tests/test_windows.py` find a new file by glob?~~ Resolved: no, by a list;
  it and the three guards that read only `sdlc.py` are extended (R6).
