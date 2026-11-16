---
id: 062
slug: backlog-readiness-and-themes
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 062 — Readiness groups for the backlog, and taking a theme as one change · plan

## Context

Status's Next up ranks 27 candidates without saying which are ready to build and which need the
person's decision, and `idea:` names one seed, so a change built for a theme's ideas leaves all but
one in the register. Spec R1–R10: split Next up into `Ready to build` / `Needs a decision`
(inferred from each item's rule), print a take-the-theme command in `status --all`, and let
`idea:` name several seeds, read by every reader and deleted by ship.

## Files to change

- **`scripts/sdlc.py`**: `READY_RULES`; `next_up()` sets each item's `group` and reads every open
  and closed change's `ideas`; `_next_themes()` gives a theme with 2+ ideas its `command`; status
  prints the two groups and `--all`'s theme command; `intent_ideas()`, `ideas` on `load_change()`
  and `_change_record()`; `check`'s orphan link, `cmd_ship`'s seed deletion,
  `_milestone_verdicts()` and `_open_claims()` read `ideas`.
- **`skills/intent/SKILL.md`**: several ids as the argument; `idea: [a, b]` shown and written;
  each entry tagged `[building]`.
- **`skills/status/SKILL.md`**: the two groups, the theme command, precedence rule 9.
- **Docs**: `AGENTS.md` inbox paragraph, `docs/REFERENCE.md`.
- **Tests**: `test_next_up.py` (R1–R3, R6), `test_sdlc.py` (R4, R5), `test_bugs.py` (R6),
  `test_skills.py` (R7, R8).

## Work order

1. `intent_ideas`, records, readers + tests. 2. Ship's multi-seed deletion + test. 3. Groups,
printing, theme command + tests. 4. Skills, docs, `./check.sh`, this repo's `status` in `notes.md`.

## Verification

- `uv run --group dev pytest -q tests/test_next_up.py tests/test_sdlc.py tests/test_bugs.py tests/test_skills.py`
- `uv run --quiet --script scripts/sdlc.py status` and `status --all` by eye.
- `./check.sh` exit 0.
