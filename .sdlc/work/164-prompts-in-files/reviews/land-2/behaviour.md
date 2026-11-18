VERDICT: PASS

## Notes
- The spec's end-to-end path is that every task's prompt is the same bytes as before and a mismatched placeholder is refused. `tests/test_prompts.py` covers both. It has 59 tests, and all pass. They compare each task's prompt with a recorded copy in `tests/prompts/`.
- The gate record `land-2.gate.md` shows `GATE: PASS` for build `62ee20666cca99cf`.
- `plugins/factory/prompts/` holds 15 files, and none contains a machine path.
- `plugins/factory/README.md` says where the prompts are (line 294).
- `checks.md` does not exist in this change folder, so there are no acceptance checks to read.

## Evidence
$ cat .sdlc/work/164-prompts-in-files/build/land-2.gate.md | head -12
GATE: PASS
Attempt 1: Verdict PASS, Command `./check.sh`, Build 62ee20666cca99cf, Exit 0, Tree unchanged
exit: 0

$ uv run --group dev pytest tests/test_prompts.py -q
59 passed in 8.38s
exit: 0

$ grep -n "prompts" plugins/factory/README.md | head -5; ls plugins/factory/prompts | wc -l; grep -rn "/Users/" plugins/factory/prompts | head -3
94:  yes the skill runs each change's acceptance checks and cases behind their own prompts, then
294:**What each agent is told** for each step is text in `plugins/factory/prompts/`, one file per task
298:edit there, not in the script. The prompts are read only from the plugin itself, never from a
15
exit: 0
