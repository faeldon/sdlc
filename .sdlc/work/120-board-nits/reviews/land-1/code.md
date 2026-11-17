VERDICT: PASS

## Notes

- Nit: `tests/test_next_up.py:620-621`. `STOP_NEXT` still holds the old `rerun` sentence ("fix its cause, then /sdlc-factory:build 001, or ship it by hand with /sdlc:ship 001"), and the comment above it says the record is as `stop_text()` writes it, which this change made untrue. The test passes because it doesn't pin the wording. Set the constant to `WAYS["rerun"]`'s current text, or reword the comment. The round-3 review raised this too and the landing diff doesn't touch it.
- Nit: `scripts/sdlc.py` (`needs_of()`, about line 4352) nests an f-string inside an f-string: `f"stopped: {way or f'read {FACTORY_STOPPED.as_posix()}'}"`. Compute the fallback into a variable first, as the line above does for `way`.
- Nit: `test_each_way_on_fits_two_lines_at_phone_width` checks a length of at most 90 characters, a proxy for two lines at 390px. Its name and docstring say "two lines", which overstates what is checked. The plan accepted the proxy, so either say "about two lines" or leave it.
- Optional: decision D4 (a stop recorded before this change keeps its old `NEXT:` sentence until its next `verdicts --record`) is confirmed but not stated in `docs/REFERENCE.md` or `plugins/factory/README.md`. A line in the changelog or release note would tell the person.
- Optional: in `skills/status/SKILL.md`, the reflowed paragraph's line ending "never" runs to 110 characters, against about 100 elsewhere in the file. Reflow it.

## Done well

- Each of the four seeds is built and pinned. `.next code` has `overflow-wrap: anywhere`, and `test_a_long_next_step_wraps_inside_its_card` checks it. `_progress()` is parenthesised with its result unchanged, and `test_a_stop_hides_the_step_track_as_it_always_has` checks it at each stage. The needs-you wording is plain, has no comma and no `mend`, and `test_a_stop_s_need_is_in_plain_words` pins that.
- `WAYS` is shortened to the command and a few words, and the longer sentence goes in the record's body through `WAYS_WHY`. `test_the_stop_record_says_why_and_reads_as_before` shows `factory_stop()` reads the same fields and the new line matches none of the three record regexes. The record's shape is kept.
- `test_the_board_fixture_stops_as_the_factory_writes` keeps the 006 fixture in step with `stop_text()`, so the screenshots can't go stale again.
- The landing diff's `.sdlc/work/inbox.md` removal is only seeds 81–84, which this change built. Seeds 63 and 76 were already gone on the base, so the resolution is correct.
- The docs (`REFERENCE.md`, `plugins/factory/README.md`, `status/SKILL.md`) match the code's needs and `WAYS` wording.

## Tests and commands run

- `uv run --group dev pytest -q -n auto tests/test_board.py tests/test_factory.py tests/test_sdlc.py tests/test_skills.py tests/test_defaults.py`: 1080 passed, 13 skipped.
- I did not run the full `./check.sh` gate or the acceptance `sh` block in `checks.md`. The builder's land-1 gate run reports the full suite passing, and the round-3 review checked the acceptance grep.
