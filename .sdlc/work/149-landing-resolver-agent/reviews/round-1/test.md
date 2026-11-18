VERDICT: PASS

Every requirement R1–R14 has a test that would fail without it. I read the diff and the gate record, and I ran no tests myself.

## Notes

**Requirement map**
- R1–R3, R9 and R10 are covered by `test_a_train_conflict_goes_to_the_resolver_with_every_change` in `tests/test_train.py`.
  - It checks `--agent sdlc-factory:resolver`, `--session-id` with no `--resume`, and `role == "resolver"` with model `sonnet`.
  - It checks that `builder.sessions` is byte-identical and that the only new cost row is `resolver`.
  - It checks that `resolver.sessions` is committed in `HEAD` and not left dirty.
  - It checks that `notes.txt`, which the replayed commit staged cleanly, is unchanged and passes the fence.
- R4 is covered by `test_train_resolve_runs_no_role_but_the_resolver`. It tries `builder`, `code` and `verifier`, and asserts no `_claude` call and no new `.sessions` file.
- R8 is covered by `test_a_resolution_outside_its_files_is_refused`.
  - The untracked case is `LICENSE.txt` (it isn't tracked in the scratch repo), and the tracked-edit case is `.gitignore`.
  - It asserts the refusal text, no marker, the rebase still under way, nothing staged, the stop line naming `resolve 002 --continue`, and that undoing the edit lets the same resolution through.
- R5 and R6 are covered by `AGENT_TOOLS["resolver"]` and `NEVER_RUNS_CHECKS["resolver"]` in `tests/test_skills.py`. They are exercised by the existing parametrised tests.
- R7 is covered by `test_the_resolver_has_a_model_of_its_own`. It checks the `sonnet` default across tiers and depths, that `[models] builder` doesn't reach it, `models_at`, and an `opus` override with no "unknown role" warning.
- R11 is covered by the new `out["role"] == "builder"` assertion in the existing `land-fix` test.
- R12 is covered by `test_a_resolver_session_is_its_own_role`, which calls `_agent_sessions` on a real commit.
- R14 has one test for each script: `test_a_train_conflict_in_a_non_ascii_path_resolves` (`factory.py`) and `test_a_conflict_in_a_non_ascii_path_is_resolved` (`sdlc.py resolve`). Both use `docs/café.md`.
- R13 is covered by the check in `checks.md` plus `./check.sh`.

**The run:** `build/round-1.gate.md` reads `GATE: PASS`, exit 0, from `./check.sh`: `2838 passed, 28 skipped in 109.41s`. Ruff and `claude plugin validate --strict` also passed. The only warning is the factory plugin's missing icon.

**`checks.md`:** it has one section, "The docs say the builder and the resolver edit…".
- It is a single `sh` block of `grep`s with no writes, so it leaves the tree unchanged.
- I expect it to pass now.
- It would fail on a revert of the docs, which is what it is for.
- I did not run it.

- NIT: tests/test_train.py:976: the fence test mixes tracked and untracked strays in one flow. A failure message won't say which case broke, so the `refused` helper could take a label {tests S low}
