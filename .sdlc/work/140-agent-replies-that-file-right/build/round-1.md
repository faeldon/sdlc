I built all six slices of 140 and the gate is green. The work is uncommitted, as required; HEAD is still `4f1df6f`.

**First step: the real stream.** I recorded one short haiku session with `--output-format stream-json --verbose`. It started a background `sleep` and replied `VERDICT: PASS`. The background task's notice woke it again, which added a second `assistant` reply and a second `result` event. The second result's `total_cost_usd` is the session's running total (0.00438, then 0.00478). Its `usage`, `duration_ms` and `num_turns` count only that turn. So R5's split (last cost, everything else summed) matches what the stream actually holds. The recording is committed as `tests/fixtures/stream-two-replies.jsonl`.

**Slices built**
1. **The stream (R1, R3–R5).** `_claude()` now reads the stream and returns every reply in order. A `result` that repeats the reply before it counts once. `_figures()` takes the last cost and sums the rest. A session still fails on a non-zero exit, no `result`, an error on the last `result`, or no text. The fake `claude` in the tests now prints stream lines.
2. **The reply that holds the answer (R2).** A new `holds(role, reply)` checks for each role's answer. `agent` files the last reply that holds one, or else the last reply.
3. **One reader (R6, R7).** `opening()` finds a reply's verdict or decision, and `read_rounds()`, `land_verdict()`, `_land_task()` and `read_decision()` all read through it. A verdict after prose is now read where it stands. `preamble()` and `decision_preamble()` now mean only "answer lines that disagree, none of them first". The two mend prompts now say that.
4. **The copies (R8).** `board.py` has `opening()` and `sdlc.py` has `_factory_opening()`, each used where the first line was read before.
5. **The prompts (R9).** Every reviewer and the verifier now says the gate is the script's, where its record is, and to run nothing in the background. Tests they run are named and run in the foreground.
6. **The prose (R10).** I updated the AGENTS.md mend sentence, the factory README (*Shown, not said*), the build and land skills, `WAYS_WHY["mend"]` and the board fixture's `stopped.md`.

**Tests added, and what each proves**
- `test_claude_returns_every_reply_in_order` (R1): both replies come back, in order, with a repeated `result` counted once.
- `test_a_recorded_stream_with_two_replies_reads_both` (R3): the real recording yields the verdict and the wake-up note, `holds()` picks the verdict, and the figures come out right.
- `test_a_stream_without_a_result_or_with_an_error_fails` (R4): each failure case files no reply.
- `test_figures_sum_a_session_s_turns_and_take_its_last_cost` (R5).
- `test_a_second_reply_never_replaces_the_verdict` (R2). I checked it fails against filing the last reply: it filed `My verdict stands.`.
- `test_holds_picks_each_role_s_answer` (R2): what each role's reply must hold.
- `test_opening_reads_the_answer_line` (R6): 13 cases, from a shared table in `tests/fixtures/opening-cases.json`.
- `test_a_verdict_after_prose_is_read` (R6): for a reviewer, a status line before `CHANGES`, and the approver. A reply with no verdict is still `rerun`.
- R7: I rewrote the reviewer, approver and landing mend tests with disagreeing replies. The landing test now also proves a verdict after prose reads as `pass`.
- R8: pins in `test_board.py` and `test_metrics.py` run the shared table through each copy. A call-site test for each confirms the board and the metrics actually use it. I checked each fails against the old first-line reading.
- `test_no_reviewer_runs_the_gate_or_waits_in_the_background` (R9).

**Changed beyond the plan:** `test_skills.py` pinned the old "verdict written after a" wording, so I updated the pin to the new sentence. Some factory docstrings and comments still described the preamble rule, so I updated them. Both are recorded in `plan.md`.

**Left in `notes.md`:**
- The problem text `_no_verdict()` and `NO_DECISION` still says "doesn't open with…", as the spec chose. Rewording it would move the board's and status's text and their pins.
- The fixture trims its `system` lines to type, subtype, ids and task fields, because a real `init` event lists this machine's plugins and MCP servers.

No decisions raised this round.

## Evidence

$ ./check.sh
All checks passed!
257 files already formatted
2574 passed, 18 skipped in 129.52s (0:02:09)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable
475 passed, 18 skipped, 2099 deselected in 72.20s (0:01:12)
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k "second_reply_never"   # with `reply = replies[-1]` swapped in, then restored
E       AssertionError: assert 'My verdict stands.\n' == 'VERDICT: PAS...s its code.\n'
1 failed, 311 deselected in 0.45s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "after_prose"   # against the old first-line reading, then restored
E       AssertionError: assert None == 'READY'
1 failed, 214 deselected in 0.50s
exit: 1

$ uv run --group dev pytest -q tests/test_metrics.py -k "after_prose"   # against the old first-line reading, then restored
E       AssertionError: assert None == 'READY'
1 failed, 120 deselected in 0.19s
exit: 1

$ claude -p "<start 'sleep 5; echo done' in the background, then reply VERDICT: PASS>" --model haiku --output-format stream-json --verbose --allowedTools "Bash(sleep:*)" > /tmp/rec140/stream.jsonl
result success 'VERDICT: PASS\nThe draft reopens.' False 0.00437887 2 2322
result success 'The background command finished with exit code 0. Its output was `done`, from `sleep 5; echo done`.' False 0.00477998 1 954
exit: 0

$ git log --oneline -1
4f1df6f File 2026-11-18-39
