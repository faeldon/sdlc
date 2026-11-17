All three corrections are built, and the full gate passes (2191 tests passed, 9 skipped). The work is left uncommitted for `/sdlc:ship`.

**Slices built** (I wrote a `plan.md` even though this is Tier 1, because the Approach touches four files):

1. **The themes rule (2026-11-17-66).** The listing is done in the skill, not the script, so the rule went into `skills/idea/SKILL.md`. The `--themes` pass now runs `sdlc.py status --all` and leaves out every entry in its "N being built" list. That list is what an open change's `idea:` or `fixes:` line names, plus legacy `[building]` tags. If status prints no *Next up* section, every open idea or bug is being built, so the skill has nothing to propose and stops. I added an `allowed-tools` rule for `status *`. Status's existing tests already cover the script side: `test_status_counts_and_lists_what_is_being_built` and `test_next_up_lists_what_open_changes_build`.
2. **The six comments (2026-11-17-65).** These are the comments above `ENTRY_RE`, `OPEN_ITEM_RE`, `DOC_TEMPLATES`, `config`'s `"work"` key, `LAST_ID` and the trackers section. They now say `.sdlc/work/`. The `config` comment also claimed a `work/ideas.md` fallback the script no longer has, so I took that out. I left `_seed_title()`'s ` → work/<folder>` alone: it's a docstring that describes an older heading format on purpose. Nothing but comments changed.
3. **Tracker docs (2026-11-17-28).** CONTRIBUTING's *Writing a tracker* section now covers each intake method core calls when a tracker has `intake()`. It says what each returns and which command calls it: `intake`, `dangling`, `titles`, `open_numbers`, `open_marks` (optional), `mark`, `needs_info` and `closed_by` (optional). The intent listed `unmark()`, but core never calls it, so the docs say so.

**Tests:** I added `test_idea_themes_leave_out_what_status_lists_as_being_built` to `tests/test_skills.py`. It checks that the `--themes` pass runs `status --all`, that the skill allows that command, and that the old rule (leave out only `[building]` tags) is gone. I saw it fail first because the `status --all` run was missing. The comment and docs outcomes are covered by two acceptance checks in `checks.md` instead, since only a revert could break them. Both pass, and both were run against the files as changed, not against the old text.

**`plan.md`:** this is the first version. It records the choice to put the rule in the skill and the decision to keep `_seed_title()` as it is.

**`notes.md`:** one unticked item. `recorded_issues()`'s docstring names `unmark()` among the methods that set its records, but core never calls it. Either wire it in where a record is withdrawn, or drop it from the docstring.

- DECISION: [default] Document `unmark()` as GitHub's own method, not part of core's interface? Options: name it as "core doesn't call it yet"; leave it out; wire it into core in this change. Going ahead with naming it, since the intent listed it but no core path calls it, and wiring it in would add behaviour this change's constraints rule out.

## Evidence

$ uv run --group dev pytest tests/test_skills.py::test_idea_themes_leave_out_what_status_lists_as_being_built -q   (before the skill edit)
tests/test_skills.py:728: AssertionError
FAILED tests/test_skills.py::test_idea_themes_leave_out_what_status_lists_as_being_built
1 failed in 0.46s
exit: 1

$ uv run --group dev pytest tests/test_skills.py::test_idea_themes_leave_out_what_status_lists_as_being_built -q
1 passed in 0.04s
exit: 0

$ uv run --group dev pytest tests/test_skills.py -q -n auto
351 passed in 1.86s
exit: 0

$ git show HEAD:scripts/sdlc.py | grep -cE '^[[:space:]]*#.*[^/]work/'
6
exit: 0

$ grep -nE '^[[:space:]]*#.*[^/]work/' scripts/sdlc.py
exit: 1

$ uv run --quiet --script scripts/sdlc.py accept 116
  "passed": true,
  "problems": []
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0

$ ./check.sh
All checks passed!
2191 passed, 9 skipped in 135.80s (0:02:15)
✔ Validation passed
✔ Validation passed
exit: 0
