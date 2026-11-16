---
id: 060
slug: rework-as-declared-fix
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 060 — Rework as a declared fix, with surviving lines as the cross-check · plan

## Context

Retro's `rework` pairs any two changes closed within 7 days that share a file: 50 pairs in the
current window, none a real fix, so M5 is carried. The spec (`spec.md`, R1–R12) replaces it with
declared links (`reworks:` in an intent, and a fixed bug's `Introduced by:`) and a blame
cross-check listed as questions, never counted, and drops the file pairs and `rework_common`.

## Files to change

- **`scripts/sdlc.py`**
  - `reworks(text)` beside `depends_on()`; `load_change()` keeps and validates `reworks` as it
    does `depends_on`; `_change_record()` reads it from a closed intent.
  - `check`: an open change's `reworks` id naming no closed, dropped or open change is a problem,
    from one lazy walk shared with the `Introduced by:` check.
  - `retro()`: the file pairs, `touched`, `every_change`, `common` go; a new `_rework()` returns
    the declared links (`reworks:` and fixed bugs' `Introduced by:`, merged by pair, `via`), the
    blame questions (lines a change in the window removed, blamed at its base, owned by an earlier
    change in the window, pairs a link covers dropped) and problems. Output `rework`,
    `rework_questions`; `rework_common` gone. `REWORK_DAYS`, `REWORK_COMMON_SHARE` deleted.
- **`scripts/indicators.py`**: pure `removed_ranges()` (from `git diff -U0`) and
  `blame_commits()` (from `git blame --porcelain`).
- **`skills/intent/SKILL.md`**: Step 1 asks for `reworks:`; Steps 3 and 5 show and write it.
- **`skills/retro/SKILL.md`**: `rework` and `rework_questions`; no `rework_common`.
- **Docs**: `AGENTS.md`, `docs/REFERENCE.md`; `guide/process.md` only if it says "shared".
- **Tests**: `test_indicators.py` (parsers), `test_sdlc.py` (R1, R2, R10), `test_retro.py` (R3–R6,
  old rework tests replaced; `_close` gains `reworks=` and `rewrite=`), `test_skills.py` (R7, R8).

## Work order

1. Parsers + tests. 2. Frontmatter + check + tests. 3. `_rework()` + retro tests. 4. Skills, docs,
`./check.sh`, this repo's figures in `notes.md`.

## Verification

- `uv run --group dev pytest -q tests/test_retro.py tests/test_sdlc.py tests/test_skills.py tests/test_indicators.py`
- `uv run --quiet --script scripts/sdlc.py retro | jq '{rework: (.rework|length), questions: (.rework_questions|length)}'`
- `./check.sh` exit 0.

## Rollback

`git revert <sha>`: file-pair rework returns; a `reworks:` line already written in an intent is
then ignored text, harmless.
