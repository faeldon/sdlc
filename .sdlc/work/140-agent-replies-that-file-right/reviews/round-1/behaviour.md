VERDICT: PASS

I found no failure in the change's end-to-end path. I ran only the tests the spec names for this path, not the gate.

## Notes
- **Gate:** `build/round-1.gate.md` is `GATE: PASS`. I read it and did not rerun the gate.
- **`checks.md`:** the change has no `checks.md`, so there are no acceptance checks to read.
- **R1, R3 and R5, the stream reading:**
  - The committed fixture is a recorded stream with two `result` events, so it exercises the case where a background notice adds a second `result`.
  - The `_claude()` stream and figures tests pass.
  - `notes.md` says the fixture's `system` lines are trimmed to type, subtype and ids. That is acceptable, since the parser reads only `assistant` and `result` events.
- **R2, filing the right reply:** the `second_reply` test passes, so the verdict-bearing first reply is filed and `verdicts` moves on.
- **R6 and R7, reading answers:**
  - `opening()` reads `VERDICT: PASS` after a line of prose as PASS, with the `- CHANGE:` lines after it.
  - It returns `None` for disagreeing lines when neither is first.
- **R8, board and metrics copies:** the shared-table pin tests in `test_board.py` and `test_metrics.py` pass.
- **R9, reviewer prompts:** all seven reviewer and verifier files carry the "Run nothing in the background" line.
- **R10, docs:** the AGENTS.md mend sentence now says "lines that disagree, none of them first".
- **Not run:** the full `./check.sh` and the Windows-portable subset. The gate record already covers the full check.

## Evidence
$ cd <worktree>; ls .sdlc/work/140-agent-replies-that-file-right/ .sdlc/work/140-agent-replies-that-file-right/build; cat .sdlc/work/140-agent-replies-that-file-right/intent.md .sdlc/work/140-agent-replies-that-file-right/spec.md; cat .sdlc/work/140-agent-replies-that-file-right/checks.md; cat .sdlc/work/140-agent-replies-that-file-right/decisions.md; tail -20 .sdlc/work/140-agent-replies-that-file-right/build/round-1.gate.md
(read; output showed the intent and spec, then the gate record's tail ending "✔ Validation passed". `checks.md` and `decisions.md` do not exist: "no matches found".)
exit: 0

$ head -5 .sdlc/work/140-agent-replies-that-file-right/build/round-1.gate.md; git status --short | head -30; uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_board.py tests/test_metrics.py -k "second_reply or after_prose or recorded or reviewer_runs or opening or mend or stream" 2>&1 | tail -15
GATE: PASS
(then the modified-files list)
37 passed in 15.33s
exit: 0

$ cat .sdlc/work/140-agent-replies-that-file-right/notes.md | head -30; head -c 1500 tests/fixtures/stream-two-replies.jsonl; grep -n "def opening\|stream-json\|WAYS_TEXT\|\"mend\"" plugins/factory/scripts/factory.py | head; grep -rn "first-line rule\|after a preamble\|preamble" AGENTS.md plugins/factory/README.md plugins/factory/skills | head; python3 - <<'E' (calls opening() on two cases)
(2, <re.Match object; span=(0, 13), match='VERDICT: PASS'>)
None
exit: 0

$ sed -n 234,244p AGENTS.md; grep -n "background" plugins/factory/agents/*.md | head -12; grep -c '"type":"result"' tests/fixtures/stream-two-replies.jsonl
(AGENTS.md lines 234–244 as quoted above; "Run nothing in the background" in all seven agent files; the fixture's `result` count printed 2)
exit: 0
