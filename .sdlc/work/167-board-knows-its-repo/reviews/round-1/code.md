VERDICT: PASS

## Notes
- All 14 requirements have code and a test that would fail without it.
  - R1: `_repo_id`, in `test_the_board_names_its_repo_by_id_not_by_path`.
  - R2–R5: `cmd_board`, in the three refusal and "already" tests.
  - R6: `skills/dashboard/SKILL.md`, in `test_the_dashboard_skill_offers_another_port_on_a_refusal`.
  - R7–R10: `train_run_held` and `_mark_unattended`, in the lock tests.
  - R11: `progressRow` in `scripts/board.html`, in `test_the_page_says_unattended_only_from_the_lock`.
  - R12: the pinned `TRAIN_RUN_LOCK` copy, in `test_the_run_lock_name_is_a_pinned_copy`.
  - R13: the extended `test_the_board_writes_nothing`, which now compares the git common dir before and after.
  - R14: the board docstring, REFERENCE.md and AGENTS.md.
- Contract:
  - `sdlc.py` is untouched, so a running board that reloads `board.py` but keeps an old `sdlc.py` won't break.
  - The board opens the lock read-only, with no `O_CREAT`, and `msvcrt` is imported only inside `_release`.
- Done well: `unattended` sits on each card rather than at the top of `state.json`, so the page's redraw key sees it change. `_land_progress` also defaults it to `False`, so every landing card has the same shape.
- I ran no tests. `build/round-1.gate.md` records `./check.sh` as passing.
- The spec asks for the person's yes on the brief two-syscall lock take (*Contracts touched*). That is an approval for the person at ship, not a finding.
- NIT: `scripts/board.py` `train_run_held`: on Windows, `msvcrt.locking` on a read-only handle is untested here, because the portable tests that hold the lock run only in CI's Windows job. The spec already names this as an accepted risk, and any failure reads as "not held". {tests M low}
