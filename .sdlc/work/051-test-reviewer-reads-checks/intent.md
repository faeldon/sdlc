---
id: 051
slug: test-reviewer-reads-checks
tier: 1
impact: patch
stage: shipped
created: 2026-11-12
updated: 2026-11-12
shipped: 2026-11-12
idea: 2026-11-04-4
depends_on:
serves: none
---

# 051 — The test reviewer reads checks.md and never runs it

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`plugins/factory/agents/reviewer-test.md` tells the test reviewer to run each `checks.md`
section's `sh` block itself, from the repo root, and to count a requirement as covered when it
passes. The behaviour check (`reviewer-behaviour.md`, 039) is told the opposite, under `## checks.md:
read, never run`: an agent may have written those commands, and `/sdlc:ship` runs them with
`sdlc.py accept` only after a person has seen each one. So one factory round has two reviewers with
opposite rules, and the one with `Bash` that runs them is running commands another agent (the
builder) wrote, with nobody seeing them first: the unasked run `accept`'s prompt exists to stop.
`test_what_runs_the_change_shows_its_evidence_and_never_runs_checks` pins the rule for the
behaviour check only, so nothing catches the test reviewer. Found while building 039, noted
pre-existing in its `notes.md`.

## Outcome

- `reviewer-test.md` no longer tells it to run `checks.md`: it reads each section and says, against
  the code as it stands, whether the check would prove its requirement and could fail, as it does
  for a test. A section it expects to fail, or one that can't, is a CHANGE.
- The test reviewer still runs the repo's test suite; `Bash` stays in its tools for that.
- A test in `tests/test_skills.py` pins the rule for the test reviewer as the existing one does for
  the behaviour check, and fails if the "run each section's `sh` block yourself" wording comes back
  — for every factory agent with `Bash` but the builder, which writes them.

## Affected

- **Area:** the factory's review agents.
- **Files & components:** `plugins/factory/agents/reviewer-test.md`; `tests/test_skills.py` for the
  pin. The factory's other agents (approver, verifier, reviewers) only read, to confirm none runs
  `checks.md` either.
- **Downstream:** `/sdlc-factory:build`, which spawns the test reviewer each round, and the hosts
  that install `sdlc-factory`. `sdlc` itself is unchanged: `accept` and ship's prompt stay as they
  are.
- **Contracts:** `accept` stays the only thing that runs `checks.md`, never in `ALLOW_RULES` or a
  skill's `allowed-tools` (`test_no_skill_lets_accept_run_unasked`).

## Constraints

- The test reviewer keeps its tools (`Read, Grep, Glob, Bash`, pinned in `tests/test_skills.py`),
  since it still runs the suite.
- It stays read-only, and stays adapted from agent-skills with its NOTICE line.

## Open questions

- ~~Should the test reviewer say why it expects each check to pass or fail in its `## Notes`, as
  the behaviour check does, or is one line per check enough given the behaviour check covers
  that?~~ Resolved: its Notes name each check and what it expects of it, as the behaviour check's do.
- ~~Should the pin be one test over every factory agent's text ("no agent but the builder mentions
  running `checks.md`"), or a second assertion beside the behaviour check's?~~ Resolved: one test
  over every agent with `Bash` but the builder, which also covers the verifier.

## Approach

Rewrite the "How each test could fail" bullet in `reviewer-test.md`: a suite test only a revert
could fail is still asked for as a `checks.md` section, but each existing section is read, never
run, with the behaviour check's reason. Add the pin to `tests/test_skills.py` beside
`test_what_runs_the_change_shows_its_evidence_and_never_runs_checks`.
