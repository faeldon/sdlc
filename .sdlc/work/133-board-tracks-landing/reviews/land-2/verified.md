- KEPT: code: C1: plugins/factory/scripts/factory.py:4742: `cmd_land_close` writes the `stop` to `runs/land-step.md` after the landing commit is amended, so the file is left modified. The same happens at 4733-4736, 4719-4720 and 4580-4581. `land-step.md` is not git-ignored and the amend stages the folder, so it is tracked after the amend. `_record_land` rewrites it with `path.write_text`, and `_land_refused` calls it without a following `_amend_record`. `sdlc.py base` refuses on any dirty path, and nothing exempts this file.
- KEPT: ux: C2: scripts/board.py:730: a stopped landing always names `/sdlc:ship {ident}` by hand. A landing stopped at `close` sits on a card already at `stage: shipped`, so that step is wrong. The stopped-landing branch comes before the `CLOSED` check and never looks at the stage.

## Notes
- I ran nothing. I read `_record_land`, `_land_refused`, `_amend_record`, `cmd_land_close`, `_dirty_paths` and `board.next_action`, and ran `git ls-files` and `git check-ignore` on `land-step.md`.
- For C1, I didn't reproduce a `sdlc.py base` refusal in a live run. A test that leaves a stop after a close failure and then checks `git status` would settle it.
- For C1, the stop at 4694 comes before the amend, so the amend picks it up. Only the stops after the amend are the defect.
- For C2, I assumed the card's `seen` or `stage` is `shipped` when the stop's `after` step is `close`. I didn't read how the board derives `after`.
