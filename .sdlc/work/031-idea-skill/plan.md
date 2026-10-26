---
id: 031
slug: idea-skill
kind: plan
created: 2026-10-27
updated: 2026-10-27
---

# 031 — An /sdlc:idea skill, and inbox-commit for every kind of entry · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `_main_lock()` lifted out of `claim()`; `RETIRE_REASONS` by kind and
  `entry_kind()`; `BUG_SUBJECTS` → `INBOX_SUBJECTS`; `cmd_bug_commit` → `cmd_inbox_commit` with
  the worktree path and entry splicing; the `inbox-commit` parser entry, dispatch and docstring.
- `skills/idea/SKILL.md` (new): `/sdlc:idea`, filing, editing and retiring ideas behind one WAIT.
- `skills/bug/SKILL.md`: `inbox-commit` rule and command; runs from any checkout.
- `skills/triage/SKILL.md`: `inbox-commit` rule and command, nothing else.
- `AGENTS.md`: the bugs and intake paragraphs, and the writing-skills list.
- `docs/REFERENCE.md`: the command's name, filing from a worktree, idea retire reasons.
- `README.md`: a skill-table row for `/sdlc:idea`.
- `tests/test_bugs.py`: renamed commit tests, per-kind reasons, worktree filing, the lock.
- `tests/test_archive.py`, `tests/test_adoption.py`: the renamed call.
- `tests/test_skills.py`: `idea` in the writing and found lists, its `READS_CONFIG`, the bug and
  triage skills' new command, a test for the idea skill.

## Work order

1. **Lock helper.** `@contextmanager _main_lock(home)` on `state_path(home, LAST_ID).parent`,
   `fcntl.flock LOCK_EX`, closed in `finally`; `claim()` uses it. Existing tests pass unchanged.
2. **Kinds.** `RETIRE_REASONS = {"idea": ("duplicate", "superseded", "declined"), "bug":
   (today's four), "nit": ()}`, `entry_kind(e)` beside `is_bug()`/`is_nit()`, `INBOX_SUBJECTS`.
3. **`cmd_inbox_commit(root, ids, reasons, triaged, whys)`.** From the main checkout, today's path.
   The retire check moves into the removal loop: `[building]` refused, a reason outside its kind's
   refused, a nit refused; `Sdlc-Retired:` for bugs only, `Reason <id>: <word>` in the body for an
   idea. From a worktree: ids required, triage flags refused; under `_main_lock(home)` the main
   checkout must be on `trunk` and clean; each id's action comes from the worktree's register
   against its `HEAD` (an unchanged id refused, a File already in `main`'s refused, an
   Update/Retire missing from `main`'s refused). Splice whole entries with `_entry_spans(text)`
   (`ENTRY_RE`/`FENCE_RE`, as `parse_entries()` reads them) into `main`'s register, commit
   `-- <rel>` in the main checkout, put `main`'s text back if the commit fails, then restore those
   ids in the worktree's register to its `HEAD` text, keeping every other edit.
4. **Parser.** `inbox-commit` with positional `ids` and `--reason/--triaged/--why`; dispatch;
   module docstring. Not in `OWN_SCRIPT_CMDS`: filing shouldn't run a change's unfinished script.
   Rename the call sites in `test_bugs.py`, `test_archive.py`, `test_adoption.py`; tests green.
5. **New tests** in `test_bugs.py` (see Tests).
6. **Skills.** `skills/idea/SKILL.md` modelled on `skills/bug/SKILL.md`; bug and triage renamed;
   bug loses its main-checkout stop and passes the id from a worktree. `test_skills.py` updated.
7. **Docs.** AGENTS.md, `docs/REFERENCE.md`, README.md.
8. `./check.sh` green.

## Tests

- **R1:** the existing `test_bug_commit_*` cases renamed to `test_inbox_commit_*` and run through
  `cmd_inbox_commit`; the archive and adoption tests through the new name; `main(["bug-commit"])`
  raises argparse's `SystemExit`.
- **R2:** an idea retired as `superseded` commits; an idea as `wontfix` is refused naming
  `duplicate|superseded|declined`; a nit removed is refused saying ship retires nits.
- **R3:** removing a `[building]` entry is refused.
- **R4:** an idea's `Retire` commit has `Reason <id>: superseded` and no `Sdlc-Retired:` line; a
  bug's keeps its trailer.
- **R5:** from a worktree, a new idea named by id lands on `main` as `File <id>`, touching only the
  register; the worktree's own uncommitted `[building]` edit survives and the filed entry is gone
  from its diff; an update and a retire from a worktree land likewise; an id the worktree didn't
  change is refused; no ids is refused.
- **R6:** a dirty main checkout, and a main checkout off `trunk`, are each refused with nothing
  written.
- **R7:** with `_main_lock` held on another fd, `inbox-commit` from a worktree blocks until it is
  released (a thread, a short timeout).
- **R8, R9:** `test_skills.py`'s invariants over the new skill (one WAIT, description, rules used,
  `READS_CONFIG`), plus a test that it takes ids from `next-entry`, commits through
  `inbox-commit` and says "names no host"; the bug and triage tests name `inbox-commit`.
- **R10:** manual: AGENTS.md, `docs/REFERENCE.md` and README.md name `inbox-commit` and
  `/sdlc:idea`; `git grep bug-commit` finds only history's register text and this change's
  folder.
- **R11:** `./check.sh`.
- **Manual:** in a scratch repo with a worktree under `.claude/worktrees/`, edit the worktree's
  register and run `uv run --script scripts/sdlc.py inbox-commit <id>` from it: `main`'s last
  subject is `File <id>`, it touches only the register, and the worktree's `git diff` no longer
  shows the entry.

## Rollback

`git revert <sha>` of the ship commit restores `bug-commit` and the skills that call it, and
removes `/sdlc:idea`. It doesn't cover inbox commits already made on `main` by `inbox-commit`:
those are ordinary `File`/`Update`/`Retire` commits of the register and stay valid, since history
readers never look at the command's name. A host that loaded the new skills keeps them until
`/reload-plugins` after the revert.
