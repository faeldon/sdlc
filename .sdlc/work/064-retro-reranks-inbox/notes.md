# 064 — Retro re-ranks the inbox · notes

## This repo

`sdlc.py retro`'s `entries` lists 23 open ideas and bugs: every idea in the register but the two
being built (this change's 2026-11-08-3, and 2026-10-25-7, which 063 has open in another session),
and no nit. 16 of them carry `Priority: low`, the backlog the next retrospective re-ranks.

## Departures from the spec

- **`register_drift` compares an entry's tag too** (`[idea]` → `[building]` is a change): a
  retrospective has no reason to retag, and `entries` already leaves building entries out.
- **The refusal for a removed entry names its way out**: "retire it with /sdlc:idea, not a retro".
