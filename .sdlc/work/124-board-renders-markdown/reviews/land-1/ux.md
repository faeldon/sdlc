VERDICT: PASS

No CHANGE and no DECISION. Every path the spec describes works from the source: a card opens the drawer, the first file (`intent.md`) shows rendered, and a `.md` file picked from the list shows rendered. Checkboxes are disabled, links to other files open in the drawer, and web links open in a new tab with `rel="noopener noreferrer"`. Nothing in a change's file is parsed as HTML.

## Notes

**What I read.** The two screenshots (1280×800 and 390×844), `intent.md` (Tier 1, so no `spec.md`), `decisions.md` (D1–D5), `build/land-1.md`, `scripts/board.html` in full, `tests/test_board.py` lines 1–1036 and 1637–1858 (the markdown section), `tests/fixtures/board/changes/005-draft-sharing/reviews/round-1/code.md`, and the REFERENCE.md lines that mention markdown. This session has no shell, so I could not run `git diff`. I read the changed files at their current state instead, and I checked the markdown tests against the page's source.

**What I could not see.** Both screenshots show the board only. The shot command never opens the drawer (D5), so no rendered markdown appears in them. I judged the rendered output from the renderer's code and the fixture, not from a picture. The empty-file blank pane is already filed as idea `2026-11-18-8`, and I did not raise it again.

**Smaller findings:**
- The Raw button hides while each file loads. `show()` sets `doc = null` and `paint()` then sets `d-raw.hidden`, so the button disappears and comes back on every file pick, including a `.md` to `.md` link. Set its visibility from the path's `.md` ending rather than from the loaded text.
- A refused link (`span.md-refused`) shows its target only in a `title` tooltip. A keyboard or touch user never learns why the link does nothing. Consider showing the target in text, or saying "not followed" in the words.
- Each code block is labelled `code` and each table `table`. In a file with several of either, a screen reader user hears identical landmarks. A language or a number in the label would tell them apart.
- D3 says Raw "stays as set while the drawer is open". The code also keeps it across openings, since `raw` is never reset. That is probably the better behaviour, but the decision's wording and the code disagree, so one of them should change.
- Links that open a new tab do not say so. A short "(opens in a new tab)" in the link's accessible name would help.

**What the change does well.** Every construct is built with `h()` and `textContent`, and the hostile-markup test covers `<script>`, `<img onerror>`, `javascript:`, `data:` and `JavaScript:` links. The `.md pre.md-code` and `.md-table` boxes scroll inside themselves at 390px and are named tab stops. The focus trap skips the hidden Raw button, so Tab never lands on an invisible control.
