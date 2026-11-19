# 179-feature-inventory — entries

## [2026-11-19-41] [nit] the factory paragraph's reflowed line runs past 100 columns (`` `surface` (`COMMAND_RE`), never running … ``); rewrap it like its neighbours

Raised by the code review of 179-feature-inventory, round 1: AGENTS.md:253: the factory paragraph's reflowed line runs past 100 columns (`` `surface` (`COMMAND_RE`), never running … ``); rewrap it like its neighbours

Theme: style
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-42] [nit] `_surface_at` calls `COMMAND_RE.findall` on `sdlc.py` at a tag that predates the `@command` registry.

Raised by the code review of 179-feature-inventory, round 1: scripts/retro.py:1768: `_surface_at` calls `COMMAND_RE.findall` on `sdlc.py` at a tag that predates the `@command` registry. It returns `commands: None` only because `core` is empty, which is the intended behaviour, but it's implicit. A short comment would say so

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-43] [nit] `_retire` stops walking back once every item is decided, so `retire.windows` can be below `RETIRE_AFTER` while no candidate is hidden.

Raised by the code review of 179-feature-inventory, round 1: scripts/retro.py:1715: `_retire` stops walking back once every item is decided, so `retire.windows` can be below `RETIRE_AFTER` while no candidate is hidden. REFERENCE.md could say `windows` is the windows actually read

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-44] [nit] the docstring starts "179 R1", which cites the change by number; the rest of the repo's test docstrings name only the behaviour

Raised by the test review of 179-feature-inventory, round 1: tests/test_metrics.py:495: the docstring starts "179 R1", which cites the change by number; the rest of the repo's test docstrings name only the behaviour

Theme: style
Paths: tests/test_metrics.py
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)
