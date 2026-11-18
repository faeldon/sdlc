VERDICT: PASS

No Critical or Required finding in this landing round. The rebase resolution is sound, and the landing record is written where the landing commands say it is.

## Notes

- **The conflict resolution loses nothing.** `git diff 12a2c3d HEAD -- .sdlc/work/inbox.md` is +24 lines and no deletions. The base entries `-12` to `-16` are intact, and this change's `-17` to `-20` follow them with unique ids.
- **Carried points are not raised again.** D1 to D6 are confirmed in `decisions.md`, so I reviewed against them. The round-2 kept findings C1 and C3 (a stopped landing at `shipped` names `/sdlc:ship`, which `sdlc.py ship` refuses) and C4 (raw stop reasons on the card) are carried as seeds `2026-11-18-19` and `-20`. The ESCALATE history is in `decision.md`.
- **Worth knowing, not a finding:** `_record_land(root, folder, "rebase")` in `cmd_land`'s re-landing branch (`plugins/factory/scripts/factory.py:4580`) runs before `land-<n+1>` is created. So the rebase that starts round 2 is recorded as `ROUND: 1`, and the board shows "landing L1" until the gate writes L2. `test_land.py` pins that `("rebase", 1, 1)`. It reads as deliberate, since round 1 is the one under way until its successor opens. Say if you want the rebase labelled with the round it starts.
- **Checked and fine:**
  - The record is in the commit that `land`, `land --close` and `resolve --continue` make, and the tree is clean afterwards.
  - `gate --land` records before the tree is hashed.
  - Board samples for `land-gate`, `land-review` and `land-verify` split correctly at the approver.
  - The pinned copies of `read_land_step` and `LAND_AT` match the factory's `LAND_STEPS`.
  - `board.html` builds the landing track with `textContent`.
  - `.card.landing-stopped` comes after `.card.ready`, so it wins.
- **Context docs:** `docs/REFERENCE.md` and `plugins/factory/README.md` still tell the truth; the new text is accurate, though see the two nits below.

- NIT: plugins/factory/README.md:381: the paragraph's reflow leaves a 139-character line, and the wrap at 382 is a lone `pre-approved);`. Rewrap the paragraph to the file's width. {docs S low}
- NIT: docs/REFERENCE.md:550-551: `A click opens` ends its line and `click opens` starts the next, so the sentence is split across a short line and a long one. Rewrap it to the file's width. {docs S low}

**Tests and commands run**
- `uv run --group dev pytest -q -p no:cacheprovider -n auto tests/test_board.py tests/test_land.py`: 249 passed, 14 skipped.
- The builder's `./check.sh` in `build/land-1.md`: 2451 passed, 14 skipped, plugin validation passed. I did not rerun the full gate.
