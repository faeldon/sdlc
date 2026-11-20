# 191-tests-paydown — entries

Retire 2026-11-18-79: taken in by 191-tests-paydown
Retire 2026-11-18-101: taken in by 191-tests-paydown
Retire 2026-11-18-104: taken in by 191-tests-paydown
Retire 2026-11-18-109: taken in by 191-tests-paydown
Retire 2026-11-19-6: taken in by 191-tests-paydown

## [2026-11-20-15] [idea] Give the workarounds' `unknown` block its `n`, as `_workarounds()`'s docstring says

Left undone by 191-tests-paydown, carried forward when it landed: `retro.py`'s workarounds block gives `unknown` a `count` and `rows` but no `n`, though `_workarounds()`'s docstring says "each count carries its `n`" (nit 2026-11-19-56). That is a code change, and this change is tests-only, so its test pins the row's `change` key and leaves `n` alone.
See .sdlc/work/191-tests-paydown/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-16] [nit] `UNCACHED`'s `offline` and `no solution found` are broad, so a script failure that happens to print "offline" would skip the test when it should fail.

Raised by the code review of 191-tests-paydown, round 1: tests/uv_run.py:17: `UNCACHED`'s `offline` and `no solution found` are broad, so a script failure that happens to print "offline" would skip the test when it should fail. The `--offline` run only gets here after the index was unreachable, which makes this unlikely, but a tighter match would cost little.

Theme: robustness
Paths: tests/uv_run.py
Cost: S
Value: low
Raised by: 191-tests-paydown (correctness)
