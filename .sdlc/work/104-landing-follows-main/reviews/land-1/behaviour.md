VERDICT: PASS

The change does what the spec says, and I found nothing that fails. I did not run the spec's `preflight 104` step (spec Verification), which would show whether the land skill's cases are in scope.

## Notes
- **checks.md:** the change has no `checks.md`, so there are no acceptance checks to read.
- **Gate:** `build/land-1.gate.md` is green. I didn't rerun the gate.
- **Rebase:** the base has 0 commits the branch lacks (`git rev-list --count HEAD..refs/heads/main` printed 0), so the rebased tree is current.
- **Named tests:** all nine tests the spec names exist in `tests/test_land.py`: R1/R3 move-then-rebase, R4 race, R5 both bound tests, R8 fix and no-command-line-words, R10 fix-needs-ask, R12 auto refusal, R13 hand edit.
- **End-to-end path:** `tests/test_land.py`, `tests/test_skills.py` and `tests/test_metrics.py` pass (498 passed). The land tests cover the whole chain: a `moved` return, the re-entry rebase, the gate, review and pass, then `Close`. They also cover the fix path and the `unreviewed=` trailer.
- **Skill wiring:** `SKILL.md` carries the `land-fix` rule, names `land.moves` and has the fix substep. The `land-fix` command takes `--ask` and `--commit`, and the ask comes from `decisions.md` as R8 says.
- **Not run:** the Windows `portable` subset and the paid eval cases. Neither was needed for this behaviour check.

## Evidence
$ git rev-list --count HEAD..refs/heads/main
0
exit: 0

$ uv run --group dev pytest tests/test_land.py tests/test_skills.py tests/test_metrics.py -q -n auto
498 passed in 50.84s
exit: 0

$ grep -c "def <each named test>" tests/test_land.py
1 for each of the nine tests
exit: 0

$ grep -n "land.moves\|land-fix" plugins/factory/skills/land/SKILL.md
18, 51, 96, 216-218, 236 matched (the allowed-tools rule, the config key, the fix substep)
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py land-fix --help
options: --ask ASK (the person's fix in decisions.md (R1): open its round), --commit (amend the builder's fix in)
exit: 0
