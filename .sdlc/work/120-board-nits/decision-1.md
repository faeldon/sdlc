DECISION: ESCALATE

## Why

I'm escalating because both rounds were used up and one change was still open, so no other decision is allowed. The code looks right: all four seeds are built and tested, the full gate passed at 2252 tests, code and ui passed both rounds, and round 1's only kept change (the word "mend" in `WAYS_WHY`) is fixed and pinned by a test. Two things still need you: the ux reviewer's open CHANGE, which says the screenshots don't show the "line or two" outcome, and four decisions that were assumed and never confirmed (D1 to D4).

## Reconsider the approach

**What came back each round:** the shots built from fixture 006. Round 1's ux reviewer noted that card 006 still showed the old long `next:` sentence (about nine lines at 390px) and that "the short text appears only on the next stop". Round 2 made that a CHANGE, and the verifier kept it: `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md` still has the old `NEXT:` line with "mend" in it. The change never touched that file. Round 2's ui reviewer said the same thing, as a note.

**What should change: the plan, not the code or the approach.** Shortening `WAYS` itself and putting the longer text in the record's body is sound. Every reviewer agreed with it, and ux agreed explicitly (D3). But `plan.md`'s Files list and Work order cover only the code that writes a new stop record. Nothing in the plan updates the board fixture that the shots are rendered from. So the reviewers who judge by screenshot could never see outcome 2, and each round the builder fixed code that was already correct. Another build round would only fix the fixture. Doing that by hand before landing is cheaper and closes the CHANGE.

D4 matters here too. A real host's old stop record keeps its old sentence until the run is rerun, because the board writes nothing and so can't rewrite it. That's correct, but it explains why "line or two" won't show up on existing cards right away.

## Open items

- ux (round 2, kept by the verifier): `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md:2` still has the old run-on `NEXT:` line with "mend" in it. Regenerate it with the current `stop_text()` and reshoot at 390px.

## Decisions to confirm

- **D1:** change the wording in `factory.py`'s `WAYS` itself, not just in how the board shows it. This may conflict with 112, 113 or 119 in the `WAYS` block.
- **D2:** write a stop's need as `stopped: <instruction>` (for example `stopped: rerun to ask an agent again`), not the intent's example with a comma, because `status` joins needs with `, `.
- **D3:** keep D1 and D2 as they are (ux agreed).
- **D4:** a stop recorded before this change keeps its old `NEXT:` sentence until its next `verdicts --record`. The builder didn't say so in the README or a release note as ux suggested, so it's worth a line in the changelog.

## For the person at ship

1. **`plugins/factory/scripts/factory.py`:** look at the `WAYS` and `WAYS_WHY` blocks and the extra body line in `stop_text()`. Check the new line can't match `STOPPED_RE`, `NEXT_RE` or `PROBLEM_RE`, and watch for conflicts with 112, 113 and 119, which also edit `factory.py`.
2. **`scripts/sdlc.py`:** look at `FACTORY_STOP_NEEDS` and `needs_of()`. A round-1 nit flagged a nested f-string there.
3. **Fixture 006's `runs/stopped.md`:** refresh it, then look at the 390px shot.
4. **Dark theme:** no shot shows the `--stop` colour in dark mode (ui flagged this both rounds).

- IMPACT: patch — the board and `status` read better: a long next step wraps, a stop's next step is short, and its needs-you line is in plain words. Nothing anyone calls or reads by machine changes, since the stop record keeps its `STOPPED:`/`NEXT:`/`- PROBLEM:` shape.

## Undone items

- UNDONE: ux: `.sdlc/reports/shots/120-board-nits/round-2/index-390x844.png`, card 006 and the same card at 1280: the `next:` line still reads "rerun /sdlc-factory:build 006, whose one mend asks again for the missing ## Evidence or a verdict on the reply's first line; if that reply still lacks it, ship it by hand with /sdlc:ship 006". That is the old run-on sentence with the word "mend" in it, the text the intent says to shorten, so the phone-width outcome ("a stopped run's next step reads in a line or two") is not shown. The current `WAYS["mend"]` (`plugins/factory/scripts/factory.py:1980`) already reads "rerun /sdlc-factory:build {id}, or /sdlc:ship {id}". The board shows the stored `NEXT:` line verbatim (`scripts/board.html:292`, `board.py:632`), so this record was written before the change. Regenerate the stop record the shot is built from with the current `stop_text()` and reshoot at 390px, so the shot shows the outcome and not the old sentence. → seed: Refresh board fixture 006's stop record to the short NEXT wording and reshoot at 390px
