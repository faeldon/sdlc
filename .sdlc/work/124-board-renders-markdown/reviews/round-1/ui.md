VERDICT: PASS

PASS with a note: no screenshot shows the change itself. Both shots are of the board index, and the rendered markdown is inside the drawer, which `factory.py shots` never opens (the builder's D5 says the same). Nothing I could see on the index is broken at 1280 or 390, and the change's CSS reads as sound, but I have not seen a rendered `.md` file at either width.

## Notes

Screenshots read: `index-1280x800.png` and `index-390x844.png`. Both show the board, with the drawer closed. I also read `scripts/board.html` (the `.md` CSS at lines 134–161, `paint()`, `show()`) and `intent.md`, `decisions.md` (D1–D5).

What I checked by reading the CSS, not by sight:
- The `.md` rules use the page's tokens (`--line`, `--chip`, `--accent`, `--muted`, `--ink`), so the rendered file follows the light and dark themes the way the rest of the page does.
- At 390px, `pre.md-code` is `white-space: pre` with `overflow-x: auto` and the tables sit in `.md-table` with `overflow-x: auto`, so wide code and tables scroll inside themselves. `.doc` has `overflow: auto`, so it doesn't push the page sideways.
- `.md` caps the line length at `72ch`.

Smaller findings:
- `scripts/board.html:138`: `.md .md-h1` is 20px, and the drawer's own title (`.d-head h3`) is 15px. A file's `#` title therefore outranks the change title above it. Consider 15–16px for the h1 so the drawer title keeps the top of the hierarchy.
- `scripts/board.html:146`: `.md li.md-task input` uses a negative left margin (`-1.3em`) to hang the checkbox. That depends on the checkbox's default width, so check it in the real drawer before relying on it.
- The intent's Approach asks for a fixture `.md` that "the ui reviewers' screenshots show rendered". D5 records that the shot command can't do this. The gap is real, and D5 already holds the question open, so I have not raised it again. If the person wants drawer shots, a fix belongs in the shot step, not in this change.
- The `.d-raw` button sits in `.d-head` with `flex-wrap`, so it wraps at 390px. Reasonable, but it is unseen.
- Drawer screenshots at 1280 and 390, opened on `reviews/round-1/code.md` from the fixture, would settle the rendering, the h1 weight and the checkbox alignment in one pass.

What the change does well: it keeps every rendered node on `h()`/`textContent`, and it marks refused links with dotted underlines and a tooltip, so the state is not carried by colour alone.

PREEXISTING: none seen in the two index shots.
