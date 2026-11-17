I resolved all five conflicted files, keeping both sides' work in each. No conflict markers are left, I ran no git command, and `./check.sh` passes with 2018 tests.

While I was building, the base branch landed three things that met this change: nits a change takes in are now retired when it lands, the landing's own record is amended into the commit before a second rebase, and a resolved conflict counts as a signal only until a reviewer has seen it.

**`plugins/factory/scripts/factory.py`**
- **From the base branch:**
  - `resolved_files()` and `resolution_signals()`, and the conflict signal they produce, which replaces the old plain check for `runs/land-resolved`.
  - The nit helpers (`named_nits()`, `retire_nits()`) and `land_message()`'s `nits` argument.
  - Picking the nits up in `cmd_land`.
  - The refactor of `land-verdicts` into `land_verdict()`, with its new `settled` reading.
- **From this change:**
  - The landing parts and proposals (`land_parts()`, `read_proposals()`, `unrecovered()`).
  - The `accept` and `cases` commands.
  - `land`'s refusals and writes before ship. Its single up-front preflight call replaces the base's second one, and the base's "no `findings.md`" write of the `Fresh review:` line becomes my version, which adds the line whenever it's missing.
  - The assumed-decisions signal.
- **Combined:**
  - `land_signals()` takes this change's signature, with both docstrings merged.
  - The commit message now has, in order: body, `Retired nits:`, `Carried forward:`, `Dropped:`, `How to recover:`, then the trailers. Ship also puts `Retired nits:` straight after the body.
- **One semantic merge.** git merged my `accept` step into the base's `land_verdict()` cleanly, but the base had added `settled`: a reviewed round's result stands even after the landing's own amend moves `HEAD`. My acceptance-check result compared against `HEAD` and ignored that, so a change with checks would have kept its "resolved conflict" signal after its review passed. `_accept_state()` now takes `settled` and reads it the way `_land_gate_state()` does.

**`plugins/factory/skills/land/SKILL.md`**
- The signal list keeps the base's "a resolved conflict no reviewer has seen" and its explanation, and adds checks, cases and undone notes.
- Step 3.1 keeps the base's nit retirement (`retired_nits`, `Retired nits:`) and the note that a second landing adds the earlier landing's record to its commit first. It adds the refusals and the dispositions written on the person's yes.

**`plugins/factory/README.md`**
- The signal list now holds the base's wording for a resolved conflict plus checks, cases and undone notes. It keeps this change's account of what the yes approves.
- The base's nit retirement, in the paragraph's first sentence, is untouched.

**`.sdlc/work/inbox.md`**
- Both sides deleted entries, and I kept both deletions. The base removed bugs 2026-11-17-31 to 34, which its changes fixed. This change's ship removed seeds 2026-11-17-35 and 36, which it grew from.

**`tests/test_land.py`**
- Both sides only appended new tests, with no names in common. I kept the base's (close reading the first modified path, second landing, nit retirement, resolution signals) followed by this change's.

## Evidence

$ uv run --group dev pytest tests/test_land.py tests/test_factory.py tests/test_skills.py -q -n auto
529 passed in 17.59s
exit: 0

$ ./check.sh
All checks passed!
214 files already formatted
2018 passed in 42.49s
✔ Validation passed
exit: 0
