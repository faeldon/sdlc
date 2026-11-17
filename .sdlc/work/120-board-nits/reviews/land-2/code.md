VERDICT: PASS

## Notes

- Nit: `tests/test_next_up.py:620-621`. `STOP_NEXT` still holds the old sentence ("fix its cause, then /sdlc-factory:build 001, or ship it by hand with /sdlc:ship 001"), and the comment above it says the record is as `stop_text()` writes it, which this change made untrue. Land-1 and round-3 both raised it and it is still open. Set the constant to the current `WAYS["rerun"]` text, or reword the comment.
- Nit: `scripts/sdlc.py`, `needs_of()` (about line 4352), nests an f-string inside an f-string: `f"stopped: {way or f'read {FACTORY_STOPPED.as_posix()}'}"`. Compute the fallback into a variable first, as the line above does for `way`. Raised in land-1 and round-3, still open.
- Nit: `test_each_way_on_fits_two_lines_at_phone_width` checks at most 90 characters, a proxy for two lines at 390px, but its name and docstring say "two lines". Say "about two lines", or leave it, since the plan accepted the proxy.
- Nit: `skills/status/SKILL.md`, the reflowed paragraph. Its line ending "quote it, never" is longer than the paragraph's other lines. Reflow it.
- Optional: decision D4 (a stop recorded before this change keeps its old `NEXT:` sentence until its next `verdicts --record`) is confirmed but not stated in `docs/REFERENCE.md` or `plugins/factory/README.md`. The changelog or impact line at ship is the other place it could go.

Checked against the spec, nothing needs a CHANGE:
- Outcome 1, the wrap: `.next code` carries `overflow-wrap: anywhere`, and `test_a_long_next_step_wraps_inside_its_card` pins it.
- Outcome 2, the stop line: `WAYS` is shortened and the longer text is in `WAYS_WHY`, written into the record's body. `factory_stop()` reads the same fields, and the new line matches none of `STOPPED_RE`, `NEXT_RE` or `PROBLEM_RE`. Both pinning tests are present.
- Outcome 3, the stop test: `_progress()` is parenthesised, and its result is pinned at each stage by `test_a_stop_hides_the_step_track_as_it_always_has`. The acceptance grep in `checks.md` matches the new line in `board.py`.
- Outcome 4, the needs-you wording: `FACTORY_STOP_NEEDS` has no comma and no `mend`, and `test_a_stop_s_need_is_in_plain_words` pins it. The three pinned tests were updated to the new wording.
- The fixture: the test that keeps `006-draft-purge/runs/stopped.md` equal to `stop_text()` output passes.
- The rebase: `6168f16` is the only commit above `a2f7996`, so the diff is this change's alone. The register change removes exactly seeds 81–84 (24 lines, nothing else), which the land-1 review also found correct.

## Done well

- The record's `STOPPED:`, `NEXT:` and `- PROBLEM:` shape is unchanged, and the new body line is kept out of every reader's regex.
- The docs (`REFERENCE.md`, `factory/README.md`, `status/SKILL.md`) match the code's `WAYS` and needs wording.
- The board's stop test keeps its result, and the parenthesisation is pinned by a checks.md acceptance grep, which a unit test can't do.

## Tests and commands run

- `uv run --group dev pytest -q -p no:cacheprovider -n auto` on `test_board.py`, `test_factory.py`, `test_sdlc.py`, `test_next_up.py`, `test_skills.py`, `test_defaults.py` and `test_metrics.py`, with bytecode off: 1231 passed, 13 skipped.
- I did not run the full `./check.sh` gate, the `ruff` checks, or the `checks.md` acceptance block myself. The land-2 gate record reports the full gate passing (2309 passed, 13 skipped).
