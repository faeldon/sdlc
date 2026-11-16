---
id: 064
slug: retro-reranks-inbox
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 064 — Retro re-ranks the inbox · plan

## Context

A retrospective sets direction but never re-ranks the register, so after each retro Next up (split
into Ready to build / Needs a decision by 062) still ranks by age and hand-set `Priority:` lines.
Spec R1–R7: retro lists the rankable entries, its skill proposes the changed `Priority:` and
`Theme:` lines behind its one approval and writes them, names retire candidates for `/sdlc:idea`,
and `retro-commit` refuses any register edit beyond those two lines.

## Files to change

- **`scripts/sdlc.py`**: `retro()` prints `entries` (open ideas and bugs, not nits, not being
  built); a pure `register_drift(old, new)` over `parse_entries()`; `cmd_retro_commit()` refuses
  what it finds between the register at `HEAD` and on disk.
- **`skills/retro/SKILL.md`**: Step 0's `entries`; the direction pass's re-rank; Step 4's table;
  Step 5's clause; Step 6's write; Step 7's report of retire candidates.
- **Docs**: `AGENTS.md` retrospectives paragraph; `docs/REFERENCE.md` retro paragraph.
- **Tests**: `tests/test_retro.py` (R1, R5), `tests/test_skills.py` (R2–R4).

## Work order

1. `entries` + test. 2. `register_drift` + `cmd_retro_commit` + tests. 3. Skill text + tests.
4. Docs, `./check.sh`, `notes.md`.

## Verification

- `uv run --group dev pytest -q tests/test_retro.py tests/test_skills.py`
- `uv run --quiet --script scripts/sdlc.py retro | jq '.entries | length'`
- `./check.sh` exit 0.
