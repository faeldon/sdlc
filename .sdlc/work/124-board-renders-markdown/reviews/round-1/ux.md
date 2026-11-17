VERDICT: CHANGES

- CHANGE: scripts/board.html:338 and :361: a fenced code block or table wider than the drawer scrolls only with a pointer in some browsers (Safari does not make an overflowing box a tab stop, and notes.md flags the same gap), so a keyboard person can't reach the cut-off part of a long line or a wide table. Give each `pre.md-code` and each `.md-table` `tabindex="0"` and a name (`role="region"` with an `aria-label` such as "code" or "table"), so the box takes focus and can be scrolled from the keyboard. The existing `:focus-visible` outline style on `.doc` can be reused.

## Notes

**Read:** both screenshots (`index-1280x800.png`, `index-390x844.png`). They show the board's index only: the seven columns, the Needs you cards and the 390px stacked layout. Neither shows the drawer or any rendered markdown, so the rendered view is judged from the source. Also read `intent.md`, `decisions.md` (D1 to D5), `notes.md`, `scripts/board.html` in full, `tests/test_board.py` from line 1750, the fixture `reviews/round-1/code.md`, and `board.py`'s `_files()`, which gives the relative paths that link resolution depends on. There is no `spec.md`, since this is Tier 1; the intent's Approach stands in for it.

**Agreed with D5.** The index shots don't open the drawer, so the rendered fixture is seen by no reviewer. The person should open a `.md` in the drawer at 390px and at 1280px before ship.

**States I couldn't see, and how I judged them:**
- Loading: `paint()` shows a bare `…` until the file arrives. It's brief on localhost, but it says nothing (smaller finding 2).
- Error: "`path` can't be read (status)." is in words and the Raw toggle is hidden. Fine.
- No files: "This folder holds no file yet." Fine.
- Empty `.md` file: renders a blank pane with no words, because the empty-folder message only covers a folder with no files (smaller finding 5).

**Smaller findings:**
1. The toggle's visible word is "Raw". With `aria-pressed` the state is announced, but "Raw" doesn't say what pressing it does. "Raw text" or "Show raw text" would.
2. `…` while loading: "Loading `path`…" would say what is happening.
3. A refused link is dotted-underlined text whose reason ("not followed: …") appears only as a hover tooltip. A tap or keyboard user gets no reason. The refusal itself is right; the underline suggests a link that does nothing.
4. The file's `#` renders at 20px, larger than the drawer's own 15px title, so the file's heading outranks the change it belongs to.
5. An empty `.md` file shows a blank pane (see the states above).

**Done well:**
- Frontmatter sits apart as a dimmed block, and the task checkboxes are disabled and carry their state in text.
- Scheme links are refused, and in-folder links open in the drawer with focus moved to the pane, so the keyboard path through the file survives a link.
- Escape closes the drawer and the focus trap now covers the rendered links, because the `a[href]` selector matches them.
- At 390px the file list stacks above the document and the code and table boxes scroll in themselves; the page itself doesn't widen.
