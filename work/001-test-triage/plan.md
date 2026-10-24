---
id: 001
slug: test-triage
kind: plan
created: 2026-10-24
updated: 2026-10-24
---

# 001 — Triage tests by how long they should live · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `defaults/SDLC.md`: Stage 4 — Test gains "Ask of each test how it could ever fail" and the
  three-way list (regression, compatibility, acceptance), after the failing-test-first paragraph.
- `.sdlc/SDLC.md`: the same text, in the same place.
- `defaults/REVIEW.md`: Pass 1's opening sentence lets a check recorded in `notes.md` stand in for
  a revert-only test; Pass 1 gains **A test only a revert can fail.** after **A test that can't
  fail.**; Pass 3 gains **A shim with no removal version.** after **Nothing speculative.**
- `.sdlc/REVIEW.md`: the same three edits, word for word (`tests/test_defaults.py` checks the
  bullets).
- `plugins/factory/agents/reviewer-test.md`: **How each test could fail.** after **The tests can
  fail.**, so the factory stops asking for acceptance-only tests in the suite.
- `work/ideas.md`: this seed goes `[building]` with a pointer here; a new seed under its own
  heading carries steps 2 and 3 and the sweep of existing tests, so ship's removal of this seed
  leaves it.
- `work/001-test-triage/notes.md` (new): this change's acceptance check, as the new rule says.

Not touched: `docs/REFERENCE.md` (doesn't list the review passes), `sdlc.py`, the skills,
`AGENTS.md` (already has the mirror rule).

## Work order

1. Stage 4 text into both SDLC docs from one script, so the two copies can't drift.
2. The three review edits into both REVIEW docs the same way.
3. The factory reviewer's bullet.
4. The follow-up seed; the intent's open questions struck, `stage: build`.
5. `./check.sh`, then the acceptance check, recorded in `notes.md`.

## Tests

- Regression, already in the gate: `tests/test_defaults.py` (the copies keep the defaults'
  headings in order and every review bullet word for word; the shipped docs' shape) and
  `tests/test_nothing_local.py`, both via `./check.sh`.
- Acceptance, run once and recorded in `notes.md`, not added to `tests/`: grep shows "Ask of each
  test how it could ever fail" once in each SDLC doc, and "A test only a revert can fail" and "A
  shim with no removal version" once in each REVIEW doc.

## Rollback

`git revert` covers all of it: every edit is a doc in this repo. Hosts that ran `/sdlc:setup`
after a release carrying this keep their copies; a revert doesn't reach them, and nothing needs it
to.
