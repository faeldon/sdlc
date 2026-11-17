---
id: 116
slug: register-and-docs
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 116 — Correct the work/ comments, idea's themes and the tracker docs · plan

> Tier 1, but the intent's Approach reaches four files, so the build wrote its plan down after
> reading the code. Read by the review alongside the intent.

## Files to change

- `scripts/sdlc.py`: comments only. The six `#` comments that call the change folder `work/`:
  above `ENTRY_RE` (the register), `OPEN_ITEM_RE` (notes.md's carry to the register),
  `DOC_TEMPLATES`, `config`'s `"work"` key (which also names `work/ideas.md` as a fallback the
  script no longer has: `register_path()` is `inbox.md` alone, `OLD_INBOX` is read only from
  history), `LAST_ID`, and the trackers section. Each says `.sdlc/work/` (or "the change's folder")
  instead. `_seed_title()`'s ` → work/<folder>` is a docstring naming an older intent's heading,
  history read on purpose: left as it is.
- `skills/idea/SKILL.md`: the `--themes` pass reads `sdlc.py status --all` and leaves out every
  entry its *being built* list names, which is `next_up()`'s `building`: an open change's `idea:`
  or `fixes:` line, or a legacy `[building]` tag. The listing is the skill's (no script lists
  themeless entries), so per the intent's Approach the rule goes in the skill, reading status
  rather than a copy. A new `allowed-tools` rule for `status *`. When status prints no *Next up*,
  no idea or bug is open beyond those being built (`_next_themes()` counts every ready and waiting
  one, a themeless one under `(no theme)`), so there is nothing to propose.
- `docs/CONTRIBUTING.md`, *Writing a tracker*: the intake methods core calls, which commands
  `_intake_tracker()` gates on `intake()`, and close's record step, which calls `mark()`,
  `open_marks()` and `open_numbers()` whenever `mark()` exists (review round 1), each with what it returns and which command calls it: `intake()`, `dangling()`,
  `titles()`, `open_numbers()`, `open_marks()` (optional), `mark()`, `needs_info()`, and
  `closed_by()` (optional, `status`'s unpushed count). Found from `scripts/trackers/github.py` and
  the call sites in `sdlc.py` (`_intake_tracker()`, `cmd_intake()`, `_closes_report()`,
  `mark_issues()`, `cmd_close`'s record step, `cmd_sync()`, `cmd_ask()`, `unpushed()`).
  `unmark()` joins the list as optional (round 3, the person's R1): see below.
- `scripts/sdlc.py`, round 3 (the person's R1, "wire unmark"): `cmd_sync()` sends back to triage
  each issue that left the change's `closes:` line. Where the tracker has `unmark()` and
  `open_marks()`, core lists the open issues' marks once and calls `unmark()` on each issue still
  marked triaged that carries this change's marker (`<!-- sdlc:intake:<name> -->`, which core's
  own `mark()` left), isn't on the line, and that `recorded_issues()` doesn't record otherwise (an
  entry, another change, a verdict): so an issue a person labelled by hand, or one another record
  now holds, is never touched. The comment is core's, `closes_texts()`'s new `withdrawn`, under
  `<!-- sdlc:withdrawn:<name> -->`. A drop already reaches `unmark()` through `archive()`
  (GitHub's `_settle()`, with core's `dropped` text), so nothing changes there. Not in the full
  marking pass: close's pass runs once the folder has left `main`, while its `Closes #N` push may
  be still to come, and would send a just-fixed issue back to triage. `recorded_issues()`'s
  docstring, which named `unmark()`, is now true.
- `tests/test_skills.py`: one test pinning the themes rule.
- `tests/test_archive.py`: one test for the sync's unmarking.
- `docs/REFERENCE.md`, the intake paragraph: sync sends back an issue that left a change's line.

## Work order

1. **Themes rule**: the test first (red), then the skill's paragraph and its `allowed-tools`
   rule (green). The script's side, that `status --all` lists an entry an open change's `idea:` or
   `fixes:` names, is already pinned by `test_status_counts_and_lists_what_is_being_built` and
   `test_next_up_lists_what_open_changes_build`.
2. **Comments**: reword the six; the gate shows no behaviour moved.
3. **Tracker docs**: the intake list in CONTRIBUTING.md.
4. **Round 3, unmark wired**: the test first (red), then `cmd_sync()`'s step and the
   `withdrawn` text (green), then CONTRIBUTING's `unmark()` line and REFERENCE's paragraph.

## Tests

- `test_idea_themes_leave_out_what_status_lists_as_being_built` (new, `tests/test_skills.py`):
  the `--themes` pass runs `sdlc.py status --all`, leaves out what it lists as being built, and
  names the `idea:` and `fixes:` lines as what marks one; the skill grants that command. Proves the
  intent's second outcome and its "a test pins the themes rule".
- `test_sync_sends_an_issue_that_left_the_closes_line_back_to_triage` (new,
  `tests/test_archive.py`): an issue taken off the line loses `triaged` and its parent, with one
  comment however often sync reruns; one still on the line, one another record holds, and one a
  person labelled by hand keep theirs. Proves R1.
- The comment and docs outcomes are text a revert alone would undo: acceptance checks in
  `checks.md`.

## Rollback

`git revert` undoes the repo's side. What it can't undo: a sync run with the new code may have
taken `triaged` off, and commented on, an issue that left a change's `closes:` line. Undo by hand
(`gh issue edit N --add-label triaged`, and delete the comment), or by putting the issue back on
a line and syncing.
