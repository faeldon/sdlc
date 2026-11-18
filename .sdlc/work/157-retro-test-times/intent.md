---
id: 157
slug: retro-test-times
tier: 1
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: none
---

# Retro reads the suite's per-test run times

## Problem

`/sdlc:retro`'s pruning pass reads `tests.times` from `retro.test_times`, and this repo sets none,
so the retrospective of 2026-11-18 reported `times.state: unset`. Its pruning seed
(2026-11-18-90) rests on `drifted` alone, with no slow test named. The suite has grown from 18,861
to 38,166 lines in one window, and two open nits (2026-11-18-71, -79) already point at a single
test taking about 49 seconds, but nothing measures it.

## Outcome

- `.sdlc/config.toml`'s `[retro]` sets `test_times` to one command. It runs the suite once with
  `--junitxml` into `.sdlc/reports/junit.xml` (ignored), sends pytest's own output to /dev/null,
  and `cat`s the report, so stdout holds only the XML.
- From the main checkout, `sdlc.py retro` gives `tests.times.state: ok` with the counts, the total
  seconds, the median, the ten slowest and `slow`, inside retro's 600-second limit.
- A red suite still prints its report (`;`, not `&&`), so the times are read either way.

## Affected

`.sdlc/config.toml` alone, read by `sdlc.py retro` (`_evidence()`), which runs the command only
when a retrospective runs. Nothing a host has changes: the key is this repo's own setting, and
`docs/REFERENCE.md` already documents it.

## Constraints

- The command runs as `sh -c` from the repo root, as `retro.evidence` does. It must print only the
  JUnit XML on stdout, finish within 600 seconds, and write nowhere tracked.
- `retro` stays read-only but for its report. The junit file goes under `.sdlc/reports/`, which its
  own `.gitignore` ignores, so the tree stays clean for `retro-commit`.

## Open questions

- Whether running the full suite at every retrospective (a few minutes with `-n auto`) is worth it,
  rather than `cat`ting a report the gate leaves. A report the gate leaves could be stale, or come
  from a worktree.

## Approach

Add the `test_times` line, with a one-line comment, under `[retro]` in `.sdlc/config.toml`. Then
run `sdlc.py retro` from this change's worktree and confirm `tests.times.state` is `ok` and the
slowest tests are named.
