---
id: 001
slug: test-triage
tier: 1
impact: patch
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea: Triage tests by how long they should live
depends_on:
serves: none
---

# 001 — Triage tests by how long they should live

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Nothing in the process asks how long a test should live, so `tests/` only ever grows. Some tests
matter only while a change is being built. For example, a test that a file moved or a key was
renamed can fail only if someone deliberately reverts that change, yet it stays in the gate forever
and every later run pays for it. Shims kept "for one release" are the other half: no rule says a
shim must name the version it's removed in, so nothing ever flags one that's overdue. Stage 4 —
Test in `defaults/SDLC.md` covers the gate, the slower check, failing-test-first and the empty run,
but never what a test is *for*. Review Pass 1 in `defaults/REVIEW.md` catches "a test that can't
fail", but not a test that only a revert can fail.

## Outcome

- Stage 4 — Test, in `defaults/SDLC.md` and `.sdlc/SDLC.md`, sorts each test by how it could ever
  fail:
  - **Regression:** a later change breaks it by accident. It stays in `tests/` for good.
  - **Compatibility:** it breaks when a shim stops working. It lives exactly as long as the shim,
    and the shim names the version it's removed in.
  - **Acceptance:** only a deliberate revert breaks it. It proves the change once and stays out of
    `tests/`.
- `defaults/REVIEW.md` and `.sdlc/REVIEW.md` gain two findings, word for word the same in both:
  *a test in `tests/` that only a revert can fail*, and *a shim with no removal version*.
- `./check.sh` passes, including `tests/test_defaults.py`'s check that `.sdlc/` keeps every default
  heading and review bullet in order.

## Affected

- **Area:** the process docs the plugin ships, and this repo's copies of them.
- **Files & components:** `defaults/SDLC.md`, `defaults/REVIEW.md`, `.sdlc/SDLC.md`,
  `.sdlc/REVIEW.md`. `docs/REFERENCE.md` only if it describes the review passes.
- **Downstream:** new hosts get the rule through `/sdlc:setup`. Existing hosts own their copies and
  don't see it, except a host with no review doc, whose review reads `defaults/REVIEW.md` directly.
  `/sdlc:ship`'s review applies the findings.
- **Contracts:** the "process docs track the defaults" invariant (same edit in `defaults/` and
  `.sdlc/`, bullets word for word), and the one-shape rule for shipped docs. No `sdlc.py`, skill,
  WAIT or `allowed-tools` change.

## Constraints

- Each edit lands in both `defaults/` and `.sdlc/` in this change. The default review bullets stay
  word for word in this repo's copy.
- Docs only. The `DEPRECATIONS` registry, `compat` marker and overdue-shim test (seed step 2), and
  acceptance checks living in `work/NNN-slug/` (seed step 3), stay in the seed for later changes.
- Nothing names a project or a local path (`test_nothing_local.py`).

## Open questions

- ~~Without step 3, where does an acceptance check go?~~ Resolved: run it once at Stage 4, as a
  command or a throwaway test, and record what ran and what it showed in the change's `notes.md`,
  which reaches history with the folder.
- ~~Which pass gets which finding?~~ Resolved: a test only a revert can fail goes in Pass 1, beside
  "A test that can't fail"; a shim with no removal version goes in Pass 3, beside "Nothing
  speculative".
- ~~Should existing tests in `tests/` get a sweep for acceptance-only cases in this change?~~
  Resolved: no, it is a later change, in the follow-up seed with steps 2 and 3.

## Approach

Add a short paragraph and the three-way list to Stage 4 — Test after "A bug fix starts with a
failing test.", one bullet each to review Pass 1 and Pass 3, and a clause to Pass 1's opening
sentence that lets a recorded check stand in for a revert-only test. Make the same edits in
`.sdlc/SDLC.md` and `.sdlc/REVIEW.md`. Give the factory's test reviewer
(`plugins/factory/agents/reviewer-test.md`) one bullet asking how each test could fail, so it stops
asking for acceptance-only tests in the suite. Add a follow-up seed to `work/ideas.md` carrying
steps 2 and 3 and the sweep of existing tests, under its own heading so ship's removal of this
seed leaves it. Run `./check.sh`. `plan.md` holds the exact text.
