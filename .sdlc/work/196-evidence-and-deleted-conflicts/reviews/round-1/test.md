VERDICT: PASS

No requirement lacks a test that would fail without it, and I found no test that can't fail. The gate's record is green.

## Notes

**Requirement-to-test map:**
- **Outcome 1** (a read printing `## ` lines owes no `exit:`): `tests/test_evidence_headings.py`.
  - `test_a_read_printing_headings_owes_no_exit` uses 189's report shape. I traced it through the new `read_evidence()` loop and it returns `[]`, and it would be flagged before the change.
  - Evidence stays strict: `test_the_commands_after_a_read_printing_headings_are_still_checked` still flags a later command with no `exit:`.
  - A heading after an `exit:` still ends the section (`test_a_heading_after_an_exit_ends_the_section`).
  - A read that printed nothing before a later heading still owes its `exit:` (`test_a_silent_read_before_the_next_section_still_owes_its_exit`).
- **Outcome 2** (a modify/delete conflict reaches the resolver):
  - `test_a_modify_delete_conflict_reaches_the_resolver_and_lands` is parametrized over both `UD` and `DU`. It runs the train to `resolve` and checks the prompt names the deleting side, the `:2:` or `:3:` stage, the diff command and the moved file.
  - The same test checks that `--continue` keeps the deletion, stages the carried edit, names both paths in the `land-resolved` marker, and that the train lands.
  - `test_a_modify_delete_resolution_outside_the_moved_files_is_refused` checks an edit outside the moved files is still refused.
- **`train-resolve-deleted` prompt:** the new fixture is pinned in `tests/test_prompts.py`.
- **Nit 2026-11-20-8** (`by_alts` built only from entries with real alternatives): `tests/test_decision_alternatives.py` files two decisions that share one option apart.

**Checks in `checks.md`:**
- **Resolver instructions:** a `grep` for the new resolver paragraph. It would fail without the change, can fail, and leaves the tree unchanged.
- **Nit 2026-11-20-9** (`GREP_FOLLOWS_MIN` constant and its use): a `grep` for the constant and its comparison. It is sound for the same reasons. I confirmed by reading the diff that both lines are in `landing.py`, and I did not run either check.

**Gate:** `build/round-1.gate.md`, `./check.sh` exit 0, "3470 passed, 29 skipped". I ran no tests myself.

- NIT: tests/test_evidence_headings.py:1: a read whose printed heading follows a blank line (the `## Speed` line in 189's report) is only covered by the one combined case, so a regression to the blank-line rule would show up only there {tests S low}
