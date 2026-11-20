# 195 — Plan

> Tier 1, written because the Approach touches four files. The intent's Approach is the spec.

## What the code says

- A Tier 2's first spec draft (`/sdlc-factory:spec`, or `/sdlc-factory:build` with `spec` true)
  runs `factory.py agent --task spec`, which writes **no** `runs/step.md` (`TASK_STEP` has no
  `spec`). It appends the session id to `runs/spec-writer.sessions` before `claude` starts, and on
  return writes `runs/spec-draft.md` and a `runs/costs.jsonl` row naming that session.
- Only an upgraded Tier 1 records `STEP: spec` in `runs/step.md` (its `verdicts`), with the change
  back at `stage: plan`.
- Nothing removes `runs/spec-draft.md` on a no; the person deleting it is what "its draft is gone"
  means.

So "the spec-writer runs" is read as: `runs/step.md` names `spec`, or the newest session in
`runs/spec-writer.sessions` has no `costs.jsonl` row yet. A draft waits while
`runs/spec-draft.md` exists. A finished session with its draft deleted is neither, so the change
goes back to Planned.

## Files to change

- `scripts/factory_records.py`: `SPEC_DRAFT` (factory.py's name, so
  `test_every_shared_name_is_the_factorys` pins it), `SPEC_SESSIONS`, and `specifying(folder)`,
  reusing `read_step()` and the costs rows' `session` field. Add it to `reading()` and to
  `card_reading()`'s result as `specifying`, so `status` and the board both carry it.
- `scripts/sdlc.py`: `column()` maps a factory change at `plan` with `specifying` (and no written
  spec, which `needs_of()` already sends to Needs you) to `designing`. The stage line isn't touched.
- `tests/test_modules.py`: `specifying`, `SPEC_SESSIONS` and `SPEC_DRAFT` join `RECORD_NAMES`;
  `SPEC_SESSIONS`, core's own name, is pinned to `factory.py`'s `agent_name()` and `TASK_ROLE`.
- `docs/REFERENCE.md`: *The board*'s Designing says it holds such a change.
- `tests/test_board.py`: the test below.

## Work order

1. One slice: the test, then `specifying()`, then `column()`.

## Tests

- `test_a_plan_change_being_specified_is_designing` (tests/test_board.py): plan-stage factory
  changes with `STEP: spec`, a waiting draft, or a spec-writer session not yet returned sit under
  Designing on the board and in `status`; one with neither, or a returned session whose draft is
  gone, stays Planned; no `stage:` line changes.
- `test_spec_sessions_is_the_spec_writers_file` (tests/test_modules.py): the sessions path is the
  one `factory.py agent` writes for the spec-writer. `SPEC_DRAFT` is pinned by
  `test_every_shared_name_is_the_factorys`, as a name both share.

## Rollback

Nothing outside the code: `git revert` undoes it all. The board writes nothing.
