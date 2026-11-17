The docstrings in `scripts/sdlc.py` are fixed, with no code changes. The gate passes (1998 tests) and so do the three new acceptance checks. Everything is left uncommitted on branch `102-sdlc-docstrings`.

**No `plan.md`:** the prompt said Tier 2, but `intent.md` says `tier: 1` and the change touches only one file, so the intent's Approach is the plan.

**Open question (cut the subcommand list, or keep it and pin it with a test?):** I took the cheaper answer from the Approach and cut it. The module docstring now gives the module's purpose and says `sdlc.py -h` lists the subcommands and `sdlc.py <subcommand> -h` gives one's arguments. I checked that `-h` lists all 41 subcommands, each with a line of help, so no test is needed.

**What changed (one slice):**
- **`_drop_record()`:** "Why not, or / None" now reads "Returns why it failed, or None once the commit is made; a failure aborts the merge and leaves main as it was."
- **`work/` → `.sdlc/work/`** in the docstrings of the module, `change_dirs()`, `next_id()`, `claim()`, `cmd_uninstall()` and also `stamp_shipped()`, which the seed didn't name. `_seed_title()` keeps `→ work/<folder>`: that is the old heading format in older intents, and the code splits on that exact text.
- **Rewrapped** three lines that went over 100 characters after the rename.

**Proof:** these are docstring-only outcomes that only a deliberate revert could break, so they are acceptance checks in `.sdlc/work/102-sdlc-docstrings/checks.md`, not suite tests. All three failed before the edits and pass now. They check that:
1. `_drop_record`'s docstring no longer has the half sentence and says what it returns.
2. No docstring calls the folder `work/`, except `_seed_title`'s old-heading pointer.
3. The module docstring names `sdlc.py -h` and no longer has the subcommand table.

**Left in `notes.md`:** one unticked item. Six `#` comments in `sdlc.py` still say `work/`. They aren't docstrings, so I left them for a later change.

`.sdlc/work/inbox.md` was already modified when I started (entry 2026-11-17-27 marked `[building]`). That isn't my edit, and I didn't touch it.

No decisions to raise.

## Evidence

```
$ uv run --quiet --script scripts/sdlc.py accept 102     (before the edits)
"name": "No docstring calls the change folder work/", "exit": 1, "passed": false
"name": "The module docstring points at -h instead of listing subcommands", "exit": 1, "passed": false
"passed": false
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 102 | grep -E '"name"|"passed"'     (after)
      "name": "_drop_record's docstring says what it returns, whole",
      "passed": true,
      "name": "No docstring calls the change folder work/",
      "passed": true,
      "name": "The module docstring points at -h instead of listing subcommands",
      "passed": true,
  "passed": true,
exit: 0

$ ./check.sh
All checks passed!
1998 passed in 64.21s (0:01:04)
✔ Validation passed
exit: 0
```
