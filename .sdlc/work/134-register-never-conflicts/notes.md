# Notes

- [x] Close takes `_main_lock()` only around its register write and `Close` commit, not from its merge: an `inbox-commit` that lands between the two puts a `File` commit between the change's commit and its `Close`, where `closed_changes()` reads the `Close`'s first parent as the change. That hazard predates this change (the folder's removal had it too); holding the lock from the merge would close it, at the cost of blocking `/sdlc:idea` through the archive step. → seed: 2026-11-18-23
- [x] `test_close_and_inbox_commit_keep_both_entries` (R7) files the idea between close's check and its locked write, so it proves the reread under the lock, not two processes racing for it. A threaded test, like `claim()`'s, would prove the lock itself. → seed: 2026-11-18-24
