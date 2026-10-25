---
id: 014
slug: ship-landing-edits
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 014 — Ship does its own landing edits · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py ship <NNN>`, after its existing refusals and the stamp, deletes from the
   change's checkout's `work/ideas.md` the one entry whose title matches the intent's `idea:`,
   heading to the line before the next `## ` heading (or end of file), leaving one blank line
   between the remaining entries. A test shows the entry gone and its neighbours byte-for-byte
   unchanged.
2. **R2.** Matching is exact on the title, ignoring a trailing ` → …` pointer on the heading and
   accepting an `idea:` written as the full `## [date] [tag] title`. A test covers each form.
3. **R3.** Two entries matching the `idea:` make `ship` refuse before stamping or writing anything,
   naming both lines. A test asserts intent and `ideas.md` are unchanged.
4. **R4.** No matching entry, no `work/ideas.md`, or no `idea:`: `ship` prints one line saying so
   and carries on. A second `ship` run succeeds (test).
5. **R5.** `ship` then stages every path `_dirty_paths()` lists in the change's worktree, minus each
   `--leave <path>`, with `git add -- <paths>`, and prints each path staged. A test: code, the
   folder, `work/ideas.md` and `.sdlc/last-id` staged; a `--leave` path left unstaged; a path with
   a space staged.
6. **R6.** A `--leave` path that is already staged is a refusal before any write (`unstage it
   first`), since `git add` can't take it out of the commit.
7. **R7.** `ship` never runs `git commit`, `git add -A` or `git add .`. A test asserts no commit is
   made.
8. **R8.** `skills/ship/SKILL.md` Step 6 runs `sdlc.py ship <NNN>` (with `--leave` for each path the
   human chose to commit separately), then `git status --short`, then `git commit`. It no longer
   deletes the seed entry or builds a `git add` list. `Bash(git add *)` leaves `allowed-tools`;
   `tests/test_skills.py` passes (every command has a rule, every rule is used).
9. **R9.** `tests/test_adoption.py` still runs `new` → `close` in a bare repo via `uv run --script`,
   with ship's staging done by `ship`.
10. **R10.** `docs/REFERENCE.md` (where it says what `ship` writes) and `.sdlc/SDLC.md` /
    `defaults/SDLC.md`'s ship section (if it describes Step 6's edits) say `ship` deletes the seed
    and stages the change; `sdlc.py record` reruns if `defaults/` changes.

## Design

`cmd_ship(root, ident, leave)`: the existing refusals (undone items, impact), plus the new ones,
ambiguous seed (R3) and a staged `--leave` path (R6), all before the first write. Then
`stamp_shipped`, then `_drop_seed(work_dir, idea)`, then `_stage(tree, leave)`. A refusal leaves
the tree as it was; a failed `git add` after the stamp is reported, non-zero, and a rerun redoes
all three harmlessly (the stamp is idempotent, the seed already gone, the add again).

`_seed_title(heading_or_title)` strips the `IDEA_RE` prefix and a trailing ` → …`; `_drop_seed()`
reuses `IDEA_RE` and edits `ideas.md` as lines, never through a parser. `_stage()` reuses
`_dirty_paths()` (NUL-split, safe with spaces) and passes paths after `--`. The tree is the change
folder's checkout (`path.parent.parent`); at ship the session is always there, since
`/sdlc:intent` put it there.

The `[building]` tag: in 014's own `work/ideas.md`, the pointer moves under the heading
(`Building in work/014-ship-landing-edits/.`), so the title is exact either way; the matcher's `→`
tolerance covers hosts whose tags already carry it. Argparse: `ship` gains `--leave PATH`
(append).

## Contracts touched

- **Confirm before writing.** `sdlc.py ship` runs only after ship's one WAIT; the new writes (the
  `ideas.md` edit, the index) are covered by that approval, whose prompt already says the folder is
  "stamped shipped" and the change committed. Deleting the seed was already in that approval's
  scope; nothing new escapes it.
- **Narrow `allowed-tools`.** One rule removed, none added; the bash block stays plain commands.
- **`stamp_shipped` edits in place.** Untouched; the seed deletion follows the same line-edit rule.
- **Only publish pushes.** No push, no `"push"` in new code.
- **Always Tier 2:** changes what `sdlc.py` writes in a host (`work/ideas.md`, the index) and a
  skill's `allowed-tools`.
- **Nothing about a project or a workspace.** Test data uses neutral seeds (`reopen-drafts`).

## Alternatives rejected

- **Print the paths and let the skill `git add` them.** Keeps a rule and a command, and the model
  still copies a long list by hand: the failure the seed names.
- **Stage `changed_paths()` since the merge base.** Includes paths already committed on the
  branch; it's ship's view of the whole diff, not what's left to commit.
- **Script the nits and notes edits too.** Their text is judgment; a later seed if they turn out to
  cost stops.
- **`ship` commits too, as `drop` does.** The commit message is written and approved in the skill;
  moving it changes ship's WAIT contract for no saving.

## Verification

- `uv run --group dev pytest tests/test_sdlc.py tests/test_skills.py tests/test_adoption.py -q`,
  then `./check.sh`: green.
- Manual: this change's own `/sdlc:ship` runs the new Step 6. `sdlc.py ship 014` removes the
  `[building]` seed from `work/ideas.md` and prints the staged paths; `git status --short` shows
  them all staged; close's `Sdlc-Totals` shows `permission=0` for ship.
