---
id: 212
slug: landing-gaps
tier: 1
impact: none
stage: shipped
created: 2026-11-21
opened: 2026-11-21T03:58Z
updated: 2026-11-21
shipped: 2026-11-21
idea: [2026-11-20-7, 2026-11-20-51]
depends_on:
serves: [O6]
origin: self
---

# 212 — Two gaps in the landing's safety checks

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two gaps earlier changes left undone, both in the factory's landing code:

- **2026-11-20-7, from 193:** in `plugins/factory/scripts/landing.py:795`, "the grep refusals cover
  GNU grep and BSD grep only. If a host's `grep` on `PATH` is ugrep, `grep -r --dereference-files
  keep .` is allowed and follows links to files outside the checkout."
- **2026-11-20-51, from 200:** "No test fails when the train's readiness refusal
  (`_land_readiness()`'s `refusal`, in `cmd_train`) is ejected under another cause: mutating its
  `"refusal"` to `"review"` passed every train and landing test." The removed
  `test_every_ejection_names_its_cause` never reached that path either.

## Outcome

- The read-only list refuses ugrep's symlink-following long options: `--dereference-files` and
  each prefix ugrep accepts for it. A test fails if `grep -r --dereference-files keep .`, or a
  prefix of it, passes the list.
- A test drives the train to a readiness refusal and asserts its ejection's `cause` is `refusal`;
  mutating it to `review` fails that test.
- **Moves O6:** the landing that runs unattended has one fewer way to read outside the checkout,
  and one fewer cause it could misreport unseen.

## Affected

- **Area:** the factory's landing.
- **Files & components:** `plugins/factory/scripts/landing.py` (sensitive); the factory's landing
  and read-only tests.
- **Downstream:** every unattended train; the approver's read-only clearance of `checks.md`.
- **Contracts:** `plugins/factory/scripts/landing.py` is `[review] sensitive`; the read-only list's
  copies are pinned by tests; `test_no_agent_but_the_builder_runs_checks` stays green.

## Constraints

- The read-only list only grows stricter: nothing refused today is allowed after.
- No change to what a refusal ejects, only a test that pins it.

## Open questions

- Which other ugrep long options follow links (`--dereference-recursive`?), and does the list check
  prefixes of each, or every word against a list of such options?

## Approach

In `landing.py`'s grep check, refuse `--dereference-files` and any word that is an unambiguous
prefix of it (ugrep accepts `--deref…`), plus any sibling ugrep option the plan finds that follows
links, each with a test. Add one train test: a readiness refusal ejects with `cause: refusal`,
checking the mutation to `review` fails it. Two files plus tests.

Nits taken in: none
