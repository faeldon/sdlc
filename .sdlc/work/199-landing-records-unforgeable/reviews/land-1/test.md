VERDICT: PASS

The fix does what the person asked, and both new tests fail without it.

## Notes

- **Docs:** `plugins/factory/README.md`, `docs/REFERENCE.md` and `skills/land/SKILL.md` now say the ledger protects against an agent's Edit and Write tools, which work in the change's worktree. They also say it does not protect against a shell command that can reach the git common dir. "The README" is read as the factory's README, the one that describes the ledger.
- **Recheck in `cmd_gate`:** both `factory.py` and `sdlc.py` check again that the earlier record is vouched. The check comes after the slot wait and the run, before the earlier record is read for its attempt count and earlier text. On failure the gate refuses, leaves the record untouched and adds no ledger line. The first check, before the slot, still stops a record that was already forged.
- **Tests that can fail:** `test_records_ledger.py::test_a_record_forged_while_the_gate_ran_is_never_appended_to` and `test_hand_gate.py::test_a_hand_gate_record_forged_while_it_ran_is_never_appended_to`. In each, the check command itself copies a forged record over the genuine one, so the forgery lands during the run. Each asserts exit 1, the refusal text, the record left byte-for-byte as forged, and no new ledger rows. The builder's evidence shows both failing before the code with `assert (0 == 1)`, so they test the change.
- **Gate:** the gate's record for this build is `build/land-1.gate.md`: `GATE: PASS`, 3619 passed, 29 skipped. I read the record and did not run the suite.
- **Run:** I ran the two named tests above in the foreground and both passed: `2 passed`.
- **`checks.md`:** the one section greps the docs for `records ledger`, `sdlc-factory-records.jsonl`, `Write tools` and `can reach the git common dir`. I did not run it. The greps match phrases in the diff's README, REFERENCE.md and `SKILL.md` text, so I expect it to pass once those edits are present. It would fail if the new wording were reverted, and it leaves the tree unchanged.
- NIT: plugins/factory/scripts/factory.py:2898: the ledger's code comment still says "It guards against a write in a worktree", which is looser than the docs now say; word it as Edit and Write tools, not a shell that reaches the git common dir {docs S low}
