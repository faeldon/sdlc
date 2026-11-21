VERDICT: PASS

The rebase's only conflict was `tests/fixtures/close-output.json`. The landing took main's side, so that file is not in the change's diff and the masked `Sdlc-Runtime: plugin=<version>` line is kept. Nothing else in the tests moved since round 2 passed, so the requirement-to-test map from rounds 1 and 2 still holds.

## Notes

- **Gate:** `build/land-1.gate.md` is PASS. `./check.sh` exited 0, with 3676 passed and 29 skipped, and `claude plugin validate --strict` passed. I did not run any test myself.
- **Checks:** I did not run either check in `checks.md`. Both are still sound as acceptance checks.
  - **AGENTS.md map (R10):** it greps four strings. They match today, and each fails if the Updates paragraph is removed.
  - **README skill table (R15):** it greps for the `/sdlc:update` row. It matches today and fails if the row is removed.
  - Both leave the tree unchanged.
- **Well covered:** `tests/test_update.py` has 22 tests, the recorded `tests/fixtures/plugin-list.json` and the one-hook pin in `tests/test_skills.py`. `tests/test_readiness.py` covers `uncommitted`.
- NIT: tests/test_update.py:107: the fake `claude` opens its log and rows files without `encoding="utf-8"`. This is carried over from round 2 and only matters on a non-UTF-8 locale, since the test isn't portable. {tests S low}
