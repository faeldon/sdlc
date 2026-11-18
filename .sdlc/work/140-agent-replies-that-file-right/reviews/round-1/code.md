VERDICT: PASS

I found no Critical or Required problems. The one failing test is caused by this round's own behaviour report, not by the change's code.

The full gate ran 2573 passed and 1 failed. The failure is `tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden`. It flags 3 lines in `reviews/round-1/behaviour.md` (the behaviour reviewer's report from this round). The first is line 22, a `$ cd <worktree>; ls .sdlc/work/140-agent-replies-that-file-right/ …` command that cites a change folder by number. The builder can't fix that, because the report is written by the reviewer, not the builder. The report needs scrubbing before it is committed at ship or landing, or the gate will fail then.

## Notes
- Every requirement R1–R10 has code and a test. I checked these paths:
  - R1: `_stream()` and `_claude()` read the stream, with the `result` that repeats an earlier reply counted once.
  - R2: `holds()` plus `cmd_agent` file the last reply that holds the answer.
  - R5: `_figures()` sums over the `result` events and takes the last cost.
  - R6 and R7: `opening()` is the one reader, and `_disagrees()` narrows `preamble()` and `decision_preamble()` to disagreeing lines.
  - R8: the copies in `board.py` and `sdlc.py` match `factory.py`'s and are pinned over the shared table `tests/fixtures/opening-cases.json`.
- The mend texts and `WAYS_WHY` were updated to match.
- Replies with no answer line are still stopped.
- The 2026-11-18-26 case is handled and covered by a recorded stream fixture, as REVIEW.md asks.
- NIT: plugins/factory/scripts/factory.py:3840: `replies[-1]` is a safe fallback only because `_claude()` guarantees a non-empty list when it returns no problem. A one-line comment saying so would help. {robustness S low}
- I ran `./check.sh`, the full gate (result above), and read the diffs of `factory.py`, `board.py` and `sdlc.py`.
