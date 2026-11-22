VERDICT: PASS

The gate record (`build/round-1.gate.md`) is green. I also ran the seven `ask_says` tests by name and they pass.

## Notes
- Requirements walked:
  - **Reviewer default, never built → `rebuild`.** `unbuilt_defaults()` and `cmd_ask()` do this, naming the lines in `unbuilt`. `test_ask_says_rebuild_for_a_reviewer_s_default_never_built` drives 216's case, for both an ESCALATE and a READY.
  - **Builder's own default stays kept.** The same test asserts `ship` for a builder default.
  - **BUILT line rules.** The parametrized test covers a later-round report, the raising round's own report, and a line naming another id.
  - **Builder text.** The builder, decide skill and README wording is in place, and a skill-text test pins it.
- The two open decisions (D1: an explicit `- BUILT: D<n>` line; D2: autopilot left for later) are reasonable defaults, and I raised nothing against them.
- NIT: `plugins/factory/README.md:82-83`: the edited line runs past the file's wrap width. {style S low}
- NIT: `plugins/factory/scripts/factory.py:2325`: a `source` that doesn't match `round N` (such as a supervisor's) is treated as raised in round 0, so any `- BUILT:` line counts as built. That is lenient but harmless. A short comment would say so. {docs S low}
- Done well: the check reads only the files in the change folder, so `ask` stays read-only. The tests cover the negative cases (same round, wrong id) as well as the positive ones.
