VERDICT: PASS

I read the diff, the intent and the gate record, which is green. I ran no tests of my own, so what follows rests on reading the code and the tests. There is no `spec.md`, which is normal at Tier 1, so I checked against the intent's outcomes.

## Notes
- Every outcome has code and a test that would fail without it:
  - **Staged deletion:** `deleted_sides()` now falls back to the commits when the deletion is already staged. `test_a_staged_modify_delete_resolution_lands` runs the resolver, then the staging, then `--continue`, in the order a landing runs. It covers both UD and DU, with the carried file staged or only edited.
  - **`UU` deletion (nit -20):** the new `gone` check in `cmd_resolve` refuses a deletion that isn't one side of a modify/delete. `test_a_deleted_both_modified_file_is_refused` covers it deleted by hand and with `git rm`.
  - **Evidence rule (nits -19, -21):** the new test pins the "read, blank line, heading" case, and the docstring now says what the code does.
- **Edge cases handled:**
  - A path staged as kept is excluded, because `ls-files --stage` now lists every index entry and the fallback subtracts them.
  - The commit fallback runs only while a rebase is under way, since `REBASE_HEAD` outlives its rebase.
  - `carried` is now judged by whether a moved file's text is neither side's (`_neither_side`), so staged and unstaged edits are treated the same.
- **Move of `_rebasing`:** it went from `landing.py` to `factory.py` so `deleted_sides()` can call it without a circular dependency. All callers and the one test that used it were updated.
- **Context pass:** `AGENTS.md` doesn't describe the `--continue` internals this diff changes, so there is no `[context]` finding.
- **Tests run:** none. I relied on the gate record `build/round-1.gate.md`, which is PASS (`./check.sh`, exit 0).

- NIT: plugins/factory/scripts/landing.py:2829: `staged_gone` calls `git cat-file` once per staged deletion; harmless, but you could read `REBASE_HEAD`'s tree once. {robustness S low}
