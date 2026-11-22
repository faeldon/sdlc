---
id: 225
slug: ci-pin-test-quotes
tier: 1
impact: none
stage: shipped
created: 2026-11-22
opened: 2026-11-22T01:00Z
updated: 2026-11-22
shipped: 2026-11-22
idea:
depends_on:
serves: none
---

# 225 — The pinned-actions test reads a quoted `uses:` and says why it wants `v`

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Five nits left open on `tests/test_ci.py` by 221-ci-pinned-shas's reviews (2026-11-22-6 to -10),
two of them repeats of round 1 in round 2, and one already done:

- `USES` (`tests/test_ci.py:15`) captures a quoted value with its quotes, so
  `uses: "actions/checkout@<sha>" # v4.2.2`, a correct pin written in YAML's quoted form, is
  reported as unpinned. (The nits say a quoted tag "slips through"; it doesn't: the quotes make
  `PINNED` refuse it, which is the right answer for the wrong reason.)
- `VERSION` (`tests/test_ci.py:16`) refuses any trailing comment but `# v<digits>`, which is
  stricter than 221's outcome ("the version it is in a trailing comment") and says nowhere why.
- The `.yaml` glob nit is already fixed by `workflow_files()` and its test.

## Outcome

- `unpinned()` reads a `uses:` value in single or double quotes as its unquoted text: a quoted
  SHA pin with its `# v…` comment passes, a quoted tag or branch is still refused, and a test says
  both.
- `VERSION` keeps `# v<digits>`, and `unpinned()`'s docstring says why: it is the form Dependabot
  keeps the comment in when it bumps the pin, so a looser one would let the comment drift from the
  SHA.
- All five nits are retired when it ships.

## Affected

- **Area:** the repo's own tests, CI's supply-chain check.
- **Files & components:** `tests/test_ci.py` alone.
- **Downstream:** nothing reads it but the gate; `.github/workflows/check.yml` is unchanged.
- **Contracts:** none.

## Constraints

- The test stays `portable` (CI's Windows job runs it).
- A tag or branch pin, quoted or not, must still fail it.

## Open questions

- Is a flow-mapping `uses:` (`- { uses: a/b@v4 }`) worth reading too? No workflow here writes one.

## Approach

Strip one matching pair of `"` or `'` from `USES`'s value before `PINNED` checks it; extend
`test_the_check_refuses_a_tag_or_branch_pin` with a quoted SHA pin (passes) and a quoted tag
(refused); add the Dependabot reason to `unpinned()`'s docstring beside `VERSION`.

Nits taken in: 2026-11-22-6, 2026-11-22-7, 2026-11-22-8, 2026-11-22-9, 2026-11-22-10
