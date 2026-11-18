---
id: 136
slug: factory-rounds-that-catch-enough
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-14
depends_on:
serves: [O6]
---

# 136 — Factory rounds that catch what the landing catches, and stop early on a fault no round can fix

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A diff touching no sensitive path is built at the light depth: `[light]` runs `code` alone for 2
rounds (`plugins/factory/scripts/factory.py:108`). For a Tier 1 change, that reviewer runs on
haiku (`model_for()`, `:581`). On 2026-11-18, four changes passed their build rounds, shipped, and
were then sent back by their landing's review, which caught what the build's rounds missed:

- **124:** the `ui` and `ux` reviewers kept two changes, a heading that outranked the drawer's
  title and an unlabelled checkbox.
- **125:** `behaviour` kept a question that said "no gate configured" when no base branch had been
  read.
- **129:** `test` kept a missing test for the landing's own nit rule. The approver had escalated it
  beforehand over two unconfirmed defaults.
- **131:** the landing stopped red. The cause there was a machine path in a record, which 135
  fixes, not a missed finding.

Each of the first three cost a follow-up commit after ship, another gate run and another rebase,
made by hand. A fault the light rounds can't see costs more found at landing than found in a build
round.

The other end fails too. When every round fails on the same error, or on something no test can
show, the run spends all its rounds before it escalates. The rounds add cost without changing the
outcome.

## Outcome

- The depth and models a factory run gets are chosen from evidence: the landed factory changes'
  rounds, landing rounds, `verified.md` and `Sdlc-Review`/`Sdlc-Rework` trailers. The choice is
  written down, and each default it changes, such as `[light]`'s reviewers or rounds, or
  `model_for()`'s haiku, says why.
- Over the next retro window, fewer factory changes have a landing review that keeps a change the
  build's rounds could have caught. `/sdlc:retro` can count that from the records.
- A run whose rounds keep failing on the same error, or on a requirement nothing can test,
  escalates at once with that reason. It doesn't spend its remaining rounds. A test feeds
  `verdicts` two rounds with the same kept change and finds the escalation.
- **Moves O6:** a factory-built change escapes to its landing, or past it, no more often than one
  built by hand, and stops the person early when a round can't help.

## Affected

- **Area:** the factory's run loop and its defaults, in `plugins/factory/`.
- **Files & components:** `factory.py`'s `DEFAULTS`, `light_reviewers()`, `model_for()` and
  `verdicts`/`loop_state()`, which decide the next step and when to escalate. Also
  `plugins/factory/README.md`'s configuration section, and tests in `tests/test_factory.py`.
- **Downstream:** every factory run, in this repo and in any host with `sdlc-factory`. A changed
  default changes what a host's `.sdlc/factory.toml` doesn't set, and what a run costs
  (`agent_runs`, `:689`, the number the build question names). Depends on 135 only in spirit: a
  red gate caused by a machine path in a record shouldn't count as a round's fault.
- **Contracts:** `verdicts` decides from the rounds alone and never reads a state file. Depth
  comes from the diff against the base branch's `[review] sensitive`. Every setting is read from
  the base branch's `factory.toml`, so a change can't widen or lighten its own run.

## Constraints

- A host that set `rounds`, `[light]` or `[models]` keeps what it set.
- The build question keeps naming the reviewers, rounds and run ceiling a yes approves.
- The landing's own reviews stay a second look, never removed to make the numbers better.

## Open questions

- ~~Which of these closes the gap at least cost: sonnet for the light depth, the landing's reviewers
  (`test`, `behaviour`, `ui`/`ux`) moved into the build's rounds, a third light round, or a
  different reviewer by what the diff touches?~~ Resolved: sonnet for the scaled reviewers and
  `behaviour` at the light depth (spec R1, R2).
- ~~What counts as "the same error": the same kept `CHANGE:` line in two rounds, the same failing
  test in two red gates, or both?~~ Resolved: the same kept `(role, change)` in two consecutive
  rounds (spec R3, R4).
- ~~How does a run know a requirement can't be tested, and is that the builder's to say
  (`- UNTESTABLE:`) or the verifier's?~~ Resolved: the builder's, by `- UNTESTABLE:` (spec R5).
- ~~Is today's evidence enough to change a default, or should the change first make the retro count
  landing catches against build rounds, and decide from a window of data?~~ Resolved: enough to
  change R1 and R2, with the retro counting landing catches from now on (spec R1, R2, R8).
- ~~Should the early escalation name a next step for the person (a model to try, a requirement to
  rewrite) rather than only a reason?~~ Resolved: yes, under `## Reconsider the approach` (spec R7).
