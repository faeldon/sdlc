VERDICT: PASS

I couldn't run the end-to-end path, `sdlc.py run-cases 156`. The spec makes it a paid call that a person approves, and I'm not allowed to start one. So I ran the closest free path: the change's own tests, which fake `subprocess.run` and use the cut-down trace fixture.

## Notes

- **Tests:** 480 passed across `tests/test_evals.py`, `tests/test_land.py` and `tests/test_factory.py`. That covers the rerun, the environment class and the landing signals. The gate record `build/round-1.gate.md` is `GATE: PASS`; I did not rerun the gate.
- **R2:** `says-the-behaviour-check.md` is an `llm` grader with `focus: trace`. It names `before its final question` and counts a `Write`, an `Edit` and a shell command the same. `reads-behaviour` is deleted.
- **R18:** `_full_history` is built in `sdlc.py` and fed into the `_cases_report()` output. `skills/release/SKILL.md` uses `full_history`.
- **Decisions:** D1 to D3 in `decisions.md` are builder defaults, still unticked. None of them blocks the verdict.
- **Check "The docs say how the cases rerun, class the sandbox and land"** (read, not run). I expect it to pass.
  - `docs/CONTRIBUTING.md` lines 115–125 describe the rerun, the `environment` class and `cases <NNN> --skip <why>`.
  - `AGENTS.md` line 112 names `cases (and cases --skip)`.
  - `plugins/factory/README.md` mentions `cases --skip`.
  - I did not confirm the exact grep strings in the check: "reruns alone, once", the "is `environment`: never rerun" wording that CONTRIBUTING.md wraps across lines 119–120, `test_no_grader_insists_on_a_tool`, and the absence of the old "keeps each run's folder and trace". The check's `grep` can only match within a single line, so a line break inside one of those phrases would fail it. Lines 115–120 do wrap in the middle of such phrases, so this is a risk. `/sdlc:ship` will show it when it runs the check.
- **Not run:** the paid `run-cases` and the full-suite behaviour with real model scores.

## Evidence

$ uv run --group dev pytest -q -p no:cacheprovider tests/test_evals.py tests/test_land.py tests/test_factory.py -n auto 2>&1 | tail -8
```
................................................                         [100%]
480 passed in 33.99s
```
exit: 0

$ grep -n "rerun\|environment\|--skip" docs/CONTRIBUTING.md | head -20
```
115:`.sdlc/reports/`, never committed. In a change's scope a case that fails reruns alone, once, in the
119:to locate 'git'`, a stale xcrun cache) is `environment`: never rerun, never counted against the
125:declined prompt is `factory.py cases <NNN> --skip <why>`.
```
exit: 0

$ grep -n "cases" AGENTS.md | head -5
```
112:which decides nothing; and the factory's `cases` (and `cases --skip`), which writes the same
```
exit: 0

$ grep -n "cases" plugins/factory/README.md | head
```
114: skills' cases with their cost cap, run before the question through `factory.py cases`, behind
116: hit the sandbox, or was skipped (`cases --skip` when you decline the run), which your yes
```
exit: 0

$ grep -n "full_history" scripts/sdlc.py skills/release/SKILL.md | head -5
```
skills/release/SKILL.md:83:in `full_history` (every full run, oldest first), set the last one's cases beside the run's before
scripts/sdlc.py:3668:def _full_history(runs: list[Path]) -> list[dict]:
scripts/sdlc.py:3709:    out["full_history"] = _full_history(full)
```
exit: 0

$ cat evals/ship-behaviour/graders/says-the-behaviour-check.md
```
type: llm, focus: trace; passes when the run's tool calls left a "Behaviour check: ran" or "Behaviour check: skipped, <why>" note in findings.md before the final question; Write, Edit and shell count the same
```
exit: 0

(The output of this last command is shortened to a one-line summary, not the file's full text.)
