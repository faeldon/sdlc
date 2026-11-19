# 180-workarounds-tagged — entries

Retire 2026-11-19-26: taken in by 180-workarounds-tagged

## [2026-11-19-54] [idea] retro's process pass seeds from workaround rows

Left undone by 180-workarounds-tagged, carried forward when it landed: `/sdlc:retro`'s passes don't read `simplicity.workarounds` yet: its process pass could turn an `outside` or `restored` row into a seed. The report renders it with S14.
See .sdlc/work/180-workarounds-tagged/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-55] [nit] R5's test covers the eject path only.

Raised by the code review of 180-workarounds-tagged, round 1: tests/test_train.py: R5's test covers the eject path only. The same `problems.append(f"{name}: {problem}")` branch in `_train_stop` has no failing-append test.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 180-workarounds-tagged (correctness)

## [2026-11-19-56] [nit] the `unknown` rows carry a `change` key that no test asserts, and `unknown` has no `n`

Raised by the test review of 180-workarounds-tagged, round 1: tests/test_retro.py:3704: the `unknown` rows carry a `change` key that no test asserts, and `unknown` has no `n`

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 180-workarounds-tagged (correctness)

## [2026-11-19-57] [nit] add one assertion that a stop before any commit leaves no row, since the spec's edge-case section names it

Raised by the test review of 180-workarounds-tagged, round 1: tests/test_retro.py:3677: add one assertion that a stop before any commit leaves no row, since the spec's edge-case section names it

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 180-workarounds-tagged (correctness)
