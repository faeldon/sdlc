VERDICT: PASS

The change reads well at both widths. The header now names the repo ("drafts — open changes"), and `document.title` follows it. `board.html` writes both with `textContent`, which matches the board's no-HTML-strings rule.

## Notes
- I read `index-1280x800.png` and `index-390x844.png`, and the `repo` handling in `board.html`.
- At 1280px the header is one line and the title is the most prominent thing on it. The status, time and totals sit beside it in the muted style the board already used.
- At 390px the header wraps cleanly, and the status text and totals go onto their own lines with no overflow or clipping. Only the Needs-you column shows in the narrow view, which is the board's existing behaviour.
- A very long repo name could crowd the header at phone width. The screenshots use a short name, so I couldn't check this. A `overflow-wrap` on `h1` would cover it, but I'm not requiring it.
- The change does well to reuse the existing `h1` and status styles, so it adds no new classes or hard-coded colours.
