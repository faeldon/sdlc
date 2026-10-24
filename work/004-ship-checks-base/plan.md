# 004 — Catch a stale base at ship (Tier 2 plan)

## Context

002 shipped three times because `main` moved while it was open, and nothing compared the branch
with `main` until close's fast-forward refused. 004's spec
(`work/004-ship-checks-base/spec.md`, R1–R12) has `/sdlc:ship` bring a clean stale base up to
date itself at Step 0, before the gate and the review, and stop, touching nothing, when it can't.
You approved the gate on 2026-10-24: the update is mechanical, has no prompt, and is reported
with an undo command.

Already built and uncommitted, now rebased onto `main` at `3f0406c` (003 landed):
`behind_main()` (R1), the status marks (R2, wording still to change), close using the helper
(R11), and the Tier 1 ship paragraph and doc sentences, which are rewritten below. 003 touched
nothing this plan depends on. Its shim registry (`.sdlc/deprecations.toml`) doesn't apply,
because nothing here is a shim.

## Files to change

- `scripts/sdlc.py`: `cmd_base()`, its subparser and dispatch, and the status wording.
- `skills/ship/SKILL.md`: Step 0 runs `base`, plus one `allowed-tools` rule.
- `tests/test_sdlc.py`: tests for R2–R9.
- `docs/REFERENCE.md`, `.sdlc/SDLC.md`, `defaults/SDLC.md`: rewrite the sentences added earlier.
  The two SDLC copies get the same edit.
- `work/004-ship-checks-base/plan.md`: replaced by this plan.

## Work order

### 1. `cmd_base(root, ident)` — `scripts/sdlc.py`, after `behind_main()`

1. **Find the change.** Find its worktree the way `cmd_close()` does (lines ~1824–1858):
   `worktrees(root)` filtered by `DIR_RE`, then `names_change(b, ident)`, then `ident`. When
   `ident` is None, use the current branch.
   - If nothing matches, or the match is the main checkout itself, report `action: current`
     with reason "not in a change's worktree" and exit 0. A change in the main checkout has
     nothing to update.
2. **Set up the report.** `report = {change, branch, behind, action, from, to, undo, reason}`,
   printed as JSON by a local `emit(code)`, as in close.
   - `main = main_root(root)`
   - `behind = behind_main(main, branch)`
   - `from = _git(tree, "rev-parse", "HEAD")`
3. **Decide what to do:**
   - **Behind is None** → `refused`, "no local main branch". `cmd_close()` treats this the same
     way, through `!= 0`.
   - **Behind is 0** → `current`, exit 0.
   - **The branch has commits of its own** (`own = rev-list --count refs/heads/main..refs/heads/<branch>`
     is greater than 0):
     - If `_dirty_paths(tree)` is non-empty → `refused`, "<branch> has commits of its own and
       uncommitted work: commit the work, then run /sdlc:ship again". Run nothing.
     - Otherwise `err = _git_err(tree, "rebase", "-q", "main")`. If that fails, run
       `_git_err(tree, "rebase", "--abort")` and report `refused` with `err`. On success, report
       `rebased`.
   - **No commits of its own:**
     - **Counter (R7).** `ours = tree/.sdlc/last-id`. If it is untracked in the tree
       (`git ls-files --error-unmatch` fails) and `_git(main, "cat-file", "-e", "main:.sdlc/last-id")`
       succeeds, save its text and number (`_read_number`), then unlink it.
     - `err = _git_err(tree, "merge", "--ff-only", "-q", "main")`.
     - **On failure:** write the saved text back exactly, then report `refused` with `err`. Git
       lists the files that block it.
     - **On success:** if a counter was set aside, compare `main`'s number (`_read_number` of the
       now-tracked file) with ours. If ours is higher, write ours back in `new`'s format: reuse
       the existing writer (`_write_state(tree, LAST_ID, …)`), as `cmd_new` does. Report
       `fast-forwarded`.
