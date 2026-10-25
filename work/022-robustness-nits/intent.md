---
id: 022
slug: robustness-nits
tier: 1
impact: patch
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea:
depends_on:
serves: [O2]
---

# 022 — Pay down the robustness nits in acceptance checks, release and deprecations

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Six `[robustness]` nits sit in `work/nits.md`, approved unfixed by the ships of 003, 005 and 010
on 2026-10-24. Each is a place in `scripts/sdlc.py` where bad input or a failed step gives a wrong
or confusing result instead of a clear one:

- **003-2:** `deprecations()` catches `TOMLDecodeError` but not `UnicodeDecodeError` from
  `read_text`, so a registry that isn't UTF-8 crashes `status` with a traceback, against the rule
  that bad input in a host is reported, never raised.
- **005-1:** `cmd_accept` takes the tree's `before` once, so one acceptance check that leaves the
  tree changed fails every check after it too, and ship reports failures that aren't real.
- **005-2:** `TimeoutExpired.stdout` is bytes even with `text=True`, so a timed-out check's output
  reads `b'…'`.
- **005-3:** acceptance checks inherit stdin, so a check that reads stdin waits out the full
  timeout instead of failing at once.
- **010-1:** release's after-bump step finds what the command changed with `git diff --name-only`,
  which sees unstaged changes only. A file the command stages is missed: left out of the release
  commit, and not put back on failure.
- **010-2:** when after-bump or the commit fails, `restore()` puts back tracked files only, so a
  changelog file the release created stays, and a rerun adds its section twice.

010-1, 010-2 and 003-2 are all on the path of the coming 1.2.0 release.

## Outcome

- Each nit has a test in `tests/` that fails on today's code and passes after:
  - a non-UTF-8 registry is a reported problem in `deprecations()`, not a raise;
  - a check that dirties the tree fails alone, and the next check is judged from its own `before`;
  - a timed-out check's `output` is text;
  - a check reading stdin gets EOF at once (`stdin=DEVNULL`) and doesn't wait out the timeout;
  - after-bump's changed files include ones the command staged (`git diff --name-only HEAD`);
  - a failed release removes a changelog file it created, so a rerun writes the section once.
- `/sdlc:ship` retires 003-2, 005-1, 005-2, 005-3, 010-1 and 010-2 from `work/nits.md`.
- `./check.sh` passes.
- **Moves O2:** a failed release or acceptance run leaves the host's tree as it found it and says
  what failed. Nothing is left half-written for a rerun to duplicate, and no crash hides the cause.

## Affected

- **Area:** `scripts/sdlc.py`: `deprecations()`, `cmd_accept()`, and `cmd_release()`'s after-bump
  and `restore()`.
- **Files & components:** `scripts/sdlc.py`, `tests/test_acceptance.py`, `tests/test_release.py`,
  `tests/test_deprecations.py`, `work/nits.md`.
- **Downstream:** hosts running `/sdlc:ship`'s acceptance checks and `/sdlc:release`, and `status`,
  which reads the deprecations registry. No change of meaning for any of them, only failures
  handled correctly.
- **Contracts:** release refuses a dirty main checkout (`_release_refusals()`), and the fixes must
  not loosen that; `accept` stays out of `ALLOW_RULES`; bad input is reported, never raised.

## Constraints

- No config key, frontmatter, skill text or WAIT changes.
- Restore deletes only what the release itself created: never a pre-existing file, never an
  untracked one the release didn't write.
- Each fix stays inside its function. Stop and promote to Tier 2 rather than rework a function.
- Don't touch retro or rework code, which is 021's ground.

## Open questions

- ~~For 010-1: should a file the after-bump command stages go into the release commit, or be
  refused?~~ Resolved: it goes in. `commit()` already commits the whole index; what was broken is
  that a failure didn't put it back, which `_put_back()` now does.
- ~~For 010-2: does `restore()` know which files the release created?~~ Resolved: no, so
  `changelog()` records the path in `created` when the file didn't exist, and `restore()` removes
  only those.
- ~~For 005-1: should a check that leaves the tree changed also put it back?~~ Resolved: no. Each
  check is judged on its own diff; `accept` never writes to the person's tree.

## Approach

One fix per nit, each in its own function, each with its test written first:

- **003-2:** catch `UnicodeDecodeError` beside `TOMLDecodeError` and report it.
- **005-1:** take `before` per check.
- **005-2:** decode `e.stdout` when it's bytes, with `errors="replace"`.
- **005-3:** pass `stdin=subprocess.DEVNULL`.
- **010-1:** diff against `HEAD`.
- **010-2:** record which release-written paths were new before writing them, and delete those in
  `restore()`.

Takes in nits 003-2, 005-1, 005-2, 005-3, 010-1 and 010-2.
