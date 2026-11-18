# 160-command-registry — entries

## [2026-11-18-109] [nit] `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so).

Raised by the test review of 160-command-registry, round 1: tests/test_registry.py:104: `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so). It guards R7 and would catch a later regression, but it never failed on the old code. Only the `config` command is stubbed, so an adapter that bound its handler at import time would be caught for that one command and no other. Stubbing one more, such as `status` with the default no-command path, would cover R5's `--all` default through `main()`.

Theme: tests
Paths: tests/test_registry.py
Cost: S
Value: low
Raised by: 160-command-registry (correctness)
