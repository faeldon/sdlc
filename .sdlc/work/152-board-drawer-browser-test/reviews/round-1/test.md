VERDICT: PASS

I found no requirement without a test that would fail without it, no test that can't fail, and no failing suite.

## Notes

- O1 (dev group only): `test_no_plugin_script_names_playwright` scans `scripts/**` and `plugins/*/scripts/**`. It asserts the list is non-empty, so it can't pass on a glob that matches nothing. `tests/test_adoption.py` is untouched and in the gate's green run.
- O2 (drawer focus): `test_the_drawer_holds_focus_and_returns_it_to_its_card` covers the three behaviours the intent names:
  - Focus is on `#d-close` after a card is opened.
  - Tab runs one past the count of focusable nodes in the drawer, then Shift-Tab, and focus stays inside `#drawer`.
  - After a `notes.md` write forces a poll to rebuild the cards, the old card node is detached, and Escape returns focus to the card with the same `data-change`. This catches the rebuilt-node case the intent worries about.
- O3 (skip without the browser): the `chromium` fixture skips with the install command when the library is missing or the launch raises "Executable doesn't exist". Any other launch error is re-raised. The server is shut down in a `finally`. I did not run the skip path itself.
- The gate record `build/round-1.gate.md` shows `2833 passed, 28 skipped`, with ruff and plugin validation green. It doesn't say whether the browser test was among the skips.
- I ran `uv run --group dev pytest tests/test_board_browser.py -q -rs` in the worktree. Result: `2 passed in 49.01s`, so the browser test runs here and doesn't skip.
- I did not re-run the plan's red steps (removing the focus call, the trap's forward wrap, and the old-node refocus). I judge the assertions sensitive to each of the three.
- Checks in `checks.md`:
  - CI install step: I expect it to pass. The one workflow line contains `playwright` and sits before the pytest line.
  - `pyproject` dependency and marker: I expect it to pass. Both lines are present as the greps require.
  - CONTRIBUTING install command: I expect it to pass. The paragraph contains the exact command.
  - Each is a one-line grep that leaves the tree unchanged, and each fails if the change is reverted.
- NIT: .github/workflows/check.yml:3: the reflowed header comment leaves one line far over the file's roughly 100-column wrapping {style S low}
- NIT: tests/test_board_browser.py:98: the test takes about 49s here, mostly waiting on the poll interval. A shorter bounded wait or a faster poll in the fixture would speed up `./check.sh` {tests M low}
