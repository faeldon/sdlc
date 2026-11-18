---
id: 152
slug: board-drawer-browser-test
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 152 — The board's drawer is tested in a real browser · plan

> Tier 1, written because the Approach touches four files. The intent's Approach is the spec; the
> outcomes below are its three bullets, O1–O3.

## Files to change

- `pyproject.toml`: `playwright` in the `dev` group (and nowhere else); a `browser` marker in
  `[tool.pytest.ini_options]`.
- `tests/test_board_browser.py` (new): the drawer's focus test in Chromium, and a test that no
  plugin script names Playwright.
- `.github/workflows/check.yml`: the Linux job installs Chromium before pytest. Windows unchanged.
- `docs/CONTRIBUTING.md`, *The gate*: a paragraph on installing the browser locally, and that the
  test skips without it.
- `.sdlc/work/152-board-drawer-browser-test/checks.md` (new): the CI install step and the
  CONTRIBUTING paragraph, which only a revert would remove.

Reused, not re-derived: `tests/fixtures/board/build.sh` builds the fixture repo (the same one
`serve.sh` and the UI review use), and `board.serve(root, 0)` serves it in-process on `127.0.0.1`
with a port the OS picks, as `tests/test_board.py`'s `served` fixture does. Not `serve.sh` itself:
a subprocess on a port chosen beforehand races other xdist workers for it, and the in-process
server is shut down in a `finally` however the test ends (the intent's constraint).

## Work order

1. **The drawer test, skipping without Playwright.** `pytest.importorskip("playwright.sync_api")`,
   then skip when `chromium.launch()` raises Playwright's "Executable doesn't exist" (headless runs
   its own build, so `chromium.executable_path` isn't the one to look for). Build the fixture,
   serve it, open a card, assert focus is on `#d-close`; Tab once more than the drawer has
   focusable nodes and assert focus never leaves `#drawer`, then Shift-Tab; write a `notes.md`
   into the opened change's folder so the next poll of `/state.json` rebuilds every card, wait
   until the card node it opened from is detached, press Escape and assert focus is on the card
   with the same `data-change`. Red: run it with `board.html`'s `$("d-close").focus()` removed,
   its trap's forward wrap removed, and focus sent back to the old card node, each in turn, and
   see it fail; restore.
2. **The dependency and the marker.** `playwright` into the `dev` group, the `browser` marker; a
   test that nothing under `scripts/` or `plugins/*/scripts/` names `playwright`.
3. **CI and docs.** The install step in the Linux job, the CONTRIBUTING paragraph, `checks.md`.
   Both install only Chromium's headless shell (`--only-shell`, Playwright 1.49 on, hence the
   `>=1.49` pin), which is all a headless launch runs.

## Tests

- O1 (only in the dev group): `test_no_plugin_script_names_playwright`; `tests/test_adoption.py`
  unchanged and green, since it runs `uv run --script` with `VIRTUAL_ENV` dropped.
- O2 (the drawer's focus): `test_the_drawer_holds_focus_and_returns_it_to_its_card`.
- O3 (skips without the browser; CI runs it): the skip path in the same test, shown by running it
  with `PLAYWRIGHT_BROWSERS_PATH` pointed at an empty dir; `checks.md` for the CI step.

## Rollback

`git revert` covers it all. Outside the repo: the Chromium download in Playwright's own cache
folder (`ms-playwright`, in the user's cache directory), removed with
`uv run --group dev playwright uninstall`, or by deleting that folder.
