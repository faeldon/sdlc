# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] ux: `.sdlc/reports/shots/120-board-nits/round-2/index-390x844.png`, card 006 and the same card at 1280: the `next:` line still reads "rerun /sdlc-factory:build 006, whose one mend asks again for the missing ## Evidence or a verdict on the reply's first line; if that reply still lacks it, ship it by hand with /sdlc:ship 006". That is the old run-on sentence with the word "mend" in it, the text the intent says to shorten, so the phone-width outcome ("a stopped run's next step reads in a line or two") is not shown. The current `WAYS["mend"]` (`plugins/factory/scripts/factory.py:1980`) already reads "rerun /sdlc-factory:build {id}, or /sdlc:ship {id}". The board shows the stored `NEXT:` line verbatim (`scripts/board.html:292`, `board.py:632`), so this record was written before the change. Regenerate the stop record the shot is built from with the current `stop_text()` and reshoot at 390px, so the shot shows the outcome and not the old sentence. → done in round 3: the fixture's record is rewritten by `stop_text()`, and `test_the_board_fixture_stops_as_the_factory_writes` keeps it so; the round-3 shots show the short line.
