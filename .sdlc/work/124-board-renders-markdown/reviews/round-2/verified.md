- KEPT: ux: C1: scripts/board.html:570: an empty `.md` file (`doc.text` is `""`) renders an empty `div.md` in the markdown branch at line 569, so the pane is blank. No empty-file note exists. An empty non-`.md` file also gives a blank `pre`, because `??` keeps `""`.

## Notes
I only read `scripts/board.html` and ran nothing. The `tabindex` and `role="region"` fix from the settled item is already in the code: line 364 sets it on the table, and the CSS at lines 158–159 covers focus for both the table and `pre.md-code`. I did not check the `pre.md-code` markup in the renderer. I did not re-judge the settled items.
