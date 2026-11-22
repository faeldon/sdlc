VERDICT: PASS

The round 2 gate record (`build/round-2.gate.md`) is green. I read the diff and did not run any tests myself.

## Notes
- **D2 (autopilot holds such a change):** `hold_causes()` passes the open ledger lines to `factory.unbuilt_defaults()`. The function only looks at `kind == "default"` lines whose source isn't a builder, so blocking decisions and the builder's own defaults are never held. The cause names the ids it holds on.
- **Reuse:** `unbuilt_defaults()` takes the lines to weigh, so `cmd_ask()` (the kept lines) and autopilot (the open lines) share one rule.
- **Tests:** `test_held_change_and_its_dependents_never_land[unbuilt]` covers the hold, including that its dependents never build. `test_a_reviewer_s_default_a_later_build_made_lands` covers the case where a later `- BUILT: D1` lets the change land, so the hold doesn't overreach.
- **Docs:** the autopilot skill's hold list, the README and the `hold_causes()` docstring all name the new cause.
- **Round 1 nit:** the round-0 reading of a source with no round now has a comment at `factory.py`, so that nit is done.
- NIT: `tests/test_autopilot.py:~984`: the assertion's backslash-continued f-string needs `# fmt: skip` and is hard to read. Two variables, or an `in` check on each part, would be clearer. {style S low}
