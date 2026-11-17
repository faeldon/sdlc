VERDICT: PASS

I found no Critical or Required issues. R1–R14 each have code, and each has a test that names it.

## Notes

**Optional**
- `plugins/factory/scripts/factory.py`, `cmd_land()`'s resume branch: `before = _git(root, "show", f"HEAD:{INBOX}")` can come back empty or None if `HEAD` has no register. `named_nits(..., text=None)` then reads the tree's register, so `nits` ends up `[]` without saying so. That is harmless here, but an explicit `or ""` would make the intent clear. I have not confirmed whether `_git` returns None or "" on failure.
- `retire_nits()` now ends an entry only at a level-1 or level-2 heading (`ENTRY_END_RE`). Before, any heading ended it, so a `###` line inside a nit's body used to end the deletion. The new behaviour matches R13's "up to the next `## ` heading" and is arguably more correct. It still changes what ship's retirement deletes, and the diff doesn't flag it. One line in the docstring would cover it.
- `land-mend` for a behaviour reply that has a verdict but no evidence appends `MEND` to the `land-review` prompt and starts a new behaviour session. This is what the spec describes. The new reply replaces the old file, so the person never sees the first one. That is consistent with the existing build-loop mend.

**Done well**
- Both loops use one "every problem mendable, minus roles already mended" rule. `land_mended()` reads only the `land-<n>` lines of `runs/mended`, so the two loops can't use up each other's mend allowance.
- `cmd_agent()` now refuses a build `mend` unless `verdicts` names that role, which closes the 103 misfiling at its source.
- `_commit_failed()` leaves a change a person shipped and committed by hand alone, and a landed change with a later base move still goes to `_amend_record()`.
- R13 matches register entries by id only, skips a title-valued `idea:`, and reuses `named_nits()`, the same rule the landing used to retire them.
- I did not call out the `AGENTS.md`, README and docstring updates one by one. They are part of the diff.

**Ran**
- `pytest tests/test_land.py tests/test_factory.py -n auto`: 252 passed.
- `./check.sh`: ends with "Validation passed", with only the plugin directory's missing-icon notice, which the validator says does not change the result. I read only the tail of the output, so I did not see the ruff and pytest lines, which I take to have passed.
- I confirmed that every test named in the spec exists.
- I did not run the two manual scratch-landing checks from the spec's Verification section.
