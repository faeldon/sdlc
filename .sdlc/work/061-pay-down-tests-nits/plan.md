---
id: 061
slug: pay-down-tests-nits
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 061 — Pay down the tests nits · plan

## Context

Seven open `[nit]` entries in the `tests` theme are tests that pass whatever the code does, or a
copy nothing pins (intent.md). Each gets a test that fails on the regression it names; ship
retires all seven. `_utf8_streams` is identical in the factory and `sdlc.py`, so no script
changes.

## Changes, one per nit

1. **2026-10-24-7** (`tests/test_deprecations.py`): status with no registry equals status with an
   empty `.sdlc/deprecations.toml`, and a registry holding a shim changes it, so the comparison can
   fail.
2. **2026-10-25-22** (`tests/test_archive.py`, `tests/test_bugs.py`): a dropped change with a
   `fixes:` line is closed for real and its `Drop` commit holds no `Sdlc-Fixes:`; the source-grep
   test goes.
3. **2026-11-04-1** (`tests/test_retro.py`, `tests/test_skills.py`): retro-commit refuses a tree
   that also changes `.sdlc/REVIEW.md` or `.sdlc/config.toml`; the source grep goes.
4. **2026-10-26-14** (`tests/test_inbox.py`): readiness holds no `inbox` item.
5. **2026-11-04-12** (`tests/test_windows.py`): the LF test walks text write-mode `open` calls too.
6. **2026-11-04-14** (`tests/test_windows.py`): the factory's `_utf8_streams` is pinned to
   `sdlc.py`'s, as `_sh` is.
7. **2026-11-13-2** (`tests/test_skills.py`): every bare backticked `x.md` a `SKILL.md` names is a
   file the repo holds.

Each is shown to fail against the code it guards, broken briefly while building, noted in
`notes.md`.

## Verification

- `uv run --group dev pytest -q tests/test_deprecations.py tests/test_archive.py tests/test_bugs.py tests/test_retro.py tests/test_skills.py tests/test_inbox.py tests/test_windows.py`
- `./check.sh` exit 0.