4. **Finish.** `to = rev-parse HEAD`, and `undo = f"git -C {tree} reset --keep {from}"`.
5. **Rules for the whole function.** Never use `--force`, `stash`, `--autostash`, `fetch` or
   `push`, and never touch `main`'s ref or the main checkout. The docstring states the gate
   exception and points at the spec.
6. **Wiring.** Add the subparser `sub.add_parser("base", help=…)` with an optional `ident`, and
   dispatch it next to `close`. Don't add it to `READ_ONLY`.

### 2. Status wording (R2)

On the open-change line, `rebase before /sdlc:ship` becomes `/sdlc:ship brings it up to date`.
The Ready-to-close line stays as it is.

### 3. Ship skill (R10) — `skills/ship/SKILL.md`

- Add `'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py base *)'` to
  `allowed-tools`.
- Replace the "A stale base stops ship here" paragraph with a short block and a bash block
  running `sdlc.py base <NNN>`. The text says:
  - this happens with no confirmation, unlike anything else that writes;
  - report `action`, how many commits came in (`behind`), and the `undo` line;
  - `current` is silent;
  - on `refused`, stop before Step 1 with its `reason`;
  - never resolve a conflict or retry by hand from this skill.
- Keep Step 0's heading "(mechanical, no confirmation needed)". There's still exactly one WAIT.

### 4. Docs (R12)

Change the earlier sentences from "ship stops on that mark" to "ship brings the branch up to date
first when that is clean (a fast-forward, or a rebase of its own commits), and stops when it
isn't". Make that edit in `docs/REFERENCE.md`, and the same edit in `.sdlc/SDLC.md` and
`defaults/SDLC.md`.

### 5. Plan file

Overwrite `work/004-ship-checks-base/plan.md` with this plan.

## Tests — `tests/test_sdlc.py`

Reuse `_repo()`, `cmd_new(..., worktree=True)`, `_diverge()`, `_git()`, and `capsys` with
`json.loads`, as `_close()` does. Add one helper, `_base(root, ident, capsys)`.

| Test | Covers |
|---|---|
| `test_base_is_current_when_main_hasnt_moved` | `current`, exit 0, HEAD unchanged |
| `test_base_fast_forwards_and_carries_uncommitted_edits` | R4; R8: `main`'s sha and the main checkout's `status --porcelain` unchanged; a second run says `current` |
| `test_base_refuses_when_main_touched_a_file_the_work_did` | R4 refusal: HEAD and the edited file's bytes unchanged |
| `test_base_rebases_a_clean_branch_with_commits` | R5 |
| `test_base_aborts_a_conflicting_rebase` | R5: HEAD equals `from`, no `.git/rebase-merge` left |
| `test_base_refuses_commits_plus_uncommitted_work` | R6: runs nothing |
| `test_base_keeps_the_higher_counter` | R7: local numbering; `main` commits `.sdlc/last-id` higher, then lower than ours; after the run the file holds the higher one |
| `test_base_puts_the_counter_back_when_it_refuses` | R7: an overlapping edit forces the refusal; counter bytes restored |
| `test_base_carries_a_factory_run_intact` | R9: uncommitted `decision.md`, `decisions.md`, `reviews/round-1/code.md` and a code edit survive byte for byte |
| `test_base_undo_puts_the_branch_back` | runs the printed `undo` and checks HEAD equals `from` |

The existing `test_behind_main_counts_what_the_branch_lacks` and
`test_status_marks_a_stale_base_and_check_ignores_it` stay, with the new wording.
`tests/test_skills.py` needs no edit: its rule-coverage tests check the new rule is used.

## Rollback

Plain `git revert`. Nothing is written outside the change's own worktree, and nothing is
published.

## Verification

- `uv run --group dev pytest tests/test_sdlc.py -q -k "base or behind or stale or close or status"`
- `uv run --group dev pytest tests/test_skills.py -q`
- `./check.sh` exits 0.
- By hand: `uv run --quiet --script scripts/sdlc.py base 004` in this worktree prints
  `current`, since it was just rebased.
