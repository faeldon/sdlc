# Build report — 141-board-landing-track-truth (round 1)

Tier 1, Approach as spec. `plan.md` written first (the change crosses four scripts); built in seven slices, each test-first. Nothing committed; the tree is left as `git status` shows above.

## Slices built

1. **A shipped change mid-rebase keeps its card** — `board.py`: `_rebasing()` helper; `_on_board()` keeps a closed folder whose branch a stopped rebase detached (what `ready_to_close()` can no longer see). `file_at` serves its files too.
2. **`accept` and `cases` record a landing step** — `factory.py`: `LAND_STEPS` gains `checks` and `cases`; `cmd_accept`/`cmd_cases` record them through `_record_land()` before the commit (`_before_commit()`); `board.py`: both at the `ship` position, labelled by name.
3. **A stopped landing needs the person** — `sdlc.py`: `needs_of()` adds `landing stopped at <step>` at `test`/`shipped` from a `land_stop` field; `factory_land_stop()` (pinned copies `FACTORY_LAND_STEP`, `FACTORY_AFTER_RE`) lets `status` read it for open changes at `test` and the ready-to-close list, so `■ What needs me` and the Ready to close line say it. `board.py`: `_entry()` sets `land_stop`; `column()` puts `needs` before `close`. `board.html`: the `landing-stopped` class and style go (the column's look is the stop's). The intent's open question is answered **yes, status agrees**, with a test.
4. **Plain stop lines** — `factory.py`: `_land_refused()`/`_close_stopped()` record the plain line then the raw text (raw stays the refusal in output); `AMEND_PLAIN`/`_amend_plain()` for `_amend_record()`'s whys; plain lines for the two `landed by=auto` stops and the two `resolve` stops; `_record_move()`'s way on names `/sdlc:close` (it said "/sdlc:ship it by hand" on a committed change).
5. **An early stop is shown** — `factory.py`: `step_text()`/`stop_text()` write `- STUCK:`/`- UNTESTABLE:` lines (`early_lines()`), `read_step()` reads them; `board.py`: `progress["early"]`, the approve step labelled `approve (stuck, untestable)`; the page flags each reason as `stopped early: …`.
6. **The decision line** — build-stage `decide D1` now names *the session running `/sdlc-factory:build NNN` (rerun it if that session ended)*. See the decision below.
7. **Labels** — `B${n}` for build rounds, `L${n}` for landings; no `R${` label on the page.

