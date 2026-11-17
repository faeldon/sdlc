VERDICT: PASS

## Notes

- **Optional:** `skills/intent/SKILL.md` Step 0 now has one very long line ("the register, the file `config`'s `work.register` names, if there is one, for a seed that matches…"). Rewrap it to match the neighbouring lines. No test fails on it.
- **Optional:** `next_up`'s `holder` map is keyed by entry title. That matches how the rest of the function keys things, but two entries with the same title would share a holder. Duplicate titles are unlikely, and the code was already keyed this way, so I'm not raising it as a change.
- **Not checked:** the R2 control asserts only `returncode == 1` and `resolvable is True`, so it proves the old tag edit conflicts. That is enough to keep the test from passing vacuously.
- **Done well:**
  - Every requirement R1–R9 has code and a test that can fail. For example, the R2 test pairs a no-conflict branch with a control branch carrying the old tag edit.
  - `_claimed_by()` replaces the inline expression in `_inbox_commit`'s refusal, so there is still one reader of `_open_claims()`.
  - Legacy `[building]` tags are kept as before, with `change: None`.
  - The docs and `templates/inbox.md` match the code. `drift` reports nothing.
- **Ran:** `./check.sh` (ruff, format, 2009 tests passed, plugin validate passed) and `sdlc.py drift` (clean). I did not run the Verification section's manual `status`, `status --all` and `bugs` commands.
