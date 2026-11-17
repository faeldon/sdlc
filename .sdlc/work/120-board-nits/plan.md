# Plan

> Tier 1, written because the Approach touches five files. What gets built, in what order, and
> what proves it.

## Files to change

- `scripts/board.html`: `.next code` gets `overflow-wrap: anywhere`, the rule `.title`, `.needs`
  and `.flag` already carry.
- `plugins/factory/scripts/factory.py`: `WAYS` shortened to the command and a few words; a new
  `WAYS_WHY` holds the longer sentence, which `stop_text()` writes into the record's body, after
  the `NEXT:` line and before the problems. The record's shape is kept: `STOPPED:`, `NEXT:` and
  `- PROBLEM:` lines are as before, and the new line matches none of `STOPPED_RE`, `NEXT_RE` or
  `PROBLEM_RE`, so `sdlc.factory_stop()` (and the board, which calls it) reads the same fields.
  The board's drawer lists `runs/stopped.md`, so the longer text is a click away.
- `scripts/board.py`: `_progress()`'s first test parenthesised as
  `entry.get("stopped") or ((folder / STOPPED).is_file() and entry["stage"] == "build")`.
- `scripts/sdlc.py`: a `FACTORY_STOP_NEEDS` dict, way → plain imperative, read by `needs_of()`
  in place of the bare way. The needs texts are already imperatives (`decide D1`, `approve its
  spec`, `read the escalation`), and `status` joins them with `, `, so a label holds no comma.
  The `stopped: ` prefix and the unreadable record's `read runs/stopped.md` stay.
- `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md` (round 3, decision-1): the
  board fixture the ui and ux reviewers' shots are rendered from. Its stop record was written
  before this change, so its card showed the old run-on `NEXT:` sentence and no shot could show
  outcome 2. Rewritten as `factory.stop_text()` now writes it, for the same way (`mend`) and
  problem; a test keeps it so, so a later `WAYS` edit can't leave the shots stale again.
- Docs: `docs/REFERENCE.md` (the needs texts), `skills/status/SKILL.md` (its example),
  `plugins/factory/README.md` (`runs/stopped.md`'s contents).

Reused: `factory.stop_text()`, `sdlc.factory_stop()`, `sdlc.needs_of()`, the tests' `_rec()`,
`_stopped_run()` and `_page_parts()`.

## Work order

1. **Wrap**: test that `.next code` carries `overflow-wrap: anywhere`; add it.
2. **Short ways**: test each `WAYS` sentence, formatted for a three-digit id, fits two lines of a
   390px card (at most 90 characters) and still names its command(s); test `stop_text()` writes
   the `WAYS_WHY` sentence and `factory_stop()` reads the record exactly as before. Then edit
   `WAYS`, add `WAYS_WHY`, write it in `stop_text()`.
3. **Plain needs**: test `needs_of()` gives each way's plain label and never the bare word `mend`;
   update the existing pins (`test_a_stop_needs_its_way_on`, `test_a_blocking_decision_needs_its_id`,
   `test_status_ends_with_what_needs_me`). Then add `FACTORY_STOP_NEEDS`.
4. **Stop test**: test `_progress()` returns None for a stopped entry at any stage, for a record
   on disk at `build`, and not for a record on disk at another stage alone; then parenthesise.
5. Docs, then the gate.
6. **Fixture** (round 3): test that every `runs/stopped.md` under the board fixture is exactly
   what `stop_text()` writes for its way and problems; then rewrite 006's record. A real host's
   record written before this change keeps its old sentence until its next `verdicts --record`
   (D4): the board writes nothing, so it can't rewrite one.

## Tests

- Outcome 1 (wrap): `test_a_long_next_step_wraps_inside_its_card` (test_board.py).
- Outcome 2 (a line or two): `test_each_way_on_fits_two_lines_at_phone_width` (test_factory.py)
  and `test_the_stop_record_says_why_and_reads_as_before` (test_board.py, where `sdlc.py`'s
  `factory_stop()` is loaded beside `factory.py`).
- Outcome 3 (stop test): `test_a_stop_hides_the_step_track_as_it_always_has` (test_board.py)
  pins the result, which passed before the edit as a refactor's pin should; the parentheses
  themselves are an acceptance check in `checks.md`, since only a revert could remove them.
- Outcome 2 as the reviewers see it: `test_the_board_fixture_stops_as_the_factory_writes`
  (test_board.py) keeps the fixture's stop records in step with `stop_text()`.
- Outcome 4 (plain needs): `test_a_stop_needs_its_way_on` reworked, plus
  `test_a_stop_s_need_is_in_plain_words` (test_sdlc.py); `test_a_blocking_decision_needs_its_id`
  and `test_status_ends_with_what_needs_me` updated to the new wording.

## Rollback

Nothing outside the tree: `git revert` undoes it all. A `runs/stopped.md` written by the new
`stop_text()` carries one extra prose line, which the old readers ignore.
