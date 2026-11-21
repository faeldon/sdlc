VERDICT: PASS

Every requirement R1–R8 has a test that would fail without the change. R9 is comments and docs, which no test covers; the spec's grep and the doc pass cover it. I didn't wait for my own run of the named new tests: it passed the 120s foreground timeout and was moved to the background. The verdict rests on the gate record and my read of the diff.

## Notes

- **Gate record:** `build/round-1.gate.md` reads `GATE: PASS`. It ran `./check.sh` (exit 0, 287.9s, tree unchanged). I didn't run the suite myself.
- **R1:** `test_a_train_of_one_is_gated_at_its_tip[still|rebased]` drives the train until `gate` or `close` appears. It asserts `next == gate`, `prefix == 1`, `of == 1`, and `stacked == pre`. The `rebased` case uses a fast-forward `--ff-only` merge of a moved base, as `fresh` leaves it. It would read `close` without the fix.
- **R2:** `test_a_train_of_one_whose_commit_fails_the_check_is_ejected` uses a `git ls-files` check. The build's gate passes on the untracked file, then the train gate fails on the committed one. It asserts:
  - `cause: gate`, with `land-1.gate.md` and `exit 1` in the reason;
  - the base tip unmoved and no `Close` commit;
  - `undo: null` and a clean worktree;
  - `GATE: FAIL` and the `ejections.jsonl` row amended into the change's commit.
- **R3:** `test_a_green_train_of_one_records_its_tip_gate` asserts `gates == 1`, `ungated is None`, `GATE: PASS` in `land-1.gate.md` and `TIP GATE: PASS` in `land-train.md`.
- **R4:** the `gate-of-one` parametrization of `test_train_run_stops_on_a_hand_written_record` covers the ledger check for one change.
- **R5:** the diff changes no existing multi-change assertion.
- **R6:** `test_a_landing_with_no_check_says_it_ran_no_gate` checks `ungated` in both the reading and the exit JSON, and R3's test asserts it null with a check.
- **R7:** `test_the_landing_question_names_only_what_the_batch_holds` has the exact ungated string and the default-equals-gated assertion. `test_land_check_words_an_ungated_question[no-check|check]` also plants a check in the change's own config on the no-check case, so it proves the base branch's config is the one read.
- **R8:** `test_land_reports_an_ungated_landing` checks Step 3 for `` `gates`, `ungated` `` and Step 4 for `ungated` and "how many times the tip was gated".
- **Checks:** the change has no `checks.md`, so there are no acceptance checks to judge.
- **Tests run:** none of my own. The named-test run was backgrounded and not awaited.
- NIT: tests/test_train.py:1546: the `# fmt: skip` on the parametrize decorator exists only to keep the table on one line; a plain `ids=` list would format normally {style S low}
