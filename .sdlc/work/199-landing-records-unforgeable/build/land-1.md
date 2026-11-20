I made both parts of the fix, and the full gate passes (3619 passed, 29 skipped, lint and plugin validation clean). I ran no git commands.

**Check after the slot wait** (in `cmd_gate`, in both `factory.py` and `sdlc.py`):
- Once the slot wait and the check are over, and before the earlier record is read for its attempt count and earlier text, each gate now checks again that the record is vouched for.
- If someone rewrote the record by hand meanwhile, the gate refuses, naming the file and saying to remove it. The new attempt isn't recorded, the file is left as it is, and the ledger gets no line.
- The refusal before the slot still stands, so nothing runs on a record that was already forged.
- **Tests:** `test_records_ledger.py::test_a_record_forged_while_the_gate_ran_is_never_appended_to` and `test_hand_gate.py::test_a_hand_gate_record_forged_while_it_ran_is_never_appended_to`. In each, the check command itself copies a forged record over the genuine one. Both failed before the code (each gate exited 0) and pass now.

**Docs:** `plugins/factory/README.md`, `docs/REFERENCE.md` and `plugins/factory/skills/land/SKILL.md` now say the ledger protects against an agent's Edit and Write tools, which work in the change's worktree. They also say it does not protect against a shell command that can reach the git common dir, which could add lines to the ledger itself.

**Two edits beyond what you named:**
- **`checks.md`:** its acceptance check still grepped for the old wording, so it now greps for the new phrases in all three docs, and it passes.
- **Formatting:** ruff reformatted one assert in my new test.

A code comment in `factory.py` (line 2898) still uses the old "a write in a worktree" wording. I left it because the fix named only the three docs.

## Evidence

$ uv run --group dev pytest -q tests/test_records_ledger.py::test_a_record_forged_while_the_gate_ran_is_never_appended_to tests/test_hand_gate.py::test_a_hand_gate_record_forged_while_it_ran_is_never_appended_to
E       assert (0 == 1)
E       assert (0 == 1)
2 failed in 0.75s
exit: 1

$ uv run --group dev pytest -q tests/test_records_ledger.py::test_a_record_forged_while_the_gate_ran_is_never_appended_to tests/test_hand_gate.py::test_a_hand_gate_record_forged_while_it_ran_is_never_appended_to
2 passed in 1.64s
exit: 0

$ sh -c "<the sh block of .sdlc/work/199-landing-records-unforgeable/checks.md>"
exit: 0

$ uv run --group dev pytest -q -n 8 tests/test_records_ledger.py tests/test_hand_gate.py tests/test_feature_map.py tests/test_skills.py
497 passed in 7.31s
exit: 0

$ uv run --group dev ruff format tests/test_records_ledger.py
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 199
All checks passed!
347 files already formatted
3619 passed, 29 skipped in 196.26s (0:03:16)
✔ Validation passed
✔ Validation passed
exit: 0
