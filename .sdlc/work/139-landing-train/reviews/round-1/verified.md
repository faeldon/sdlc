- KEPT: test: C1: tests/test_train.py: nothing in `tests/` mentions `LOCK_HELD_ENV`, `_inherit_lock` or `_lock_depth`, so dropping the variable in `_handoff()` (`sdlc.py:4958`) would deadlock a real close and fail no test.
- KEPT: test: C2: tests/test_train.py:644: only the landing-review "kept" case of R8 is tested; the acceptance-check failure on the stacked commit and the reply still unreadable after the one mend have no test.

## Notes
I ran no tests. I grepped `tests/` for the lock names and found no hits. I also read `test_a_kept_landing_change_ejects_only_its_change` and spec R8 and R14. The spec says a handoff test should cover R14's second part, and none exists.
