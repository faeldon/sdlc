VERDICT: PASS

The kept change is done. `AGENTS.md:138` now reads "runs the host's `retro.evidence`, `retro.indicators` and `retro.test_times` (`_evidence()`, the only place they run)". This round's rework touched only `AGENTS.md`, so I didn't re-review the rest.

## Notes
- Test command: `uv run --group dev pytest -q -n auto` ran 2364 passed and 13 skipped, with no failures.
- `checks.md`: I didn't re-read it this round, since the rework didn't touch it.
