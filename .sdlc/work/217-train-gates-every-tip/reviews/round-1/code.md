VERDICT: PASS

Each requirement has code and a test. I read the gate record (`build/round-1.gate.md`), which shows PASS from `./check.sh`. I ran no tests of my own and did not read the new `tests/test_train.py` tests (R1–R4, R6), so I did not check that they fail without the fix. Their pass is inferred from the green gate.

## Notes

- R1–R4: `_train_gate()` no longer returns early for a one-change train. The gate now runs on the committed, stacked commit, and the existing `_read_gates()` ledger check now covers a train of one. The change is minimal and reuses the existing gate, eject and record paths.
- R6: `_ungated()` reads the base branch's config on each reading and is not stored in the train's state. It is added to both the reading and `_run_end()`, in the live and cleared branches.
- R7: `land_question(..., gated=True)` leaves the gated wording byte for byte as before. `cmd_land_check()` reads the check from the base branch, and the test confirms a check in the change's own config does not stand in.
- R8 and R9: the skill's Step 3 and Step 4, the `cmd_gate` and `cmd_land` comments, and the `REFERENCE.md` sentence are all updated. The spec's grep for the old wording returns nothing.
- NIT: `plugins/factory/skills/land/SKILL.md` Step 3 and Step 4: the lines you edited run past the file's roughly 100-column wrap (the "`gates`, `ungated`, …" line and the Step 4 "When `ungated` is set…" line). Re-wrap them. {style S low}
- Context docs: nothing in `AGENTS.md` or `.sdlc/` says something false after this diff.
