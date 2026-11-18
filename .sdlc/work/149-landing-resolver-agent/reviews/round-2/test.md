VERDICT: PASS

The change kept last round was made. The card's `next:` line now reads "its agent is resolving a conflict". This is at `scripts/board.py:843`, and the same wording is in `tests/test_board.py:1216` and `:1424`. `docs/REFERENCE.md` no longer says the builder resolves the conflict.

## Notes
- Test command: `uv run --group dev pytest tests/test_board.py -q -n auto`. It gave 265 passed and 28 skipped.
- I did not rerun the repo's gate. Its record is under `build/`.
- No `checks.md` sections were reviewed this round.
