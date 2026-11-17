VERDICT: PASS

The round-1 CHANGE is done. A mend now leaves a record in `runs/mended`, `loop_state()` reads it, and `cmd_agent` refuses a second mend. Those are the three pieces the CHANGE asked for. The fix is a little more precise than the suggested `runs/<role>.mended`: the marker is keyed by role and round, so a new round can mend again.

## Notes

- Optional: a behaviour reply that lacks both its verdict line and `## Evidence` gets only the verdict mend. `_task` returns `VERDICT_MEND` alone. The marker then records `behaviour <round>`, so the evidence problem left behind reads as `rerun`, not `mend`. This is a safe stop with a clear `way`, and it's no worse than before the change. Consider having `VERDICT_MEND` also ask for the evidence when it's owed, or leaving the one-mend rule as it is and saying so in the skill's `stop` step.
- Optional, carried from round 1: no test covers the empty aside commit (D3). `test_resolve_skips_a_commit_the_base_already_holds` only covers a non-empty aside. D3 is still `[ ]` in `decisions.md`, so the person hasn't confirmed the skip-over-undo reading.
- Nit: `plugins/factory/skills/build/SKILL.md`, the `way` sentence in the `stop` step, still ends a wrapped line on "with" and continues on the next line ("…`rerun` otherwise) with its / sentence…").
- Nit: AGENTS.md's changed paragraph still wraps unevenly. The line that begins "mended that round is a `rerun` stop…" runs well past the others, and the line carrying "checks.md" is also long.

## Done well

- The marker is written only after `_claude` returns a reply and the target is written, so a failed session records nothing and stays retryable. That matches "never retried".
- `loop_state()` and `cmd_agent()` both read the same `mended()` and `mend_round()`, so the two can't disagree about what counts as mended.
- `test_a_reviewer_s_preamble_is_mended_by_the_same_reviewer` walks the whole chain: preamble → mend → the loop reads `approve` → preamble again → `rerun`, `mend: []`, and a refused second mend with no new claude call. `test_the_builder_s_evidence_is_mended_once_a_round` covers the builder's evidence mend the same way.

## What I ran

- `uv run --group dev pytest -p no:cacheprovider -q -n auto tests/test_factory.py tests/test_skills.py tests/test_defaults.py`: 597 passed. This includes the two new tests and `test_a_stop_names_its_way`, which still passes.
- `ruff check --no-cache` on `factory.py` and `tests/test_factory.py`: passed. `ruff format --no-cache --check` on the same two files: already formatted.
- I did not run `./check.sh` in full. `claude plugin validate --strict`, `test_adoption` and `test_windows` are unverified here.
- The behaviour-reply interaction in the first note is from reading `loop_state()` and `_task()`, not from a test run.
