VERDICT: PASS

`retro` now prints the `autonomy` block in its JSON, and the repo's gate is green on this rebased build.

## Notes
- **`checks.md`:** the change has none, so there were no acceptance checks to read.
- **End-to-end path:** I ran `sdlc.py retro` on this repo. It printed `autonomy` with escalations, asked, kept_default, overturned, auto_landed, spurious_stops and looks, each with its `n`. The one change built by hand is counted apart (`by_hand: 1`), not as a zero, and the 13 factory changes make up the `n`.
- **`overturned`:** it prints `count: null` with `unmeasured` set. The spec says no writer records an overturned settled call, so this is the expected output.
- **Gate:** `build/land-1.gate.md` is `GATE: PASS` (`./check.sh`, exit 0). I did not rerun the suite.
- **Landing's conflict resolution:** the only conflict was in `tests/test_retro.py`, where the 168 and 169 test sections were both kept. `land-1.md` records 167 passing in that file.
- **Not run:** I did not exercise the status nits, the after-gate stop's wording, or `--report` output separately. The gate's tests cover them.

## Evidence
$ cat .sdlc/work/169-decisions-and-stops-counted/build/land-1.gate.md | head -12
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
Seconds: 314.2
Tree: unchanged
(the file's first 12 lines; the rest is its output)

$ ls .sdlc/work/169-decisions-and-stops-counted/checks.md
No such file or directory
(a read, so it shows its own output)

$ git diff --stat babfa8f5d6d5398a677707cedb2f0ff022f896cd...HEAD | tail -20
37 files changed, 1558 insertions(+), 31 deletions(-)
(a read, so it shows its own output)

$ uv run --quiet --script scripts/sdlc.py retro | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('autonomy'),indent=1))"
{ "factory": 13, "by_hand": 1, "escalations": {"total": 3, "changes": 3, "per_change": 0.23, "n": 13}, "asked": {...}, "kept_default": {"kept": 5, "changed": 0, "rate": 1.0, "n": 5, ...}, "overturned": {"count": null, "n": 0, "unmeasured": "..."}, "auto_landed": {...}, "spurious_stops": {"build": 1, "landing": 1, ...}, "looks": {...} }
exit: 0
