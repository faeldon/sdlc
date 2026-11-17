VERDICT: CHANGES

- CHANGE: scripts/board.html:255 (the `li` built in `mdList`, line 322-323): each task checkbox is a `disabled` input with no accessible name, because the item's text is a sibling and not a label. A screen reader user hears "checked checkbox" with nothing said about which task it is. Give the input the item's text as its name, for example `aria-label` set to the item's words, or wrap the words in a `<label>`. Keep it disabled, since the spec says never clickable.

## Notes

**What I read.** The two screenshots (1280×800 and 390×844). `intent.md`, which is Tier 1 and has no `spec.md`, and `decisions.md` (D1–D5). `reviews/land-1/ux.md` and `build/land-2.gate.md` (`GATE: PASS`, 2340 passed). `scripts/board.html` in full: the CSS for `.md` and `.d-raw`, the drawer markup, `mdLink`, `mdInline`, `mdBlocks`, `renderMarkdown`, `paint()`, `show()`, and the focus trap. `tests/test_board.py` lines 1750–1857. `tests/fixtures/board/changes/005-draft-sharing/reviews/round-1/code.md`. The REFERENCE.md lines about the drawer.

**What I could not see.** This session has no shell, so I could not run `git diff e26da2f…HEAD` or check whether main moved. I read the changed files at their current state instead. `build/land-2.md` is not in the change folder (only `build/land-2.gate.md`), so I could not read the builder's conflict notes. Both screenshots show the board only, because the shot command never opens the drawer (D5). I judged the rendered markdown from the renderer's code and the fixture, not from a picture.

**Smaller findings** (land-1 points still standing, none reworked this round):
- The Raw button still hides while each file loads. `show()` sets `doc = null`, and `paint()` derives `d-raw.hidden` from the loaded text, so it flickers on every file pick. Derive it from the path ending in `.md`.
- A refused link (`span.md-refused`) explains itself only in a `title` tooltip, which keyboard and touch users never see.
- Every code block is labelled "code" and every table "table", so a screen reader gives identical landmarks when a file has several.
- Links that open a new tab do not say so in their accessible name.
- D3 says Raw "stays as set while the drawer is open". The code also keeps it across openings, since `raw` is never reset. The code's behaviour is probably the better one, but the decision's wording should match it.

**What the change does well.** Every node is built with `h()` and `textContent`, and the hostile-markup test checks `<script>`, `<img onerror>`, `javascript:`, `data:` and mixed-case `JavaScript:` links. The focus trap skips the hidden Raw button, so Tab never lands on an invisible control. Code and table boxes scroll inside themselves at 390px and are named tab stops.
