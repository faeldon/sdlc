---
id: 158
slug: list-risky-modules
tier: 1
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O6]
---

# List the risky modules in the deep review's paths

## Problem

153 moves close, push and the main lock out of `scripts/sdlc.py` into `scripts/closing.py`, and the
landing and train out of `plugins/factory/scripts/factory.py` into
`plugins/factory/scripts/landing.py`, so the deep review can name them. The depth is read from the
base branch's `[review] sensitive` (`_review_list()`), never the change's own copy, so a change
can't choose its own review. 153's spec therefore requires both paths to be listed on `main` before
its build starts (its R10 and R11): otherwise its first `verdicts` would run light, and its build
stops. Today the list names the manifests, the shared settings, the trackers and the gates, not
these two paths.

## Outcome

- `.sdlc/config.toml`'s `[review] sensitive` lists `"scripts/closing.py"` and
  `"plugins/factory/scripts/landing.py"`, with the comment above the list saying why: close, push,
  the lock and the landing are where a mistake costs a host's work or history.
- On `main`, `git show main:.sdlc/config.toml | grep` finds both lines, which is the check 153's
  spec names before its build.
- Nothing else changes now: neither path exists on `main` yet, so no current change's depth moves,
  and `factory.py verdicts` on an open change reads the same depth before and after.
- **Moves O6:** once 153 lands, every change to the factory's riskiest code is reviewed at full
  depth with the security reviewer, from its first round.

## Affected

`.sdlc/config.toml` alone, read by `factory.py`'s `depth()` and `sdlc.py`'s `risk_paths()` (ship's
`preflight`), both from the base branch. Nothing a host has changes: this is the plugin repo's own
review list.

## Constraints

- Listed exactly as 153's spec names the paths, since its R10 test and Verification grep for them.
- The list stays read from the base branch, so a change can't lighten its own review.

## Open questions

- None.

## Approach

Add the two paths to `[review] sensitive` in `.sdlc/config.toml`, and extend the comment above the
list to say why. Check with `sdlc.py config` that `review.sensitive` reads them, and that
`factory.py verdicts` on an open change reports the same depth as before.
