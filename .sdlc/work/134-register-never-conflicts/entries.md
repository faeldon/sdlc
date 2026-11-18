# 134-register-never-conflicts — entries

## [2026-11-18-23] [idea] Close holds the main lock from its merge to its Close commit

Left undone by 134-register-never-conflicts, carried forward when it landed: Close takes `_main_lock()` only around its register write and `Close` commit, not from its merge: an `inbox-commit` that lands between the two puts a `File` commit between the change's commit and its `Close`, where `closed_changes()` reads the `Close`'s first parent as the change. That hazard predates this change (the folder's removal had it too); holding the lock from the merge would close it, at the cost of blocking `/sdlc:idea` through the archive step.
See .sdlc/work/134-register-never-conflicts/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-24] [idea] A threaded test that close and inbox-commit contend for the register lock

Left undone by 134-register-never-conflicts, carried forward when it landed: `test_close_and_inbox_commit_keep_both_entries` (R7) files the idea between close's check and its locked write, so it proves the reread under the lock, not two processes racing for it. A threaded test, like `claim()`'s, would prove the lock itself.
See .sdlc/work/134-register-never-conflicts/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-25] [nit] the new *Closing* lines and the *The register* paragraph (around line 166) run past the file's ~100-column wrap, so reflow them

Raised by the code review of 134-register-never-conflicts, round 1: AGENTS.md:118-119: the new *Closing* lines and the *The register* paragraph (around line 166) run past the file's ~100-column wrap, so reflow them

Theme: style
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 134-register-never-conflicts (correctness)
