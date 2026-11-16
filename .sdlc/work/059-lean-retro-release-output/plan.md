---
id: 059
slug: lean-retro-release-output
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 059 — Leave each change's measured numbers out of retro's and release's output · plan

## Context

`unreleased`, `release` and `retro` print every change's full `metrics` blob (66 KB of
`unreleased`'s 105 KB today), which no skill reads per change: retro reads the top-level medians,
release none. Each release reads it twice. The spec (`spec.md`, R1–R11) leaves it out of the
printed JSON by default behind `--metrics`, keeping every aggregate, and takes in four S nits on
`scripts/sdlc.py`: one history walk in `next_up` (R7), `mark_issues` skipping issues already marked
(R8, touches the sensitive `scripts/trackers/`), `_inbox_commit`'s parameters (R9), and a hotspot's
`gone` (R10).

## Files to change

- **`scripts/sdlc.py`**
  - `_lean(records, metrics)` near `cmd_unreleased`: copies without `"metrics"` unless `metrics`.
  - `cmd_unreleased`, `cmd_release`, `cmd_retro` gain `metrics=False` and lean what they print;
    argparse `--metrics` on `unreleased`, `release`, `retro`; dispatch passes `args.metrics`.
  - R7: `next_up()` reads history through a cached `history()` closure, passed to
    `_milestone_verdicts(..., history=...)`, which walks only when given none.
  - R8: `mark_issues()` prefers the tracker's `open_marks()`, skipping a record with no parent or
    close whose issue is labelled `triaged`, not `needs-info`, with its marker in a comment; else
    `open_numbers()` as today.
  - R9: `cmd_inbox_commit` gathers its state into a dict; `_inbox_commit(root, home, state,
    report)`.
  - R10: `_architecture()` reads `git ls-tree -r --name-only <trunk>` and passes the paths to
    `indicators.hotspots(..., present=...)`.
- **`scripts/trackers/github.py`**: `open_marks(limit)`: one `issue list` with labels and comments.
- **`scripts/indicators.py`**: `hotspots(..., present=None)`; each entry gains `gone`.
- **`skills/retro/SKILL.md`**: only if it reads `lines: null` as deleted.
- **Docs**: `docs/REFERENCE.md`, `AGENTS.md`: `--metrics`.
- **Tests**: `test_release.py`, `test_retro.py` (R1–R4), `test_skills.py` (R6),
  `test_next_up.py` (R7), `test_archive.py` fake `gh` (R8), `test_bugs.py` (R9),
  `test_indicators.py` (R10).
- **`notes.md`**: sizes before and after.

## Work order

1. `_lean` + flags + dispatch; release/retro tests; measure sizes.
2. R7, R9 + tests.
3. R10 + test.
4. R8 + fake-gh test.
5. Docs, notes; `./check.sh`.

## Verification

- `uv run --group dev pytest -q tests/test_retro.py tests/test_release.py tests/test_archive.py tests/test_indicators.py tests/test_next_up.py tests/test_bugs.py tests/test_skills.py`
- `uv run --quiet --script scripts/sdlc.py unreleased | wc -c` ≤ 45000; with `--metrics` ≈ 105000.
- `./check.sh` exit 0.
- At ship: deep review (sensitive `scripts/trackers/`), fresh-context reviewer.

## Rollback

`git revert <sha>`: the full blob prints again; nothing written to history or a host changes.
