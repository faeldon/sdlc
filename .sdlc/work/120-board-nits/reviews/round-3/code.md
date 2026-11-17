VERDICT: PASS

## Notes

- Nit: `tests/test_next_up.py:620-621` has `STOP_NEXT` holding the old `rerun` sentence ("fix its cause, then /sdlc-factory:build 001, or ship it by hand with /sdlc:ship 001"). Its comment says the record is "as `factory.py verdicts --record` writes one (its `stop_text()`)", which this change made untrue. The test passes because it doesn't pin the wording. Update the constant to the current `WAYS["rerun"]` text, or reword the comment. This is the change's own doing, so it's not PREEXISTING.
- Optional: decision D4 (a stop recorded before this change keeps its old `NEXT:` sentence until its next `verdicts --record`) is confirmed, but neither `docs/REFERENCE.md` nor `plugins/factory/README.md` says so. The builder may add one line where a host reads about stops. The person's note asked that they know it.
- Nit: `sdlc.py:4120` nests an f-string inside an f-string: `f"stopped: {way or f'read {FACTORY_STOPPED.as_posix()}'}"`. Compute the label into a variable first, as the line above it already does for `way`.
- Nit: `test_each_way_on_fits_two_lines_at_phone_width` asserts length ≤ 90 characters, a proxy for "two lines at 390px", as the plan said. The docstring says "two lines", so the test name and docstring overstate what is checked. Either say "about two lines" or leave it, since the plan accepted the proxy.
- Kept ux item, checked: `.sdlc/reports/shots/120-board-nits/round-3/ux/index-390x844.png` already shows card 006's `next:` as `rerun /sdlc-factory:build 006, or /sdlc:ship 006`, and its `needs you:` line as `stopped: rerun to ask an agent again`. The round-2 sentence is gone. The fixture `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md` matches `stop_text()` byte for byte, and `test_the_board_fixture_stops_as_the_factory_writes` keeps it so. I checked the 390px shot only; the 1280px shot shows the same record. I did not regenerate the record or reshoot, since this review is read-only; the round-3 shots already reflect the regenerated record.
- Settled points were not re-raised, including the `WAYS_WHY["mend"]` wording.

Done well:
- `WAYS` is kept to the command and a few words, with the explanation in `WAYS_WHY` in the record body. The record's `STOPPED:`, `NEXT:` and `- PROBLEM:` shape is unchanged, and `test_the_stop_record_says_why_and_reads_as_before` pins that `sdlc.factory_stop()` reads the same fields.
- The needs texts carry no comma and no `mend`, and `test_a_stop_s_need_is_in_plain_words` pins both. The docs (`REFERENCE.md`, `status/SKILL.md`) match the code.
- `_progress()` is parenthesised with its result unchanged. `test_a_stop_hides_the_step_track_as_it_always_has` covers the stop test at each stage, and the acceptance grep in `checks.md` passes against `scripts/board.py`.
- The `.next code` wrap rule is pinned by a test.

Tests and commands run:
- Full suite, `uv run --group dev pytest -q -n auto` with no cache and no bytecode written: 2254 passed, 13 skipped.
- Targeted: `tests/test_next_up.py`, 33 passed.
- `ruff check` and `ruff format --check` on the changed Python: clean.
- The acceptance grep from `checks.md`: passes.
