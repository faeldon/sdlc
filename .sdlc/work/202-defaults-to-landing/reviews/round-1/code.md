Still reviewing: I've read the spec, the gate record and the core diff. The gate passed, and `decisions` runs before `verdicts` in the build skill, so a SETTLED default is already ticked when `uncarried()` reads the ledger. I found no blocking problems and am writing up the review.

VERDICT: PASS

## Notes

- NIT: plugins/factory/scripts/run_state.py:104: `uncarried()` reports `named` (an id in both SETTLED and CONFIRM) only when the id is also CONFIRMed. A default that is open and listed as SETTLED but not ticked, because `decisions` was skipped or refused it, reads as "no `- CONFIRM:` line". The mend text then points the approver at the wrong fix. Naming the SETTLED line in that case would be clearer. {robustness S low}
- Done well:
  - CONFIRM is read in one place (`approver_weighing`), and a CONFIRM on an ESCALATE counts for nothing (R5).
  - The sensitive-path and `closes:` bars are enforced twice: the approve prompt stops offering CONFIRM, and `loop_state()` mends a READY that carries one anyway, once, then stops as a rerun.
  - The landing's `_dispose()` and `land_signals()` are left unchanged, and `by=auto` stays refused, since an assumed default is still a signal.
  - Tests came first: golden prompt copies, parametrized mend cases, a rerun test.
  - The R12 docs were updated alongside the code, in AGENTS.md, the README, the approver and build/decide skills, and ship's side file.
- I did not run any tests. I read the gate record (`build/round-1.gate.md`: PASS, `./check.sh` exit 0) and the factory, landing and run_state diffs, and skimmed the tests that bear on R2, R3 and R5. I did not read the golden prompt files or the R6–R12 tests line by line.
