---
id: 026
slug: github-intake
kind: plan
created: 2026-10-26
updated: 2026-10-26
---

# 026 — GitHub issues as the intake for bugs and requests · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`:
  - `Issue` in `BODY_KEYS`, `entry_issues()`, and `closes:` in `load_change()`;
  - check problems in `analyze()`;
  - `recorded_issues()`;
  - `cmd_intake`, `cmd_closes`, `cmd_mark_triaged`, `cmd_needs_info`;
  - `--triaged`/`--why` on `cmd_bug_commit`;
  - close's `mark issues` step, and `closes_errors` in `mirror()`;
  - `triaged` in `bugs_retro()`;
  - argparse, and `READ_ONLY` gaining `intake` and `closes`.
- `scripts/trackers/github.py`:
  - the `TRIAGED` and `NEEDS_INFO` labels;
  - `intake()`, `titles()`, `mark()`, `unmark()`, `needs_info()`, `dangling()`;
  - sub-issues in `_reconcile()`;
  - the `closes:` loop in `archive()`, for shipped (`Closes #N`, or closed itself) and dropped
    (unmark).
- `scripts/metrics.py`: `parse_trailers` keys `triaged` by issue.
- `skills/triage/SKILL.md` (new): a writing skill with one WAIT.
- `skills/ship/SKILL.md`: the `closes <NNN>` read, the per-issue question in the WAIT, and a
  split-off seed for an unresolved issue.
- `skills/intent/SKILL.md`: the entry's `Issue:` → `closes:`.
- `skills/bug/SKILL.md`: closing a retired entry's issue by hand.
- `skills/drop/SKILL.md`: the dropped change's `closes:` issues return to triage.
- `skills/retro/SKILL.md`: the `triaged` count.
- `skills/setup/SKILL.md`: offer the issue forms for `github`.
- `skills/uninstall/SKILL.md`: the forms stay.
- `defaults/issue-forms/sdlc-bug.yml`, `defaults/issue-forms/sdlc-request.yml` (new).
- `.github/ISSUE_TEMPLATE/sdlc-bug.yml`, `.github/ISSUE_TEMPLATE/sdlc-request.yml` (new): this
  repo's copies.
- `.sdlc/setup.json`: rerecorded.
- `tests/test_bugs.py`: R1 and R6 check tests, R20 `bug-commit --triaged`, and the retro count.
- `tests/test_archive.py`: `FAKE_GH` extended, plus tests for R2–R5, R8, R9, R16, R17 and R21.
- `tests/test_skills.py`: `triage` added to `GATED`, the found set and `READS_CONFIG`, plus text
  asserts for R7, R10, R11, R15, R16, R18 and R19.
- `tests/test_defaults.py`: the forms' keys.
- `docs/REFERENCE.md`, `README.md`, `AGENTS.md`: the new keys, commands, labels and skill.

## Work order

1. **Entries and intents (R1, R6's check).** `Issue:` and `closes:` are read and checked, with
   tests.
2. **The tracker (R3, R6's sync, R8, R9).** `github.py`'s new methods, sub-issue reconciliation and
   the `closes:` loop at archive, with `FAKE_GH` extended and the tests.
3. **Core commands (R2, R4, R5, R15's read, R16's close comment, R17, R20, R21).** `intake`,
   `closes`, `mark-triaged`, `needs-info`, `bug-commit --triaged`, close's `mark issues` step, and
   retro's `triaged` count, with tests.
4. **Skills (R7, R10, R11, R15, R16, R18, R19).** The triage skill, and the ship, intent, bug, drop
   and retro edits, with the skill tests.
5. **Forms, docs and this repo (R12, R13, R14).** The issue forms, setup and uninstall, the docs,
   this repo's forms, and `record`.

Each step ends with `./check.sh` green and a commit on the branch.

## Tests

- R1: `test_bugs.py`. `Issue: #12, #15` parses; a malformed value or a duplicate issue fails
  `check`.
- R2: `test_archive.py`. Change issues and issues labelled `triaged` or `landed` are filtered out;
  `filed` names an entry or a change; `target = "none"` reports `unavailable`.
- R3: `test_archive.py`. `mark` and `unmark` are idempotent, and `--parent` is recorded.
- R4: `test_archive.py`. An uncommitted entry is skipped; a committed one is marked once; the
  parent is the entry's first issue or the change's issue; it refuses in a worktree.
- R5: `test_archive.py`. A crash after `bug-commit` and a crash after the intent edit are each
  finished by `mark-triaged`.
- R6: `test_bugs.py` for the check, `test_archive.py` for sub-issue add and remove at `sync`.
- R7, R10, R11, R15, R16, R18, R19: `test_skills.py` text asserts.
- R8: `test_archive.py`. `Closes #12` is in the Close commit; with a different default branch the
  tracker records `issue close 12`; a failure lands the change and is reported.
- R9: `test_archive.py`. A dropped change unmarks its `closes:` issues and closes none.
- R12: `test_defaults.py` for the forms' keys; `test_skills.py` for setup offering them for
  `github` only.
- R13: manual. The docs name each piece.
- R14: `test_archive.py`. The rendered comments match their fixed shapes.
- R16: `test_archive.py`. A split-off seed lands, the Close commit has no `Closes #15`, and issue 15
  gets one comment.
- R17: `test_archive.py`. A `triaged` issue with no record is listed as `dangling`.
- R20: `test_bugs.py`. An empty `Triage #12` commit carries its trailer, and retro counts it;
  `test_archive.py`, `mark-triaged` closes it once, finishing after a crash.
- R21: `test_archive.py`. An issue labelled `needs-info` is hidden until its author replies.
- Manual: the end-to-end run in spec Verification, on this repo, after `/reload-plugins`.

## Rollback

`git revert` of the change's commits covers the code, the skills and the docs. It does not cover
what a triage run already wrote on GitHub, or what it committed to `main`:
- **Labels:** `triaged` and `needs-info`. Remove with `gh label delete triaged` and
  `gh label delete needs-info`.
- **Comments, parent links and issues closed at triage.** These stay. Reopen an issue with
  `gh issue reopen <N>`.
- **`Triage #N` commits and `Issue:` lines on `main`.** They read as plain body text once the key
  is gone. Revert a `Triage` commit with `git revert <sha>`.
- **Hosts' `.github/ISSUE_TEMPLATE/sdlc-*.yml`.** Hosts own these and delete them by hand.
