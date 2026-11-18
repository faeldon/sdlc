VERDICT: CHANGES

- CHANGE: [contract] plugins/factory/scripts/factory.py:4742: `cmd_land_close` writes a `stop` to `runs/land-step.md` after `sdlc.py close` fails, after the landing commit is already amended, so the change's worktree is left dirty. The same happens unamended at 4694 (the `close` record, before the `landed by=auto` refusals at 4703 and 4706), at 4719-4720 (a `_record_move` refusal), and at 4733-4736 and 4580-4581 when a stop follows a commit. `sdlc.py base` refuses on any dirty path once the base has moved and the branch has its own commits (`_dirty_paths()` and `_status_entries()`, sdlc.py:3641), and `_amend_record()`'s docstring says `base` and `close` must find the worktree clean. The factory's own rerun heals this, because `cmd_land`'s else branch amends it. A person who takes the card's way on by hand, `/sdlc:ship`, hits "commit the work, then run /sdlc:ship again". Fix: after each stop written once the landing commit exists, call `_amend_record(root, folder)` (or write the stop before the amend), and return its refusal if it has one. Add a test that a stop after a moved refusal and after a close failure leaves `git status` clean.

## Notes

**Checked and fine:**
- The conflict resolution touches only `.sdlc/work/inbox.md`, with +24 and no deletions. `-17` to `-20` sit between `-16` and the base's `-21` and `-22`, and the ids are unique.
- `read_land_step`, `land_step_text`, `LAND_AT`, `LAND_STEPS`, `MOVES_RE` and `PROBLEM_RE` match between `factory.py` and `board.py`, and the pinned-copy test covers them.
- `history_samples` splits the rows at the approver. `typical_times` keys `land-<step>/<tier>` match `_land_progress`'s lookup.
- `land_verdict` always returns `problems`, so `--record`'s stop path can't KeyError.
- `board.html` builds the track with `textContent`. The CSS variables used exist in both themes.
- `_record_land` keeps `SINCE:` while step and round hold, and `cmd_resolve` stages the step record into the rebased commit.
- `cmd_gate --land` records before the tree is hashed, as its comment says.

**Settled, not raised again:** D1 to D6 in `decisions.md`; the carried seeds `2026-11-18-19` (C1 and C3, stopped landing at `shipped` names `/sdlc:ship`) and `-20` (C4, raw stop reasons); and the README and REFERENCE line-length nits from `reviews/land-1/code.md`.

**Context:** `docs/REFERENCE.md` and `plugins/factory/README.md` describe the landing track accurately. The `land` skill's `--record` line is correct. I found no `CLAUDE.md` or `AGENTS.md` sentence the diff makes false.

- NIT: scripts/board.py:415: a `runs/land-step.md` left by a stopped landing stays on the card after a by-hand ship or a restart back to build, and `_progress()` reads it at `test` or `shipped` until the next landing command overwrites it. Have `cmd_restart` remove `LAND_STEP`, or have `ship` do so, and pin it with a test. {robustness S med}
- NIT: plugins/factory/scripts/factory.py:4580: the else branch of `cmd_land` writes `rebase` for every re-run on a landed change, even when the base hasn't moved and `state` stays `current`, so the card says "landing, at rebase" for a rebase that didn't happen until the gate writes its record. Write `rebase` only when `base` reports `rebased`. {robustness S low}

**Tests and commands run:** `uv run --group dev pytest -q -p no:cacheprovider -n auto tests/test_board.py tests/test_land.py tests/test_skills.py` at HEAD: 606 passed, 14 skipped. I did not rerun the full `./check.sh`; the builder's `build/land-2.md` evidence shows it passing (2451 passed, 14 skipped, plugin validation passed). Nothing was written, committed or run beyond these read-only tests.
