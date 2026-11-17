VERDICT: CHANGES

- CHANGE: .sdlc/work/inbox.md:312-337: the landing dropped seed `2026-11-17-85` (`[bug]`, "The factory's ui and ux reviewers can't run at once"). Main still holds it at its line 355; this branch doesn't. It belongs to neither this change's six seeds nor seed 75, so the conflict resolution removed it by mistake, and `build/land-1.md` says everything else from the base is untouched, which isn't so. Fix: restore the `## [2026-11-17-85]` entry verbatim from `main`'s `.sdlc/work/inbox.md` and place it after seed 84. Keep the deletions of 52, 56, 57, 58, 69 and 70, and keep 75 absent. The landing would otherwise remove a live bug report.

## Notes

- Code checks out against the spec. Requirements 52, 56, 57, 58, 69 and 70 each have code and a test that would fail without it. `_stopped()` delegates to `sdlc.factory_stop()`, so the card and `status` read an unreadable `runs/stopped.md` the same way. `next_action()` reads `needs` via `sdlc.needs_of()`, which emits `decide` lines only at `build` or at an escalated `test`, so plan and design cards don't change. `entry["change"]` equals the branch name that `refs/sdlc/end/<branch>` is built from, since the rebasing set compares folder names with branches.
- The page changes are CSS only, and the empty column is built with `h()`, so no HTML strings are involved.
- Nit: `next_action()` computes `decide` before it knows whether the card needs it. Harmless, but it reads more simply if it's computed inside the two branches that use it.
- Nit: the `board.py` module docstring reflows awkwardly where the stop sentence was rewritten ("the step the" ends a short line).
- Nit: the seeds added here (81–84) are filed as `pre-existing` and are correct to file, but the 83 text cites `board.py:393` for a line this change doesn't touch; it stays accurate, so no action is needed.
- Done well: each landed seed has a test named for it, and the 086 test is renamed and pinned against `factory_stop()` rather than left to drift.

## Notes on what I ran

- `uv run --group dev pytest -q -n auto tests/test_board.py tests/test_metrics.py tests/test_sdlc.py`: 462 passed, 13 skipped.
- `ruff check` and `ruff format --check` on `scripts/board.py` and `tests/test_board.py`: both clean.
- I didn't run the full `./check.sh` gate. The builder's `build/land-1.md` reports 2208 passed, which I haven't re-run.
- The seed-85 finding comes from `git diff main -- .sdlc/work/inbox.md` and `git show main:` against HEAD. I didn't re-run `sdlc.py check --strict` after the fix; the fix needs to be checked by re-running the gate.
