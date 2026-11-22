VERDICT: PASS

## Notes
- Tier 1 change, so there is no `spec.md` or `plan.md`. I reviewed against the Outcome section of `intent.md`.
- Correctness: `QUOTED` strips one matching pair of quotes before `PINNED` is checked.
  - A quoted SHA pin with `# v4.4.0` passes.
  - A quoted tag or branch is refused.
  - A mismatched pair (`"…'`) is refused, because `QUOTED` doesn't match and `PINNED` then fails on the leading quote.
  - A quoted `./…` value is skipped like an unquoted one.
  - The test covers all of these.
  - The `portable` marker is unchanged.
- The `VERSION` regex is unchanged, and the docstring now gives the Dependabot reason for it.
- The change touches only `tests/test_ci.py`, which is what the intent said.
- NIT: tests/test_ci.py:20: `QUOTED` is a module-level regex used only in `unpinned()`. That matches the file's own `USES`, `PINNED` and `VERSION` pattern, so there is nothing to change. {style S low}
- Done well: the test includes the mismatched-quote case, which the intent didn't ask for, and it pins the "right answer for the right reason" behaviour.
- I ran no tests. The gate record `build/round-1.gate.md` reads `GATE: PASS`.
