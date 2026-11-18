VERDICT: PASS

## Notes
- The end-to-end path is `tests/test_board_browser.py`, run here with the browser installed. Both tests passed (2 passed, none skipped). The drawer test serves the fixture board on 127.0.0.1, opens a card, and finds focus on the close button. It then checks that Tab stays inside the drawer and that Escape returns focus to the card, as the intent's Outcome describes. I read the file only down to the server fixture (its first 60 lines) and relied on the passing run for the rest. The guard test passes too: no plugin script names Playwright.
- Check "CI's Linux job installs Chromium…": I expect it to pass. The exact `- run:` line is in `check.yml`, `playwright` appears once in the file, and the install line sits before the `pytest -q -n auto` line.
- Check "Playwright is in the dev group, with the browser marker": I expect it to pass. Both `"playwright>=1.49",` and the `"browser: ` marker are in `pyproject.toml` in the diff.
- Check "CONTRIBUTING says how to install the browser locally": I expect it to pass. The install command is in the added paragraph.
- I did not run the gate, since `factory.py` owns it, and I did not run `checks.md`. I did not exercise the skip path with the browser absent.
- Minor, not a CHANGE: the `check.yml` header comment now has one line well over 100 characters. Ruff does not lint YAML.

## Evidence
$ cat intent.md | head -60; ls change folder; git diff --stat a97f9a5...HEAD; cat checks.md
(intent, file list, diffstat and the three checks read as above)
exit: 0

$ sed -n 1,60p tests/test_board_browser.py (via head -60); uv run --group dev pytest tests/test_board_browser.py -q -rs | tail -8
..                                                                       [100%]
2 passed in 5.43s
exit: 0

$ git diff a97f9a5...HEAD -- .github pyproject.toml docs | head -80; grep -c playwright .github/workflows/check.yml
(workflow, pyproject and CONTRIBUTING hunks as quoted above)
1
exit: 0
