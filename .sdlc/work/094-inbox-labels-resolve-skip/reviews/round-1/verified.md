- KEPT: code: C1: plugins/factory/scripts/factory.py:1546: nothing records that a role was already mended, so a second preamble reply (or a second reply missing `## Evidence`) still gets `way: mend` from `loop_state()`. The "once only" rule lives in the SKILL prose alone, and `cmd_agent` doesn't refuse a second mend.

## Notes
- I read the diff, `loop_state()` (lines ~1100–1165), `verdict_mend()`, and `cmd_agent`'s mend path (~1840–1880). I also read the intent's outcome and the SKILL.md diff.
- I ran no tests.
- Nothing in factory.py marks a mend. A grep for `mended`, `already mend` and `second mend` finds nothing in factory.py, and nothing in tests/test_factory.py either. The mend test at test_factory.py:1532 isn't read for a second-mend case.
- The intent says "a second such reply stops as today", and AGENTS.md says "once", so the code falls short of both.
