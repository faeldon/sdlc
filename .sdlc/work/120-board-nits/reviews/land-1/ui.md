VERDICT: PASS

The change fits at both widths, and the wrap and wording fixes read as intended. This is a light-theme pass only, since no screenshot shows the dark theme.

## Notes

**Screenshots read:** `land-1/ui/index-1280x800.png` and `land-1/ui/index-390x844.png`. Both show the board with cards 001–010 and the needs-you column. I checked the card 006 `next:` line at 390px (the one the intent's wrap outcome is about), card 003's gate-red next step, and the needs-you wording ("needs you: stopped: rerun to ask an agent again"). None of them overflows its card. The 390px shot is cropped at the bottom, which is the viewport, not a layout fault.

**Styling read:** `scripts/board.html` now puts `overflow-wrap` on `.next code` (line 80), `.needs`, `.flag`, `.title` and `.d-head h3`. That covers the intent's `.next code` case and the other long-text slots on the card. All colours come from the existing tokens (`--stop`, `--ink`, `--muted`), so the change uses the page's own styling system.

**Themes:** the page ships a `prefers-color-scheme: dark` block (lines 19–23), and no screenshot shows it. The needs-you red is `--stop`, which the dark block sets to `#ff8a80` on the `#1a1e24` panel, so the contrast should hold. This is a check I could not run here.

**Smaller findings:**
- At 390px the card 006 `next:` line breaks inside `sdlc-factory` after the hyphen, so one line starts with `factory:build`. It is legible and stays inside the card. D5 settles the line count, so I am not raising it again.
- The `/sdlc–factory` dash in the screenshot is the monospace font's rendering of the hyphen, not a markup problem.
- I could not run `git diff` (no shell in this session), so my review of the change rests on the changed `board.html` rules and the build's land-1 report, not the full diff.

**Done well:** the wrap fix covers every long-text slot on a card, not only the one the seed named, and it does so with no new colours or sizes. Each needs-you line is worded as an instruction, which fits the other needs on the board.
