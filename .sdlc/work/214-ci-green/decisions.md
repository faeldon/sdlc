# Decisions

- [x] D1 (builder round 1, default): Fix the Linux port failure in `factory.py` by reading `/proc/net/tcp`, not only in the test. Going ahead unless told otherwise. → settled by the approver: The intent's Constraints require a script bug a host would hit to be fixed in the script. The code reviewer confirms `_binds()` was a real bug, not a race, and the test reviewer confirms `test_only_time_wait_reads_the_proc_tables` covers it. The security reviewer notes the fix only narrows `_lost()`.
  - OPTION: script fix via `/proc` — a host on Linux whose dev server sets no `SO_REUSEADDR` is no longer misread as having lost its port and retried; about 20 lines, Linux-only. A port held both by a TIME_WAIT and by another process's bound, not-listening socket reads as free, a rare edge.
  - OPTION: test-only fix (the test's listener sets `SO_REUSEADDR`, as most real servers do) — smaller, but leaves `_binds()`'s Linux behaviour wrong and its docstring claim false.
  - WHY: the intent's constraint is that a script bug a host would hit is fixed in the script.
- [x] D2 (builder round 1, default): Hash the hand gate's build with `git hash-object`, so existing hand-gate records read stale once after the update. Going ahead unless told otherwise. → settled by the approver: The intent fixes script bugs in the script. The code reviewer confirms the hash was a real bug on hosts with `core.autocrlf`, and the security reviewer says old records going stale once fails closed. `docs/REFERENCE.md` is updated, and the CRLF test pins it.
  - OPTION: `hash-object` — stable across line-ending checkouts for every host; each existing green hand gate needs one `sdlc.py gate` rerun.
  - OPTION: keep raw bytes and only normalise CRLF — keeps old hashes for LF-only trees, but would get other git filters (`.gitattributes` eol, smudge/clean) wrong.
  - WHY: what the hand gate means to hash is the build as git stores it.
- [x] D3 (builder round 1, default): Widen `test_windows.py` to the body of each portable test only, not to every test and helper. Going ahead unless told otherwise. → settled by the approver: The intent asks only to widen the check to the read it missed, which was in a portable test's body. The test reviewer confirms `test_every_portable_test_names_its_encoding` covers every test file's portable tests. The 275 non-portable calls are carried forward in `notes.md`.
  - OPTION: portable tests' own bodies — 6 fixes, covers what CI's Windows job runs; a helper they call isn't scanned.
  - OPTION: every test file — catches helpers too, but means 275 mechanical edits to tests Windows never runs.
  - WHY: the intent asks to widen the check to the read it missed, which was in a portable test's body.
- [x] D4 (builder round 1, default): Hash the hand gate's build with `git hash-object`, so hand-gate records written before this change read stale once. Going ahead unless told otherwise. → settled by the approver: This is the same decision as D2, worded twice, and it is settled for the same reasons.
  - OPTION: `hash-object` — stable when a checkout only rewrites line endings, on every host; each existing green hand gate needs one `sdlc.py gate` rerun.
  - OPTION: hash the raw bytes with CRLF normalised — keeps the old hashes for LF-only trees, but gets `.gitattributes` eol and clean filters wrong.
  - WHY: the hand gate is meant to hash the build as git stores it.
