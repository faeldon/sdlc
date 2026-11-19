VERDICT: PASS

Every requirement R1–R13 has a test that would fail without it. R14 is prose, and the diff matches the spec.

## Notes

- **R1:** `test_the_board_names_its_repo_by_id_not_by_path` checks three things. A worktree's id equals the main checkout's id. A second repo's id differs. No home-path variant appears in the body.
- **R2 and R5:** the existing `test_a_second_board_reports_the_first_and_anything_else_is_refused` is unchanged.
- **R3:** `test_another_repos_board_is_a_refusal` starts two repos' boards. It asserts no `serving` key in the output, the port and "another repo's board" in the refusal, and that the first repo's own board still reads `already`.
- **R4:** `test_a_board_that_names_no_repo_is_a_refusal` serves a stand-in `state.json` with no `repo_id`.
- **R6:** `test_the_dashboard_skill_offers_another_port_on_a_refusal` reads Step 1's text. It also asserts the command line is unchanged.
- **R7:** `test_a_held_run_lock_marks_a_train_card_unattended` takes the lock on its own descriptor. A train card reads `true`. An ejected card and a card outside a train read `false`. After release the train card reads `false` again.
- **R8:** `test_land_step_alone_never_claims_a_live_loop` covers both a missing lock file and a free one.
- **R9:** `test_reading_the_run_lock_creates_nothing_and_holds_nothing` checks that the file stays missing and that a free lock can be taken right after `state()`.
- **R10:** `test_no_train_no_lock_probe` stubs the probe. It also checks the probe is called once per read, however many train cards there are.
- **R11:** `test_the_page_says_unattended_only_from_the_lock` asserts the text appears once, in `progressRow`, on `p.unattended`.
- **R12:** `test_the_run_lock_name_is_a_pinned_copy` compares `board.TRAIN_RUN_LOCK` with `factory.landing.TRAIN_RUN_LOCK`.
- **R13:** `test_the_board_writes_nothing` now has a train card under way, so the board tries the lock, and it compares a listing of the git common dir before and after.
- **R14:** the `board.py` docstring, REFERENCE.md and both AGENTS.md spots (*The board* and *The factory*) were edited and match the code.
- **DECISION:** the person's yes on taking the lock briefly (the spec's open item) is not a test matter.
- **Gate:** `build/round-1.gate.md` records GATE: PASS from `./check.sh`, with `3062 passed, 28 skipped`.
- **Test run:** I ran the 11 tests this change added or extended, each selected by name with `-k`: `11 passed`.
- **`checks.md`:** the change has none.
- NIT: tests/test_board.py:660: `_bare_repo` creates a repo with no `user.name` or `user.email`. It passes on this machine, but may fail on a clean CI box. Reuse the `repo` fixture's git config if it sets one. {tests S low}
