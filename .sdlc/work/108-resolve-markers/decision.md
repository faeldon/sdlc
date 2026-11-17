DECISION: ESCALATE

**Why.** The build looks ready. The one code reviewer passed round 1, and the gate passed on the full `./check.sh` run (2174 passed, 9 skipped). The builder also showed the three new or changed tests failing on the old code. Every outcome in the intent has code and a test behind it. I'm escalating for one reason only: `decisions.md` has an unticked default. The build assumes that a line of exactly seven `=` counts as a marker, and that call has to be yours before this lands.

**Open items**
- None. The code reviewer's round 1 verdict is PASS and nothing is required. Its optional notes: the new test checks the shared pattern directly rather than going through each script's resolve, but the existing tests in `test_land.py` and `test_resolve.py` do go through both. It also noted that a CRLF separator line or a marker with no label isn't matched. The CRLF case is moot in practice: both checks read files with `read_text`, which turns `\r\n` into `\n`. Git always puts a label on the opening and closing markers.

**Decisions to confirm**
- D1: a line of exactly seven `=` is matched as a conflict separator, as the intent says. The cost is that a Markdown heading underlined with exactly seven `=` in a conflicted file would be refused.
- D2: the builder logged the same question twice, so this is a copy of D1. Settle it with D1 and strike one of the two.

**For the person at ship**
1. Start with the shared pattern `^(?:<{7} |={7}$|>{7} )` with `re.M`, at `scripts/sdlc.py:103` and `plugins/factory/scripts/factory.py:81`. Check that both resolve paths use it, at `sdlc.py:3901` and `factory.py:3631`.
2. Then read the new test, `tests/test_land.py::test_a_conflict_marker_is_matched_only_as_a_whole_line` (around line 1435). It holds the factory's copy to the same pattern as `sdlc.py`'s and runs each script's own source past the check.
3. There's no `notes.md` and no `plan.md`. That's fine at Tier 1, and the builder's report says nothing was left over.

- IMPACT: patch — a resolve in sdlc or the factory no longer refuses a correctly resolved file that quotes a run of seven `<`. Nothing new anyone can do, and no interface changed.

There are no unticked `- [ ]` items, because this change has no `notes.md`. The prompt names no irreversible paths, so there are no recovery lines.
