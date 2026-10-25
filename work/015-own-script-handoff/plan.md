---
id: 015
slug: own-script-handoff
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 015 — Write stages run the change's own script in the plugin's repo · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `_script_cmd()` (how a copy of the script runs), shared with `_handoff()`;
  `OWN_SCRIPT_ENV`, `OWN_SCRIPT_CMDS` (`ship`, `drop`, `base`, `sync`), `OWN_RAN`;
  `_own_script(root)` (the change's own script, or None: env unset, an `NNN-slug` branch,
  `_own_repo()`, `scripts/` edited against the merge base with `main` or untracked there, and not
  the running copy; never raises); `_run_own(script, argv)` (reruns with `SDLC_OWN_SCRIPT=ran`,
  adds `ran` to a JSON report or a line to text, returns None on a crash after a `⚠` line);
  `main()` calls both before dispatch.
- `tests/test_archive.py`: a section on the change's own script.
- `tests/test_adoption.py`: `land()`'s ship, through real `uv run --script`, runs the change's
  own code exactly when the change edits `scripts/`; `_by()` drops `SDLC_OWN_SCRIPT`.
- `docs/CONTRIBUTING.md` ("When a change lands") and `AGENTS.md` (close's paragraph): the handoff,
  its fallback, `SDLC_OWN_SCRIPT=off`, and that skill text still needs `/reload-plugins`.

## Work order

1. `_script_cmd()`, with `_handoff()` using it; close's tests unchanged.
2. `_own_script()` and its tests.
3. `_run_own()` and its tests.
4. `main()`'s call and its tests.
5. `tests/test_adoption.py`.
6. The docs; `./check.sh`.

## Tests

- R1: `test_a_change_that_edits_scripts_runs_its_own` (committed, uncommitted, untracked);
  `test_main_runs_the_changes_own_script_or_carries_on`; `tests/test_adoption.py`'s `land()`.
- R2: `test_no_handoff_when_the_change_leaves_scripts_alone`,
  `test_no_handoff_when_the_running_copy_is_the_changes`, `test_no_handoff_off_a_change_branch`,
  `test_the_variable_stops_a_second_handoff_and_turns_the_first_off`,
  `test_main_never_hands_off_a_command_that_only_reads`.
- R3: `test_a_host_never_runs_a_changes_own_script` (no manifest, another plugin's, unreadable).
- R4: `test_a_json_report_says_the_changes_own_code_ran`, `test_a_text_report_ends_with_which_code_ran`.
- R5: `test_a_change_script_that_crashes_hands_back`, and the `None` case of the `main()` test.
- R6: `test_a_refusal_from_the_changes_own_code_stands`.
- R7: the `off` case of the variable test; CONTRIBUTING names it.
- R8: close's handoff tests in `tests/test_archive.py` and `tests/test_adoption.py`, unchanged.
- R9: the two doc edits.
- Manual, after 015 lands: the next change that edits `scripts/` reports
  `"ran": "the change's own code"` from its `sync`.

## Rollback

`git revert <sha>`. Nothing outside the repo; hosts never run it.
