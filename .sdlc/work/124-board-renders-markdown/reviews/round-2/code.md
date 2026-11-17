VERDICT: PASS

Both kept round-1 points are already in the working tree, so nothing is left to rework.

- **Focus trap (correctness, kept):** `trapTab()` now filters with `.filter((n) => !n.closest("[hidden]"))` (board.html:631). `closest` includes the node itself, so a hidden Raw button is dropped from `first`/`end`. Tab on the last visible node wraps to `#d-close`, and Shift-Tab on it wraps to the last visible node. `test_the_focus_trap_skips_a_hidden_node` pins the filter's shape in source, as the finding asked.
- **Keyboard scrolling (ux, kept):** `pre.md-code` (board.html:340) and `div.md-table` (board.html:364) carry `tabindex: 0`, `role: "region"` and `aria-label` "code" or "table". `.md pre.md-code:focus-visible` and `.md .md-table:focus-visible` (line 159) give them an outline. `test_the_drawer_renders_markdown_as_nodes` checks all three attributes on both boxes.

I checked the trap's cycle by reading the code, not by running it in a browser, and I did not run the page's script.

## Notes

- NIT: scripts/board.html:159: the focus outline for the two new boxes is a sibling rule rather than a reuse of `.doc:focus-visible` (line 127). The rules match, so this is a style choice and nothing needs to change.
- Tests run: `uv run --group dev pytest tests/test_board.py`: 138 passed, 13 skipped. The skips are the existing escalation/stage cases, not the markdown or focus tests. The node-run markdown tests did run, since `node` is on the path here. The six tests selected by `-k "focus or markdown or only_a_markdown or drawer"` all pass.
- Not checked: the modified fixture `tests/fixtures/board/changes/005-draft-sharing/reviews/round-1/code.md` is in the working tree, and I read it only as a diff summary. Its first line still has to be `VERDICT: PASS`, which the fixture tests cover.
