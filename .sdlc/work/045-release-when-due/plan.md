# 045 — Status recommends a release only once a batch is due

> How the intent's Approach is built, after reading the code.

## Files to change

- `scripts/sdlc.py`
  - `DEFAULTS["release"]`: `due_after_changes = 5`, `due_after_days = 14`; both in `INT_KEYS`.
  - `release_due(changes, rel, today)`, pure, beside `unreleased()`: `{due, why, minor, oldest}`.
    A `major` change is always due; `minor` or `major` changes count toward `due_after_changes`;
    the oldest `close_date` (a change landed but not closed has none and is skipped) toward
    `due_after_days`. A key at 0 turns its rule off.
  - `unreleased()` sets `out["due"]` once `next` is set, so `status` and `release --check` both
    carry it. Nothing to release, a missing tag or a problem leaves it `None`.
  - `print_status`: the Unreleased line keeps `/sdlc:release` only when due; otherwise it says
    `not due: 2 of 5 minor changes, oldest 2d of 14`. When due, a `■ Release due: <why>
    /sdlc:release` section, beside Retro due.
- `skills/status/SKILL.md`: Step 3's precedence (Priority high Next up, then Release due, then
  Retro due, then Next up), and the Step 1 note on what nothing-open picks from.
- `docs/REFERENCE.md`: the two keys in the config block, and a paragraph on when a release is due.
- `guide/process.md`: the Release row and "after a few of those" say when status calls it due.
  `guide/` changes, so `sdlc.py record` runs from this checkout.
- `README.md`: the `/sdlc:release` row.

## Open questions, resolved

- A `Priority: high` bug outranks a due release, like a high idea: the label starts
  `priority high`, whatever the kind.
- A `closes:` issue doesn't make a release due sooner: it waits on a push, which is publish's
  (`2026-10-25-19`).

## Tests

`tests/test_release.py`: `release_due()` below the count, at it, a major alone, an old batch,
each key at 0, and a landed-not-closed change with no date (all `portable`); status without the
call to action below the threshold, with **Release due** at it.

## Rollback

Revert the commit: the keys are optional, and a host that set them gets a warning for an unknown
key, nothing worse.
