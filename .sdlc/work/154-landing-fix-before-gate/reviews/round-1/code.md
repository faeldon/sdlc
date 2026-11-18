VERDICT: PASS

Every outcome in the intent has code and a test, and the gate record (`build/round-1.gate.md`) is green. The change folder has no `spec.md`, since it is Tier 1, so I reviewed against the intent's Outcome and Constraints.

- **Fix named before the gate:** `_train_reading` now returns `fix` for the change inside the stacking loop, after its stack or conflict resolution and before `_train_gate`. The old step 5 placement is gone.
- **Landing test:** `test_a_fix_the_gate_needs_is_made_before_the_gate` uses a check that fails until `aa.txt` says `AA`, and the person's fix makes it so. It asserts `fix` is named before any gate, exactly one gate runs, nothing is ejected, both changes land, and the fix is in the change's own commit.
- **Round handling:** `cmd_land_fix` now takes a landing round that no reviewer has answered and that has no ask yet. Otherwise it opens round n+1 as before. This is what lets the fix be asked right after the stack. The "round hasn't passed" refusal still holds for an answered round, and `test_a_fix_commit_needs_an_ask` covers both cases.
- **Constraints:** the fix is still asked once, because the `land_ask is None` test keeps a second ask from reusing the round. It is still amended through `_amend_record`.
- **Docs and loop:** the land skill's `yes, with a fix` text and its `fix` step bullet say the fix comes before the gate. The `cmd_train` docstring says the same. `train --run` follows the reading, so it needs no separate change. A search of `plugins/`, `docs/`, README and `.sdlc/SDLC.md` found no leftover "at close" wording for the fix.

## Notes

- NIT: plugins/factory/scripts/factory.py:5880: `any((folder / "reviews" / f"land-{n}").iterdir())` raises if the round's folder is missing; `land_round` presumably only counts existing folders, so it is safe today. Guarding with `.is_dir()` would make that explicit {robustness S low}
- Done well: the stand-in test asserts "no gate before the fix" through the train state, not only the final outcome.
- I ran nothing. I read the diff and the gate record only.
