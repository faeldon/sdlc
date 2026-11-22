# 229 — Plan

> Tier 1 with an Approach across five files, so a plan: what changes where, in what order, and how
> each part is proved. The Approach in `intent.md` is the spec.

## Files to change

- `plugins/factory/scripts/factory.py`: `_park()` takes `exit` only from 2 to 255 (0 and 1 warn
  and leave it unset, as any bad value does); `busy_of()`'s `clean()` drops C0 and C1 control
  characters after folding whitespace, before `_placeholders()`/`_defused()` and the cut;
  `cmd_park(clear=True)` removes an unvouched record whatever its deadline, since no reader takes
  it as a park (`verdicts` reads it as a stop to rerun).
- `scripts/factory_records.py`: `capped_park(park, minutes)`, a copy of `factory.py`'s
  `capped_park()` (which takes the config), and `park(folder, minutes)` returning the park capped.
- `scripts/sdlc.py`: `_park_deadline_at(home, trunk)`, `[park] deadline` as the base branch's
  `factory.toml` holds it (a copy of `_park()`'s check, beside `_gate_jobs_at()`); `status`'s
  read of the park passes it. `needs_of()` itself is unchanged: it stays the one rule, now given
  the capped deadline.
- `scripts/board.py`: the card's read of the park passes the same.
- `plugins/factory/README.md`, `docs/REFERENCE.md`: `exit` is 2-255, 75 the one to use.
- `AGENTS.md`: `update` in the *Skills* list of skills that write, on the list's first line, so
  the paragraph keeps its wrap and `test_agents_md_fits_100_columns` holds.
- Tests: `tests/test_factory_park.py`, `tests/test_modules.py`, `tests/test_hand_gate.py`,
  `tests/test_board.py`.

Reused: `factory.py`'s `capped_park()` and `_park()` are the originals the copies are pinned to;
`_gate_jobs_at()` is the shape of the base-branch read.

## Work order

1. `[park] exit` refuses 0 and 1: test in `test_factory_park.py`, then `_park()`, docs.
2. `busy_of()` strips control characters: test, then `clean()`.
3. `park --clear` removes an unvouched record: test, then `cmd_park()`.
4. The slot-wait test asserts the `slot` wording.
5. `needs_of()` reads the capped deadline: pins (`test_modules.py` for `capped_park`,
   `test_hand_gate.py` for `_park_deadline_at`), a board and a status test of a park whose own
   deadline runs past the cap, then the copies and both callers; the board fixture's park moves
   its `SINCE` so its far deadline stays within the cap where a test wants it live.
6. AGENTS.md's list.

## Tests

- `test_park_exit_of_0_or_1_is_refused`: exit 0 and 1 warn and leave nothing parking.
- `test_busy_payload_drops_control_characters`: ESC, BEL, DEL and a C1 character are gone.
- `test_park_clear_removes_an_unvouched_record`: a hand-written record is cleared before its
  deadline.
- `test_a_gate_past_the_slot_wait_parks_and_a_check_exits_1`: now asserts `no gate slot came
  free` on stderr. A test made stricter, of wording the code already prints, so it passed at once.
- `test_both_park_caps_cut_a_record_alike` (`test_modules.py`): the copy is the factory's.
- `test_the_park_deadline_is_read_as_the_factory_does` (`test_hand_gate.py`): base branch only,
  bad values the default.
- `test_a_park_past_the_base_branchs_deadline_needs_you` (`test_board.py`): board and `status`
  both show the need once the capped deadline passes, though the record's own hasn't.
- `checks.md`: AGENTS.md's list names `update`, and the factory README says 75 is the one to use,
  which only a revert could undo.

## Rollback

Nothing outside the repo: `git revert` undoes it all. No host has `[park]` yet (unreleased).
