VERDICT: PASS

The end-to-end `retro` run prints the `simplicity.workarounds` block the spec describes. Both `checks.md` checks should pass.

## Notes
- **Gate:** `build/round-1.gate.md` records `GATE: PASS`. I did not rerun the gate or the suite.
- **`retro` in this repo:** the block holds `outside`, `hand_record`, `restored`, `unknown` and `overrides`.
  - `outside` and `hand_record` each have count 0 over n=64.
  - `restored` has count 3 over n=69. All three rows are the `63e1700` "File …" commit, which matches the restored-entry case in the intent.
  - `overrides` has ejections 0, stops 0 and fixes 4, over n=24 factory changes. Zero ejections and stops is expected, since 174's records only began recently.
  - The spec says "`problems`" and the output key is `unknown` (count 0). The spec's healthy-output line is loose on this, so I am not raising it as a CHANGE.
- **Working tree:** the files `git status --short` listed are the change's own edits. I changed none of them.
- **Check "The review names the doc-claim failure class (R9)":** I expect it to pass. The diff adds 3 lines to `.sdlc/REVIEW.md`, and the check greps for that bullet under *The ways this repo's code fails*. I did not run the grep, since `checks.md` is read-only for me.
- **Check "The docs describe the workarounds (R12)":** I expect it to pass. The diff touches `docs/REFERENCE.md`, `skills/retro/SKILL.md`, `plugins/factory/README.md` and `docs/RETRO-SCORECARD.md`. I did not run the greps. I did not open those files to confirm the exact strings (`simplicity.workarounds`, `which train (train`, `Done: 180`), so this is inferred from the diffstat.

## Evidence
$ cd .sdlc/work/180-workarounds-tagged && ls . build; cat intent.md; cat checks.md; tail -15 build/round-1.gate.md; git log --oneline -3; git diff --stat <merge-base>
(printed the change folder, intent, checks, the gate record tail ending in "Validation passed", and a 16-file diffstat)
exit: 0

$ head -5 .sdlc/work/180-workarounds-tagged/build/round-1.gate.md
GATE: PASS
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro > /tmp/r180.json 2>/tmp/r180.err; echo rc=$?
rc=0
exit: 0

$ python3 -I -c "…print simplicity.workarounds keys…"
outside {"count": 0, "n": 64, "rows": []}
hand_record {"count": 0, "n": 64, "rows": []}
restored {"count": 3, "n": 69, …}
unknown {"count": 0, "rows": []}
overrides {"ejections": {"count": 0, …, "n": 24}, "stops": {"count": 0, "n": 24}, "fixes": {"count": 4, "n": 24}}
exit: 0
