DECISION: ESCALATE

**Why.** All five round-1 reviewers gave `VERDICT: PASS`, and every requirement from R1 to R10 has code and a test that would fail without it. But the code and test reviewers both ran the suite after the gate and got 2573 passed, 1 failed. The failure is `tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden`, set off by this round's own `reviews/round-1/behaviour.md`. Its `## Evidence` commands write `.sdlc/work/140-agent-replies-that-file-right/`, and that matches the test's `\bwork/\d{3,}\b(?!-)` pattern for citing a change by number. The file is committed with the change, so the landing gate will be red until someone changes it. Changing a reviewer's filed report is the person's call, not mine.

**Open items**
- Red gate from `reviews/round-1/behaviour.md` (lines 22, 26 and 32 run `.sdlc/work/140-agent-replies-that-file-right/…`). Raised by the code and test reviewers. The test reviewer also could not confirm that this one file accounts for all four extra items in the assertion.
- NIT F1: `factory.py:3840` uses `replies[-1]` as a fallback. That is safe only because `_claude()` never returns an empty list without a problem, and a one-line comment should say so. Raised by the code reviewer; recorded in `findings.md`, not blocking.

**Decisions to confirm**
- None. The change has no `decisions.md`, so there are no blocking lines and no open defaults.

**For the person at ship**
- First, decide how to clear the red gate:
  - put the change's slug in place of `140*` in the behaviour report's Evidence commands (for example `.sdlc/work/140-agent-replies-that-file-right/`), or
  - rerun the behaviour review.
  
  Then rerun `./check.sh` and confirm `test_nothing_local` accounts for every extra item.
- Then the policy edit in `AGENTS.md`'s *The factory* sentence and the factory README's *Shown, not said*. A verdict or decision after prose is now read instead of mended. That overturns the first-line rule from bug 2026-11-17-18, which the spec says your approval covers.
- Then `_claude()` and `_stream()`, and `holds()` in `cmd_agent` in `factory.py`.
- Then confirm the `opening()` copies in `scripts/board.py` and `scripts/sdlc.py` (`_factory_opening()`) match `factory.py`'s.
- Last, confirm `tests/fixtures/stream-two-replies.jsonl` holds no local names.

- IMPACT: patch — factory runs stop less often over how a reply was laid out, and a reviewer's verdict is no longer lost to a later reply. Nothing a host configures or calls changes; the trailers and the mend's once-a-round rule are unchanged.

**Each undone item's disposition**
- UNDONE: `_no_verdict()` and `NO_DECISION` still say "doesn't open with VERDICT…/DECISION…", which the spec kept so the board's and status's problem text doesn't move. Since `opening()` now reads an answer after prose, the words now mean "holds no answer the script reads". A rewording would change the board's and status's text together, and their pins with it. → seed: Reword `_no_verdict()` and `NO_DECISION` now that an answer after prose is read
- UNDONE: `tests/fixtures/stream-two-replies.jsonl` keeps only the type, subtype, ids and task fields of its `system` and `rate_limit_event` lines. A real `init` event lists the machine's plugins, skills and MCP servers, which name local projects. The `assistant`, `user` and `result` lines are whole, with paths replaced by `<path-to-clone>` and `<home>`. → dropped: this explains a deliberate trim, not leftover work; the parser reads only `assistant` and `result` events, and the behaviour reviewer accepted it.
