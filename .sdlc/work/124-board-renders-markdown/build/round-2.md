I fixed both kept changes. The full gate passes (2320 passed, 13 skipped), and the new test plus the updated one each failed before their fix.

- **code C1, the focus trap (KEPT):**
  - **Fix:** `trapTab()` now leaves out any node inside a `[hidden]` element when it builds its focus cycle. The hidden Raw button is no longer counted as the first node, so the cycle starts at `#d-close` again, as it did before this change.
  - **Test:** I filtered in `trapTab()` instead of changing `FOCUSABLE`, because that also covers anything else that sits inside a hidden element. `test_the_focus_trap_skips_a_hidden_node` checks the filter is there.
  - **Browser check:** In Chromium, on `runs/builder.sessions` (where Raw is hidden), Shift-Tab from `#d-close` went to the file pane and stayed inside the drawer. Tab from the pane wrapped back to `#d-close`.
- **ux C2, wide code and tables (KEPT):**
  - **Fix:** Every fenced code block and every table wrapper now gets `tabindex="0"`, `role="region"` and an `aria-label` ("code" or "table"). A keyboard user can tab to the box and scroll it.
  - **Styling and test:** Both use the same `:focus-visible` outline as the file pane. `test_the_drawer_renders_markdown_as_nodes` now checks those attributes on both, and `test_the_focus_trap_skips_a_hidden_node` checks the outline rule.
  - **Notes:** I removed the matching item from `notes.md`, since this settles it.

`plan.md` is unchanged, because neither fix departs from it. `notes.md` now holds one item, which was already true before this change: `show()` can still paint a slow earlier file over a later one. I raised no new decisions this round.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k "markdown or focus_trap"   (before the fixes, red)
FAILED tests/test_board.py::test_the_drawer_renders_markdown_as_nodes - KeyEr...
FAILED tests/test_board.py::test_the_focus_trap_skips_a_hidden_node - assert ...
2 failed, 2 passed, 147 deselected in 0.48s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "markdown or focus_trap or tab_inside"
5 passed, 146 deselected in 0.22s
exit: 0

$ uv run --quiet --with playwright python d.py   (fixture board served on 127.0.0.1:5792)
shift-tab from close -> doc in drawer: True
tab from pane -> d-close
tab from md pane -> the spec
exit: 0

$ ./check.sh   (with pipefail, filtered to its summary lines)
All checks passed!
255 files already formatted
2320 passed, 13 skipped in 109.82s (0:01:49)
✔ Validation passed
✔ Validation passed
exit: 0
