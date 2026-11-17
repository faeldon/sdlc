VERDICT: PASS

The kept ux change is done. `WAYS_WHY["mend"]` now reads "Rerunning /sdlc-factory:build {id} asks an agent again, once, for the reply in its shape; if that reply still lacks it, ship it by hand with /sdlc:ship {id}." It no longer says "mends it once", and the wording is the one the ux reviewer suggested. The reworked `test_each_way_on_fits_two_lines_at_phone_width` now fails if "mend" appears in either the `NEXT:` line or the longer text for any way, so the jargon cannot come back unnoticed.

I checked the other reworked code for new problems and found none. The `WAYS_WHY` text is appended to the record's body in `stop_text()` and matches none of `STOPPED_RE`, `NEXT_RE` or `PROBLEM_RE`, so the readers are unaffected. Its `.format(id=…)` calls contain no stray braces.

## Notes

- The word "mend" still appears in the `STOPPED:` value of `runs/stopped.md`, which the code parses, and in docstrings. The builder noted this, and it is correct to leave it: the drawer and the needs line are what a person reads.
- I did not run any tests, because the review is read-only. The builder's round-2 evidence shows the focused test failing before the rewording and passing after, and the full `./check.sh` at 2252 passed, 13 skipped. I checked the diff by reading it, not by rerunning the gate.
- Unsettled, and not raised again here: the round-1 ux note that the card's stop wording and the needs line use different verbs for the same step ("review an agent's commit" against "read the commit"). It sits in code this round did not rework, so it is not a CHANGE here.

## Done well

- The "mend" test is a pin on the person's wording, not on the code's internals, so a future edit to either text that reintroduces the jargon fails the gate.
- The record keeps its shape for every existing reader, and the new body line is pinned as invisible to `factory_stop()`.
