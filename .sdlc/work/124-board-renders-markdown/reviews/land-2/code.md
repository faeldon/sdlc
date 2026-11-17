VERDICT: PASS

The change is sound. Nothing I found is Critical or Required, so the verdict is PASS. The one nit is below.

## Notes

- NIT: scripts/board.html:284: `MD_DELIM` accepts a bare `---` line as a table's delimiter row (checked: it matches `---` and `|---|` alike), so a paragraph line containing `|` above a horizontal rule renders as a header-only table. Require a `|` in the delimiter row in `isTable()`, as GFM does, so the rule stays a rule.

What is done well:
- Every node goes through `h()`, with text as text nodes and attributes via `setAttribute`. Nothing from a file is parsed as HTML. `javascript:`, `data:` and absolute or `..`-escaping links are refused by `mdLink()` and `mdResolve()`. An internal link becomes `data-path` on an `href="#"` anchor, and only `http(s):` and `mailto:` reach an `href`.
- Round 1's focus-trap finding (F1) is fixed: `trapTab()` filters `[hidden]` nodes, and the Raw toggle can't take focus when hidden. Round 1's keyboard-scroll finding (F5) is fixed: `pre.md-code` and `.md-table` are named, focusable regions.
- The block and list recursion always shrinks its input, so no line sequence I can find makes it loop.
- The carried ux item (the blank pane for an empty `.md`, F7) was recorded as seed `2026-11-18-8` and the `show()` race as bug `2026-11-18-9`. I did not raise either again.

Gaps in what I checked:
- `build/land-2.md` is not in the change folder. Only `build/land-2.gate.md` is there, and it records a PASS at `2bf608a`. I therefore could not read the builder's account of its resolution. The diff from `e26da2f` is only the change's own commit, and no board file differs between `6d8905f` and `e26da2f`, so I found no conflict in the code. The builder should confirm the note exists.
- `inbox.md` entries `-8` and `-9` ride on the change's commit. That matches ship's `next-entry` design for carried seeds, so I did not raise it.
- The focus trap is verified by reading it and by a source-shape test. I did not run the page in a browser.

Tests run (read-only, cache off):
- `uv run --group dev pytest -p no:cacheprovider -q tests/test_board.py -k "markdown or focus or only_a_markdown or drawer or sink"`: 6 passed.
- The full gate is not rerun. The land-2 gate record shows `./check.sh` at 2340 passed, 13 skipped.
