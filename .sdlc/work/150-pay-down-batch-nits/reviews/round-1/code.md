VERDICT: PASS

## Notes
- All of the intent's items are in the diff, and each has a test or a check:
  - -57: the `ui` pass's `why` now ends with `factory.py shots NNN --round 1 --role ui` when `sdlc-factory` is enabled. `test_preflight_passes_ui` checks the exact text both with the factory off and on. `ui.md` says ship never runs it.
  - -72: `_terms()` and `_defused(text, root)` in `factory.py`, and `_hand_terms()` in `sdlc.py`. They read `terms.local` from the main checkout and write `<term>`. `test_a_reply_quoting_a_local_term_is_filed_as_a_placeholder` covers the factory side and `test_the_placeholders_are_the_factorys` pins the `sdlc.py` copy.
  - -53, -54 and -55: AGENTS.md is reflowed, the "111 C1" label is replaced with the rule it pins, and the two `supersedes` sentences are wrapped. No added line in AGENTS.md runs past 100 columns.
  - The other nits (-56, -58, -59, -48, -51, -52, -62, -63) are each in the diff. The `_own_folder` possessive `*` has a regression assert.
- D1 and D2 (the builder's two open defaults in `decisions.md`) are reasonable, and I assumed both. The full `shots` command works as pasted, and `terms.local` holds no kinds, so a generic `<term>` is enough.
- The gate record is green (`build/round-1.gate.md`, `./check.sh`, exit 0).
- NIT: `plugins/factory/scripts/factory.py:3050`: `_terms()` accepts a term that matches the empty string, such as `a*`, and `re.sub` then inserts `<term>` between every character. `test_nothing_local` takes the same lines, so it fails on them too. Skipping a term that matches `""` would be cheap hardening. {robustness S low}
- Done well: `test_the_placeholders_are_the_factorys` pins `sdlc.py`'s copy of the term reader to the factory's, and `TERM_MARK` is never printed with a term. The `test_a_reply_quoting_a_local_term…` test also checks that `defuse`'s JSON output never quotes the term.
- I ran no tests myself and relied on the gate record.
