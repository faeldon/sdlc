VERDICT: PASS

The kept finding is done. `_stopped(folder)` now returns `sdlc.factory_stop(folder)` (board.py:352–356), and `STOPPED_RE`, `NEXT_RE` and `PROBLEM_RE` are gone from board.py. Nothing else in the repo names them. The `problems` parameter is dropped, and the `_entry` call site passes only `folder`. `test_an_unreadable_stop_record_is_a_stop_as_in_status` pins the wiring with `card["stopped"] == sdlc.factory_stop(folder)`. `test_the_factory_parsing_is_a_pinned_copy` no longer lists the stop regexes.

## Notes

- Nit: `scripts/board.py` lines 12–14, the module docstring. The rewrap after "read by `sdlc.factory_stop()` as `status`" leaves "reads it. Its card's step track is the step the" short, so the paragraph reads raggedly. Rewrap it to the 100-column width the rest of the paragraph uses.
- PREEXISTING: scripts/board.py:393: `if entry.get("stopped") or (folder / STOPPED).is_file() and entry["stage"] == "build":` mixes `or` and `and` with no parentheses. The `and` binds first, so it reads as intended, but it is easy to misread. This line is in `_progress()`, which this change doesn't touch. Parenthesise it when someone next edits `_progress()`.
- Done well: the change removes the duplicate reader rather than adding a test to catch its drift. The card and `status` now share one function, and the `next` text for an unreadable record comes from the same place on both surfaces.
- Also done well: `BOTH` makes the two multi-state pairs explicit in the precedence test, so a new overlap can't pass silently.
- Unsure about nothing material. The `and`/`or` precedence above is only a readability risk; I checked that `factory_stop()` never returns None for a file that exists, so the second clause can't change the result.

Tests and checks run in the worktree:
- `uv run --group dev pytest tests/test_board.py tests/test_metrics.py tests/test_sdlc.py tests/test_factory.py -q -n auto`: 666 passed, 13 skipped.
- `ruff check` on `scripts/board.py` and `tests/test_board.py`: clean.
- `ruff format --check` on the same two files: clean.

I did not run the full `./check.sh` gate, which includes `claude plugin validate --strict`.
