The board's drawer now has a test that runs it in Chromium: focus lands on the close button, Tab stays inside the drawer, and Escape gives focus back to the card. The full gate passes (2833 passed, 28 skipped). Everything is left uncommitted on the change's branch, and HEAD is still `7128522`.

**What was built** (Tier 1, with a `plan.md` because four files changed):
1. **The drawer test** (`tests/test_board_browser.py`, new, marked `browser`). It builds the board fixture with `tests/fixtures/board/build.sh` and serves it on `127.0.0.1`. The port is picked by the OS (`board.serve(root, 0)`), and the server is shut down however the test ends. In headless Chromium it:
   - opens the first card and checks focus is on `#d-close`;
   - presses Tab once more than the drawer has focusable elements, then Shift-Tab, checking after each press that focus is still inside `#drawer`;
   - writes a `notes.md` into the open change's folder, so the next poll rebuilds every card, and waits until the card it opened from is gone from the page;
   - presses Escape and checks the drawer is hidden and focus is on the new card with the same `data-change`.

   I saw it fail on three deliberate breaks of `scripts/board.html`, one at a time, each for the expected reason: no focus on open (`'' == 'd-close'`), no Tab wrap (focus left the drawer), and focus sent back to the old card (`None == '001-draft-labels'`). The file was restored after each.
2. **The dependency and the marker.** `playwright>=1.49` is in `pyproject.toml`'s `dev` group, `uv.lock` is updated, and the `browser` marker is declared. A second test, `test_no_plugin_script_names_playwright`, fails if any file under `scripts/` or `plugins/*/scripts/` mentions Playwright. `tests/test_adoption.py` is unchanged and passed in the full gate run.
3. **CI and docs.** The Linux job runs `uv run --group dev playwright install --with-deps --only-shell chromium` before pytest, and the Windows job is unchanged. `docs/CONTRIBUTING.md` (*The gate*) gains a paragraph on installing the browser locally and on the test skipping without it.

**Skipping:** without the library the test skips with "playwright isn't installed: uv sync --group dev". Without the browser it skips with "Chromium isn't installed: uv run --group dev playwright install --only-shell chromium". I confirmed the second by pointing `PLAYWRIGHT_BROWSERS_PATH` at an empty folder.

**`checks.md`** holds three acceptance checks, each exiting 0: the CI install step comes before pytest and only the Linux job has it; the dev-group line and the marker are in `pyproject.toml`; CONTRIBUTING has the install command.

**Where the build departed from `plan.md`** (the plan is updated to match):
- **Browser check:** the test looks for the browser by trying to start it, catching Playwright's "Executable doesn't exist" error. Checking `chromium.executable_path` doesn't work, because headless mode runs a separate build, the headless shell.
- **Headless shell only:** CI and the docs install just that build (`--only-shell`), so Playwright is pinned at 1.49 or later.
- **Card rebuild:** the test forces the card rebuild by writing a file, because a poll with nothing new rebuilds nothing.
- **Rollback wording:** I reworded the rollback section after the no-local-paths test flagged a home-directory path in it.

**`notes.md`:** nothing.

- DECISION: [default] Serve the fixture in-process (`build.sh` plus `board.serve(root, 0)`) rather than through `serve.sh` as the Approach says. Going ahead unless told otherwise.
  - OPTION: in-process — the OS picks the port, so no race between parallel test workers, and the server stops in a `finally`; it doesn't exercise `serve.sh`'s own lines
  - OPTION: `serve.sh` subprocess — the exact command the UI review runs; the port has to be chosen before it's bound, which can race, and a child process has to be killed
  - WHY: the intent's constraint that the server stops however the test ends, and `tests/test_board.py`'s `served` fixture already serves this way
- DECISION: [default] Chromium alone, not WebKit too (the intent's open question). Going ahead with Chromium only.
  - OPTION: Chromium alone — one download in CI and locally; Safari's focus handling isn't covered
  - OPTION: Chromium and WebKit — covers Safari too; a second, bigger download and a slower CI job
  - WHY: the intent's Approach names Chromium, and the trap is plain DOM focus code
- DECISION: [default] No extra note in `./check.sh`'s summary when the browser test skips (the intent's other open question): pytest's "N skipped" count and `-rs` give the reason. Going ahead unless told otherwise.
  - OPTION: no extra note — `check.sh` stays as it is; a contributor has to know about `-rs` to see why
  - OPTION: add `-rs` to `check.sh`'s pytest call — every skip's reason is printed; noisier output on every run
  - WHY: CONTRIBUTING's new paragraph says the test skips and how to install the browser

## Evidence

$ uv run --quiet --group dev pytest tests/test_board_browser.py -q -rs   (before playwright was in the dev group)
SKIPPED [1] tests/test_board_browser.py:78: playwright isn't installed: uv sync --group dev
1 passed, 1 skipped, 1 warning in 4.21s
exit: 0

$ uv run --quiet --group dev pytest tests/test_board_browser.py -q -k drawer   (board.html without `$("d-close").focus()`)
E       AssertionError: assert '' == 'd-close'
1 failed, 1 deselected in 2.58s
exit: 1

$ uv run --quiet --group dev pytest tests/test_board_browser.py -q -k drawer   (board.html without the trap's forward wrap)
E           assert False
E            +  where False = evaluate("() => document.getElementById('drawer').contains(document.activeElement)")
1 failed, 1 deselected in 2.58s
exit: 1

$ uv run --quiet --group dev pytest tests/test_board_browser.py -q -k drawer   (board.html focusing the old card node)
E       AssertionError: assert None == '001-draft-labels'
1 failed, 1 deselected in 4.19s
exit: 1

$ PLAYWRIGHT_BROWSERS_PATH=/tmp/nobrowsers152 uv run --quiet --group dev pytest tests/test_board_browser.py -q -rs
SKIPPED [1] tests/test_board_browser.py:82: Chromium isn't installed: uv run --group dev playwright install chromium
1 passed, 1 skipped in 1.69s
exit: 0

$ uv run --quiet --group dev pytest tests/test_board_browser.py -q
2 passed in 4.27s
exit: 0

$ awk '/^```sh$/{f=1;next} /^```$/{f=0} f' .sdlc/work/152-board-drawer-browser-test/checks.md | while IFS= read -r c; do sh -c "$c"; echo "exit: $?"; done
exit: 0
exit: 0
exit: 0
exit: 0

$ ./check.sh
1 failed, 2832 passed, 28 skipped in 241.74s (0:04:01)
FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden
exit: 1

$ ./check.sh   (after rewording plan.md's rollback)
All checks passed!
2833 passed, 28 skipped in 308.46s (0:05:08)
✔ Validation passed
✔ Validation passed
exit: 0
