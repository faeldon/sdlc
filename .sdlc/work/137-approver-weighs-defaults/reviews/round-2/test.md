VERDICT: PASS

All three changes kept from round 1 are made, and each has a test that fails without it. The full suite passes.

## Notes

- **Board next step at `test`** (`scripts/board.py:636`): `decide_step()` gives `/sdlc-factory:decide NNN for <ids and defaults>, then /sdlc:ship, or /sdlc-factory:land…`. The tests are the PRECEDENCE rows "escalation pending" and the new "defaults to confirm", the `BOTH` row, and `test_an_escalation_names_the_decision_it_still_needs_first`. `defaults to confirm` is the case that previously skipped the confirmation. `build` keeps "in the factory's supervisor", and the existing "decision pending" row pins that.
- **Status "What needs me"** (`scripts/sdlc.py:4383`): the line gets `  /sdlc-factory:decide NNN`, pinned by `test_status_ends_with_what_needs_me`, which expects `041  decide D3, confirm 2 defaults  /sdlc-factory:decide 041`. The 004 and 013 lines get no suffix, which the same test pins. A defaults-only status line has no test of its own. It runs through the same `decide_step()` that the board test covers for defaults-only, so I'm not asking for one.
- **`decide/SKILL.md` refusals**: Step 0 now says what to do instead. For a change not at `test`, answer the blocking decisions in the `/sdlc-factory:build` session, or wait until the run reports it ready. For a bad or unknown NNN, `/sdlc:status` lists the open changes and the ones under `■ What needs me`. `test_decide_says_what_to_do_instead_when_ask_refuses` pins both. It checks substrings of the wording, but it fails if the guidance is removed.
- **R2 and R10 on the board** are covered by `test_a_ledger_with_alternatives_is_not_garbled` and `test_an_escalation_with_only_settled_defaults_is_not_answered`.
- **Copies of the parsing:** `test_the_factory_parsing_is_a_pinned_copy` now pins `board.SETTLED == factory.SETTLED`.
- **Acceptance checks:** there is no `checks.md` for this change, and none is needed.
- **Test command:** `uv run --group dev pytest -q -n auto` gave 2457 passed, 17 skipped, no failures.
