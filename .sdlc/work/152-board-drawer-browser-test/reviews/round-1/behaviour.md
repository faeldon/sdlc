VERDICT: PASS

The browser test runs green against Chromium and drives the drawer the way the intent describes. No plugin script mentions Playwright; the only hit under `scripts` and `plugins` is `plugins/factory/README.md`, which is documentation.

## Notes
- **End-to-end path:** `tests/test_board_browser.py` passes with the `browser` marker. It opens a card's drawer, checks focus, tabs past the last element and presses Escape. I read that the test skips with the install command in its reason, when the library or Chromium is missing: lines 60 and 70 do that. I did not run that skip path, since Chromium is installed here.
- **Check "CI's Linux job installs Chromium before its tests":** I expect it to pass. The install line is at `check.yml:22`, before `pytest -q -n auto` at line 23. Playwright appears on one line only, and the Windows job is unchanged.
- **Check "Playwright is in the dev group, with the browser marker":** I expect it to pass. `pyproject.toml:17` has `"playwright>=1.49",` and line 39 has the `"browser: ` marker.
- **Check "CONTRIBUTING says how to install the browser locally":** I expect it to pass. `docs/CONTRIBUTING.md:88` has the command.
- **Gate:** I did not rerun it. The gate record (`build/round-1.gate.md`) ends with plugin validation passing; I read only its tail.

## Evidence
$ cd .sdlc/work/152-board-drawer-browser-test && ls; cat intent.md | head -80; cat build/round-1.gate.md | tail -15; cat checks.md
(tail) factory plugin validation passed; checks.md read in full
exit: 0

$ ls tests | grep browser; grep -n playwright .github/workflows/check.yml pyproject.toml docs/CONTRIBUTING.md; grep -n '"browser' pyproject.toml; grep -n -B3 -A3 pytest .github/workflows/check.yml
(tail) test_board_browser.py; check.yml:22 install line; check.yml:23 `uv run --group dev pytest -q -n auto`; pyproject.toml:17 `"playwright>=1.49",`; pyproject.toml:39 the `"browser: ` marker; CONTRIBUTING.md:88 install command
exit: 0

$ uv run --group dev pytest -q -m browser tests/test_board_browser.py -rs
(tail) . [100%]
1 passed, 1 deselected in 51.27s
exit: 0

$ grep -rln -i playwright scripts plugins | head; grep -n "skip" tests/test_board_browser.py | head
(tail) plugins/factory/README.md; 3: ... the test skips, saying which; 60: pytest.importorskip(; 70: pytest.skip(f"Chromium isn't installed: {INSTALL}")
exit: 0
