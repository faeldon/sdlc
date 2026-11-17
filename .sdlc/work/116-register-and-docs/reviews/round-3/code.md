VERDICT: PASS

## Notes

- The settled point is done. The paragraph at `docs/CONTRIBUTING.md:193` now lists the commands that go through `_intake_tracker()`: `intake`, `dangling`, `titles` (through `closes` and `preflight`), `needs-info`, `mark-triaged` and `sync`. It then says close's record step calls `mark()`, `open_marks()` and `open_numbers()` whenever the tracker has `mark()`, with no `intake()` needed. I checked this against `cmd_close` (`hasattr(found, "mark")`, scripts/sdlc.py ~4735), `mark_issues()`, and the `_intake_tracker()` call sites. Close's behaviour is unchanged.
- The reworked `sync` path matches the agreed round-1 decision (R1: wire `unmark`). `withdraw_issues()` reads `open_marks()` in the shape the GitHub tracker returns (`triaged`, `comments`), and it only unmarks issues this change marked that nothing else records. `docs/REFERENCE.md` describes that behaviour correctly.
- I accept builder default D2 (sync only, not close or `mark-triaged`). Close's pass would undo issues the same push is about to close.
- Cost, on D3 (builder default: list every open issue with its comments on each `sync`): this is a fair trade-off, since a change that removed its whole `closes:` line still needs the listing to find what to withdraw. The listing has a limit of 1000 issues with comments on every sync. If that ever shows up as slow, the fix is to record which issues each change marked, not to skip the listing.
- Nit: `docs/CONTRIBUTING.md` around line 199 has a short line mid-paragraph ("`closed_by()` is read" / "on its own, whenever…"). Reflow it to the paragraph's width.
- Done well: the new `test_sync_sends_an_issue_that_left_the_closes_line_back_to_triage` covers the three cases that matter: a withdrawn issue, a shared issue another record holds, and a person's label. It also checks that a rerun posts only one comment.

**Tests and commands run:** `uv run --group dev pytest -q -p no:cacheprovider tests/test_archive.py -k "left_the_closes_line or closes_once or sync"` gave 12 passed. `ruff check --no-cache` and `ruff format --no-cache --check` on `scripts` and `tests` both passed. I did not run the full `./check.sh` because this review is read-only. The builder's recorded gate covers the rest.
