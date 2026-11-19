VERDICT: PASS

The real `retro` run finished, and its output matches the spec. Run on this repo, `retro` gives a `cost` block with dollars and minutes per landed change by tier, each with its `n` (13 Tier 2 changes, 6 Tier 1). Coverage reads 19 of 20 changes, with the hand-built one listed under "built by hand" instead of counted as $0 (R8).

Waste is null, as it should be here. Every earlier run predates purposes, so no change counts as measured. The waste coverage is 0 of 20, shown greyed, and says "runs recorded before purposes 19".

`retro --report` prints both new Coverage lines (R9). The waste line names the untagged count (172 runs untagged).

## Notes
- `checks.md` doesn't exist for this change, so there were no acceptance checks to read.
- The gate record `build/round-1.gate.md` is `GATE: PASS`.
- My earlier note that the real retro run was unread is now settled by the output above.

## Evidence
$ cat .sdlc/work/174-waste-tagged/build/round-1.gate.md | head -c 600
GATE: PASS … Exit: 0
exit: 0

$ uv run --group dev pytest -q -k "purpose or waste or cost_and_waste or runtime_values or ampersand or spend"
45 passed, 3175 deselected in 59.14s
exit: 0

$ uv run --group dev pytest -q -k "retro and (cost or report)"
18 passed, 3202 deselected in 74.97s
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro (JSON `cost` block), then `retro --report | grep -in "cost per\|waste"`
per_change {2: n=13, 1: n=6}; coverage 19 of 20; missing_because built by hand 1; waste.share null, coverage 0 of 20 greyed
15:- Coverage, cost per landed change: 19 of 20 changes; missing: built by hand 1.
16:- *Coverage, waste share: 0 of 20 changes; missing: runs recorded before purposes 19, built by hand 1; 172 runs untagged; a hint: under half the changes*
exit: 0