Docs: `docs/REFERENCE.md` (status needs text, board columns, track steps, labels, stopped landing's way on) and `plugins/factory/README.md` (records). 2026-11-18-19 (`/sdlc:close` on a shipped card) was already in `next_action()`; it is re-pinned, not changed.

## Tests added (what each proves)

- `test_board.py`: `test_a_shipped_change_whose_landing_rebase_is_stopped_keeps_its_card` (O1); `LANDS["checks"]`/`["cases"]` in the parametrized track test (O2); `test_a_stopped_landing_is_in_needs_you` (replaces 133's "keeps its column" test; O3 + the `/sdlc:close`/`/sdlc:ship` way on), `test_the_landing_stop_is_read_as_status_reads_it` (pinned copy), `test_status_lists_a_stopped_landing_under_what_needs_me`; `test_an_early_stop_shows_on_the_card` (O5) and the step-record pin extended with `STUCK_RE`/`UNTESTABLE_RE`; `test_rounds_are_labelled_b_and_landings_l` (O7); `PRECEDENCE`/`BOTH` reworded (O6).
- `test_land.py`: `test_accept_and_cases_record_their_landing_step` (O2); `test_every_landing_stop_has_a_plain_line_over_its_raw_text` (O4); the resolve test and 133's plain-words test now expect raw under plain.
- `test_factory.py`: `test_record_writes_an_early_stops_reason` (O5).
- `test_sdlc.py`: `test_a_landing_stop_needs_the_person` (O3).

`plan.md`: test table aligned to the names written; `_before_commit()` named. `notes.md`: two unticked follow-ups (the hand-run `sdlc.py resolve` next-step while a factory builder resolves a conflict; `accept` after a rebase records no step since it runs inside the gate's).

## Decisions

- DECISION: [default] Build-stage decision line names the `/sdlc-factory:build NNN` session, not `/sdlc-factory:decide NNN for D1` as the intent says. Going ahead unless told otherwise.
  - OPTION: name the session running `/sdlc-factory:build NNN` (rerun it if it ended) — true today: `cmd_ask` refuses any stage but `test`, and the decide skill says "not for a run still building"
  - OPTION: name `/sdlc-factory:decide NNN for D1` as the intent asks — the board would point at a command that refuses
  - OPTION: extend `decide` to take build-stage blocking decisions — a scope change (the supervisor must be told through `agent --task decided`); a change of its own
  - WHY: the intent's claim "since 137, decide is where" holds only at `test`; O6 says the board must be true at every step
- DECISION: [default] An early stop's reason is recorded in `runs/step.md` (and in `runs/stopped.md` only when a stop is also written), not by writing `runs/stopped.md` on its own. Going ahead unless told otherwise.
  - OPTION: `- STUCK:`/`- UNTESTABLE:` lines in `step.md`, shown on the `approve` step and as flags; `stop_text()` carries them when a real stop is recorded — the run keeps its track and column while the approver runs
  - OPTION: write `runs/stopped.md` for an early stop — `needs_of()` would put the run in Needs you and hide its track while the approver is still about to decide, which misleads
  - WHY: an early stop is a run going to the approver with rounds left, not a run waiting on the person
- DECISION: [default] `cases` records its own step `cases` beside `checks` (both at the ship position). Going ahead unless told otherwise.
  - OPTION: two steps, `checks` and `cases` — the card says which is running
  - OPTION: one step `checks` for both — fewer names; the label is wrong while cases run
  - WHY: the Approach names `checks`; the outcome says both commands "record a landing step", and a true label costs one entry

## Evidence

```
$ uv run --group dev pytest tests/test_board.py -q -k "landing_rebase_is_stopped"
E       KeyError: '030-draft-land'
1 failed, 213 deselected in 7.29s
exit: 1

$ uv run --group dev pytest tests/test_land.py tests/test_board.py -q -k "record_their_landing_step or shows_its_landing_track or landing_step_record_is_a_pinned" -n 4
E       AssertionError: every step the factory records
E       TypeError: 'NoneType' object is not subscriptable
exit: 1

$ uv run --group dev pytest tests/test_sdlc.py tests/test_board.py -q -k "landing_stop_needs or stopped_landing_is_in_needs or read_as_status_reads or lists_a_stopped_landing" -n 4
E       AssertionError: assert [] == ['landing stopped at close']
E       AttributeError: module 'sdlc_board_under_test' has no attribute 'FACTORY_LAND_STEP'
E       assert ('close', []) == ('needs-you',...ed at close'])
exit: 1

$ uv run --group dev pytest tests/test_land.py -q -k "plain_line_over"
E       AttributeError: module 'factory_landing' has no attribute '_amend_plain'
1 failed, 77 deselected in 8.84s
exit: 1

$ uv run --group dev pytest tests/test_factory.py tests/test_board.py -q -k "early_stop or step_record_is_a_pinned" -n 4
E           AttributeError: module 'sdlc_board' has no attribute 'STUCK_RE'
E       assert '\n- STUCK: code: src/a.py:1: rename a\n' in 'STEP: approve\nROUND: 2\n...'
exit: 1

$ uv run --group dev pytest tests/test_board.py -q -k "labelled_b or decision_names_both or unreadable_reply_needs or higher_ones_step" -n 4
8 failed, 82 passed, 18 skipped in 1.91s
exit: 1

$ uv run --group dev pytest tests/test_land.py -q -n auto
78 passed in 39.05s
exit: 0

$ uv run --group dev pytest tests/test_factory.py tests/test_board.py tests/test_sdlc.py -q -n auto
758 passed, 18 skipped in 46.64s
exit: 0

$ uv run --group dev pytest tests/test_board.py -q -n auto
202 passed, 18 skipped in 44.80s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ ./check.sh
2560 passed, 18 skipped in 67.45s (0:01:07)
✔ Validation passed
exit: 0

$ git status --short
 M docs/REFERENCE.md
 M plugins/factory/README.md
 M plugins/factory/scripts/factory.py
 M scripts/board.html
 M scripts/board.py
 M scripts/sdlc.py
 M tests/test_board.py
 M tests/test_factory.py
 M tests/test_land.py
 M tests/test_sdlc.py
?? .sdlc/work/141-board-landing-track-truth/
```
