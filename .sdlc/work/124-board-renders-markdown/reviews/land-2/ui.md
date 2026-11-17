VERDICT: CHANGES

The two screenshots show the board with the drawer closed, at 1280 and 390 wide. Nothing overflows or overlaps there. The drawer, where the markdown renders, is not in either image (D5, settled), so the rendered file is judged from the CSS and renderer as they stand. I had no shell, so I could not run the diff. I read the changed files as they are in the worktree.

- CHANGE: scripts/board.html:138: a file's top-level `#` heading renders at 20px (`.md .md-h1`), larger than the drawer's own title at 15px (`.d-head h3`, line 113). A change's `intent.md` opens with `# 124 — …`, so its title outranks the drawer's title and the page's hierarchy inverts. Bring `.md .md-h1` down to 15px or below, or raise the drawer title above it, so the drawer title stays the top of the page. Not verified in a render; the values are read from the CSS.

## Notes

- Screenshots read: `land-2/ui/index-1280x800.png` and `index-390x844.png`. Both show the board with the drawer closed. The columns and cards fit at both widths.
- Checked the `.md` rules for overflow and both themes. Code blocks and tables scroll inside themselves (`overflow-x: auto`), with `tabindex` and a focus outline. Colours are tokens (`--chip`, `--line`, `--muted`, `--accent`), so both themes pick them up. Blockquote and muted text stay readable against the panel in both.
- Smaller: frontmatter (`pre.md-front`, line 155) has no `overflow-x` and no `tabindex`, unlike `pre.md-code`. A long frontmatter line scrolls the pane sideways with no keyboard stop. The fixture files have no long frontmatter lines, so this is a real-world case only.
- Smaller: the `.md` line height is 1.55 (line 135) and the raw `.doc pre` is 1.5 (line 128). A single value would keep the two views in step.
- Smaller: the `.md-table` and `pre.md-code` focus outlines use `outline-offset: 2px` (line 159), while `.doc:focus-visible` uses `-2px` (line 127). Pick one.
- Done well: the drawer's `.md` prose is capped at `72ch`, so a long review line stays readable on the desktop width, and a refused link keeps its words, with no broken layout.
