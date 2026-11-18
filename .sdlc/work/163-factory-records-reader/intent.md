---
id: 163
slug: factory-records-reader
tier: 2
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
serves: none
---

# One reader in core for the factory's records

## Problem

The core reads the files a factory run leaves in a change's folder (its decision, ledger, rounds,
gate records, landing step) through copies of `factory.py`'s parsing, since the core never
imports `factory.py`. Those copies are now spread across files: `factory_reading`, `needs_of`,
`seen_stage` and `_hand_placeholders` (with `HAND_DEFUSE`) in `scripts/sdlc.py`, and
`_factory_files` in `scripts/closing.py`, where 153 moved it with close's measure step. `print_status`
and the board read through them too. Each copy has its own pin test against `factory.py`, so a
change to a record's shape has to find and update every one, in two or three files.
`docs/RETRO-SCORECARD.md` lists it as R4. It also has to land before S3, which counts decisions
and stops from these same records and would otherwise add another reader.

## Outcome

- One module in core, loaded by path like `retro.py` (for instance `scripts/factory_records.py`),
  holds every copy of the factory's record parsing that `sdlc.py`, `closing.py` and the board
  use, and nothing else reads those files its own way.
- A pure move: `status`, `status --all`, the board's columns and cards, the hand gate, and close's
  measure trailers produce byte-identical output before and after, on the existing fixtures.
- Each pin test that compares a copy with `factory.py` now reads the copy from the one module, and
  still fails when the two drift.
- `factory.py` is still never imported by the core, and the module imports nothing from
  `sdlc.py`.
- A test fails if a factory run file (`decision.md`, `decisions.md`, `build/round-*.md`, gate
  records, `runs/land-step.md`) is opened anywhere in core outside the module.

## Affected

`scripts/sdlc.py`, `scripts/closing.py`, `scripts/board.py`, a new module beside them, and the
tests that pin the copies (`tests/test_hand_gate.py`, `tests/test_board.py`, `tests/test_sdlc.py`).
`status`, the board and close read through it; no host-facing output changes. `closing.py` is in
`[review] sensitive`, so the run is reviewed at full depth.

## Constraints

- Modules stay loaded by path and bound live (*Modules loaded by path*), never imported.
- The core never imports or runs `factory.py`; it reads only the files a run leaves.
- The board writes nothing and serves `127.0.0.1` alone; nothing here changes either.
- Metrics trailers unchanged: close's measure step reads the same values.
- Overlaps `closing.py` with 162 (lead time), which also reads the factory's run files in close's
  measure step: whichever lands second builds on the other's reader.

## Open questions

- ~~The module's name and boundary: only the parsing (pure functions over file text), or also the
  readers that open the files.~~ Resolved: `scripts/factory_records.py`, parsing and the readers
  of a change folder's files, pure; git reads come in as callables (spec R1, Design).
- ~~Whether `board.py` reads through it directly or through `sdlc`'s binding, given the board is
  loaded only when `board` runs.~~ Resolved: through the binding, `sdlc.factory_records` (spec R2).
- ~~Whether `seen_stage`, `needs_of` and `column` (the board's and status's state logic) move too,
  or stay in `sdlc.py` as consumers of the records.~~ Resolved: they stay in `sdlc.py` (spec R4).
