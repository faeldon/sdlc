VERDICT: PASS

The live `sdlc.py retro` run finished after all, and its output matches the spec. My first reply said I had no live run. That is now out of date: the run exited 0 and printed all three keys.

## Notes
- **`work_mix`:** n=14, unmeasured=0, with fix 2, capability 2, process 2 and debt 8. The shares are 0.14, 0.14, 0.14 and 0.57, and `mixed` is 4. Each is rounded to two places, as R2 says.
- **`time_to_users`:** n=0, `median_days` is null, `unmeasured` is 14 with `why: {"unreleased": 14}`, and `releases` is 0. The unreleased changes are counted apart and the median stays null, as R5 and R6 say.
- **`follow_through`:** since 2026-11-18, n=11, share 0.45.
  - The seeds line shows 6 seeds: 1 done, 5 carried.
  - The milestones line shows 5 milestones, 4 done; I only saw the output cut off after that count.
  - `missing` names the intent titles, which nothing records, as R9 says.
- There is no `checks.md` in the change folder, so there were no acceptance checks to read.
- The earlier pytest and metrics results, and the gate record `build/round-1.gate.md` (`GATE: PASS`), still stand. I did not rerun the gate.

## Evidence
$ uv run --quiet --script scripts/sdlc.py retro, then a Python filter for the three keys (this is the earlier command; its output file was read once it finished)
work_mix {"n": 14, "unmeasured": 0, "classes": {"fix": 2, "capability": 2, "process": 2, "debt": 8}, "shares": {...}, "mixed": 4}
time_to_users {"n": 0, "median_days": null, "unmeasured": 14, "why": {"unreleased": 14}, "releases": 0}
follow_through {"since": "2026-11-18", "n": 11, "share": 0.45, "unmeasured": 0, "missing": [...], "seeds": {"n": 6, ...}, "milestones": {"n": 5, "done": 4, ...}}
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_retro.py -k "work_mix or time_to_users or follow_through or value_figures or same_figures or process_work or fixes_line or ampersand or program or hand_gate"
12 passed in 21.01s
exit: 0

$ uv run --group dev pytest -q tests/test_metrics.py -k "ampersand or program or hand_gate"
39 passed, 158 deselected in 0.82s
exit: 0

$ head -8 .sdlc/work/168-*/build/round-1.gate.md
GATE: PASS / Verdict: PASS / Command: ./check.sh / Exit: 0
exit: 0
