---
id: 061
slug: pay-down-tests-nits
tier: 1
impact: none
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-11-04-8
depends_on:
serves: none
---

# 061 — Pay down the tests nits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Seven open `[nit]` entries in the `tests` theme are each a test that passes whatever the code does,
or a copy nothing pins: the suite counts 1,676 tests, and these seven let real regressions through.

- **2026-10-24-7** (`tests/test_deprecations.py`): the patched half of the deprecations `status`
  test can't fail.
- **2026-10-25-22** (`tests/test_bugs.py`, cost M): `test_only_a_close_records_fixes_never_a_drop`
  greps `inspect.getsource` for `fix_trailers(`, so only a rename or a revert fails it.
- **2026-11-04-1** (`tests/test_skills.py`): retro's never-writes test greps `cmd_retro_commit`'s
  source for `review` and `config.toml`, never the refusal itself.
- **2026-10-26-14** (`tests/test_inbox.py`): nothing stops readiness's old `inbox` item coming back.
- **2026-11-04-12** (`tests/test_windows.py`): the LF test walks `write_text` calls only, so an
  `open(p, "w")` would write CRLF on Windows unnoticed.
- **2026-11-04-14** (`tests/test_windows.py`, `plugins/factory/scripts/factory.py`): the factory's
  copy of `_utf8_streams` isn't pinned to `sdlc.py`'s, as every other copy is (`risk_paths()`, the
  regexes, `trackers/command.py`'s `_sh`).
- **2026-11-13-2** (`tests/test_skills.py`): the side-file test checks a bare `file.md` pointer only
  against files that exist, so a pointer left naming a renamed side file passes.

The process guide's paydown threshold is five per theme; `tests` is the largest theme open (9
entries, 7 nits). The retrospective of 2026-11-04 raised this seed when it held five; M8 ("The
factory has built a change here") groups it.

## Outcome

- Each of the seven is fixed so its test fails on the regression it names: the patched half
  asserts what the patch changes; a dropped change with a `fixes:` line is closed for real and its
  `Drop` commit carries no `Sdlc-Fixes:`; a retro commit whose tree also changes `.sdlc/REVIEW.md`
  is refused; readiness's items are asserted to hold no `inbox`; write-mode `open()` calls are
  walked too; the factory's `_utf8_streams` is pinned to `sdlc.py`'s; a bare side-file pointer
  naming a missing file fails.
- Each replaced test is shown to fail against the bug it guards (the code broken briefly while
  building), noted in `notes.md`.
- `./check.sh` passes, and ship retires all seven nits.

## Affected

- **Area:** the test suite; the factory script only if its `_utf8_streams` has drifted.
- **Files & components:** `tests/test_deprecations.py`, `tests/test_bugs.py`,
  `tests/test_skills.py`, `tests/test_inbox.py`, `tests/test_windows.py`; possibly
  `plugins/factory/scripts/factory.py`.
- **Downstream:** none outside the repo: tests and CI's Windows job (`portable` tests) read them;
  no host receives a test.
- **Contracts:** the Windows rules (`test_windows.py` enforces them, and gets stricter); copies
  pinned to `sdlc.py` by test; `portable` marking for what CI's Windows job should run.

## Constraints

- No test is weakened or deleted unless a stronger one replaces it in the same diff.
- A stricter Windows test that finds an existing violation (a write-mode `open` without
  `newline="\n"`) means fixing the violation here, not loosening the test.
- Tests stay offline: the drop test uses the fake `gh` or a local tracker, as the close tests do.

## Open questions

- Has the factory's `_utf8_streams` already drifted from `sdlc.py`'s?
- Does anything in `scripts/` already open a file in write mode that 2026-11-04-12's stricter test
  would catch?
- Can 2026-10-25-22's real drop run reuse `test_archive.py`'s or `test_adoption.py`'s close
  harness, or does it need its own?

## Approach

One commit, one test or pin per nit, in the files above: rewrite each source-grepping test as a
behaviour test (2026-10-25-22, 2026-11-04-1); tighten the weak assertions (2026-10-24-7,
2026-10-26-14, 2026-11-13-2); extend the Windows LF walk to write-mode `open` calls (2026-11-04-12);
add a pin test comparing the factory's `_utf8_streams` with `sdlc.py`'s, as `_sh` is pinned
(2026-11-04-14). While building, break the code each test guards briefly to confirm it fails, and
note it in `notes.md`.
