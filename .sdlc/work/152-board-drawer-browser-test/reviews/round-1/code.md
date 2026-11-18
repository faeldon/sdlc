VERDICT: PASS

I checked each outcome in the intent against the diff:
- **Playwright scope:** it is in the `dev` group only. `test_no_plugin_script_names_playwright` guards the scripts, and the gate stayed green.
- **The drawer test:** it opens a card and finds focus on `d-close`. It tabs past the last element and shift-tabs, and focus stays in the drawer. A poll then rebuilds the cards, and Escape returns focus to the new card node. This is a stricter check than the intent asked for.
- **Skip behaviour:** the browser fixture skips with the install command in its reason when Chromium is missing.
- **CI and docs:** the Linux job installs Chromium, and the Windows job is unchanged. CONTRIBUTING.md has the paragraph, and its docstring reference to *The gate* resolves.

## Notes
- NIT: .github/workflows/check.yml:3: the header comment line now runs to 166 characters; the rest of the file wraps near 100. Re-wrap it {style S low}
- NIT: tests/test_board_browser.py:75: the intent's open question on a skip note in `./check.sh`'s summary is not addressed. Recorded here as a possible follow-up; the gate record shows 28 skipped without saying why {docs S low}
- Done well: the test covers the case where a poll rebuilds the card focus must return to, which the source-reading tests can't. The server always shuts down, and it binds `127.0.0.1` on a port the OS picks.
- Ran: `uv run --group dev pytest tests/test_board_browser.py -q -rs`. Both tests passed with Chromium installed (48s). Gate record `build/round-1.gate.md`: 2833 passed, 28 skipped.
