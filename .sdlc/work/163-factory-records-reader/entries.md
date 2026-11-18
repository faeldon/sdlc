# 163-factory-records-reader — entries

## [2026-11-19-5] [nit] the "Modules loaded by path" and "The board" edits leave lines far over the file's wrap width (about 100 columns)

Raised by the code review of 163-factory-records-reader, round 1: AGENTS.md:68: the "Modules loaded by path" and "The board" edits leave lines far over the file's wrap width (about 100 columns)

Theme: docs
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)

## [2026-11-19-6] [nit] the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable.

Raised by the code review of 163-factory-records-reader, round 1: tests/test_board.py: the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable. It was a comparison of two copies, and with one copy it would compare the module with itself. `LAND_STOPS` still has no factory twin, so nothing checks it against the factory. It is only pinned against `LAND_STEPS` through the board's `LAND_AT` test.

Theme: tests
Paths: tests/test_board.py
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)

## [2026-11-19-7] [nit] a few helper names such as `_reached` and `_named` have no docstring

Raised by the test review of 163-factory-records-reader, round 1: tests/test_modules.py: a few helper names such as `_reached` and `_named` have no docstring

Theme: tests
Paths: tests/test_modules.py
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)
