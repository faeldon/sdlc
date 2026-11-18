---
id: 152
slug: board-drawer-browser-test
tier: 1
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-17-59
depends_on:
serves: none
---

# 152 — The board's drawer is tested in a real browser

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

099-board-page-fixes made the board's drawer keyboard-safe, and in its own words: "The page's tests
read its source; nothing runs the drawer's trap in a browser. A headless check would need a
dependency the gate doesn't have." Opening a card's drawer moves focus to its close button
(`scripts/board.html:627`), Tab stays inside the drawer while it is open, and closing it returns
focus to the card it came from (`:634`). `tests/test_board.py` checks the JavaScript holds those
calls, not that they work: a new focusable element the trap misses, or focus sent back to a card
node a poll has rebuilt, would pass every test. Only the factory's `[ui]` screenshots run a browser
today (Playwright through `uvx`), and they take pictures; they press no keys.

## Outcome

- Playwright is in `pyproject.toml`'s `dev` group and only there: no plugin script declares or
  imports it, and `tests/test_adoption.py` still runs a change from `new` to `close` without it.
- A test marked `browser` serves the board on its fixture (`tests/fixtures/board/`), opens a card's
  drawer and finds focus on the close button, presses Tab past the drawer's last element and finds
  focus still inside it, presses Escape and finds focus back on the card it opened.
- It is skipped, with the reason, when the browser isn't installed, so a contributor without it
  still has a green `./check.sh`; CI's Linux job installs the browser and runs it. The Windows job
  is unchanged (`-m portable`).

## Affected

`pyproject.toml` (the dev group, the `browser` marker), `tests/test_board.py` or a new
`tests/test_board_browser.py`, `.github/workflows/check.yml` (the browser install), and
`docs/CONTRIBUTING.md` (how to install it locally). Only this repo's own development: no host
installs the dev group.

## Constraints

- No plugin script imports Playwright or declares it in its PEP 723 block: nothing reaches a host.
- `./check.sh` stays green without the browser: the test skips, never fails for want of one.
- `.github/workflows/check.yml` is on `[review] sensitive`: a factory run goes to full depth, with
  the security reviewer.
- The test serves the fixture on `127.0.0.1` alone, as `board` does, and stops the server however
  the test ends.

## Open questions

- Should a skipped browser test print a note in `./check.sh`'s summary, so a contributor knows it
  didn't run?
- Chromium alone, or WebKit too, as Safari would run it?

## Approach

Add `playwright` to the dev group and a `browser` marker in `[tool.pytest.ini_options]`. A test
starts the fixture board through `tests/fixtures/board/serve.sh`, as `[ui] serve` does, on a free
port, and drives Chromium through Playwright's sync API: click the first card, assert
`document.activeElement` is the close button, Tab past the last element and assert focus is still
in the drawer, press Escape and assert focus is back on the card. `pytest.importorskip` the library,
and skip when the browser executable is missing. In CI's Linux job, add
`uv run --group dev playwright install --with-deps chromium` before pytest. A paragraph in
CONTRIBUTING.md.
