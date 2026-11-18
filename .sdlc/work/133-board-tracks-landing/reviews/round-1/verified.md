Confirmed all three.

- C1: `_record_move` only writes `runs/land-moves`. It never updates `land-step.md`, so the record keeps `STEP: close` with the old count.
- C2: `stage in CLOSED` returns `/sdlc:close` before it looks at the land record.
- C3: a landing stop goes in `progress`, not `entry["stopped"]`. So `next` and the `.card.ready` class are unchanged, and the reason is the raw `ship refused` output.

- KEPT: code: C1: plugins/factory/scripts/factory.py:4476: a moved landing leaves `land-step.md` at `STEP: close` with the old move count, because `_record_move` doesn't rewrite it
- KEPT: ux: C2: scripts/board.py:723: a shipped landing still under way gets `/sdlc:close` as `next`, not the landing's own step
- KEPT: ux: C3: scripts/board.py:725 and scripts/board.html:446-454: a stopped landing keeps the ready styling and the unstopped `next`, and shows its reason as raw output

## Notes
I only read code (`factory.py`, `board.py`, `board.html`) and ran no tests. For C3, the `.card.ready` styling comes from the card's column. I didn't check whether a stopped landing in `test` lands in another column.
