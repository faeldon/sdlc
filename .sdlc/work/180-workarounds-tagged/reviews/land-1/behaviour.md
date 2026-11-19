VERDICT: PASS

The rebase left the change working. The landing gate (`./check.sh`) is green, and in `retro.py` the code from change 175 (`pipeline`) and the code from 180 (`simplicity.workarounds`) sit side by side and both are wired into the report. The resolver said it hadn't checked that fit, so I ran the retro and archive tests, and they pass.

## Notes
- This change has no end-to-end path beyond what its tests exercise. The closest path is the retro report, where `simplicity.workarounds` appears next to `pipeline`. `tests/test_retro.py` covers it and passes.
- Check "The review names the doc-claim failure class (R9)": I expect it to pass. The bullet "A doc's claim the change made false" is in `.sdlc/REVIEW.md`. I only counted the matching line. I didn't run the check's own awk command.
- Check "The docs describe the workarounds (R12)": I expect it to pass. `simplicity.workarounds` appears once in `docs/REFERENCE.md` and once in `skills/retro/SKILL.md`. `which train (train` appears once in the factory README, and `Done: 180` once in `docs/RETRO-SCORECARD.md`. I counted these myself rather than running the check.
- The worktree has uncommitted changes under `.sdlc/work/180-workarounds-tagged/runs` and `build/`. They are the harness's own records, not part of the diff.

## Evidence
$ cat .sdlc/work/180-workarounds-tagged/build/land-1.gate.md (head and grep)
GATE: PASS … Command: ./check.sh … Exit: 0 … 3295 passed, 29 skipped
exit: 0

$ grep -c "A doc's claim the change made false" .sdlc/REVIEW.md
1
exit: 0

$ grep -c 'simplicity.workarounds' docs/REFERENCE.md skills/retro/SKILL.md; grep -c 'which train (train' plugins/factory/README.md; grep -c 'Done: 180' docs/RETRO-SCORECARD.md
docs/REFERENCE.md:1
skills/retro/SKILL.md:1
1
1
exit: 0

$ grep -n "pipeline\|simplicity" scripts/retro.py | head -20
1085:def _pipeline(…) … 2755: "pipeline": _pipeline(…) … 2765: "simplicity": {"workarounds": workarounds},
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_archive.py
375 passed in 34.30s
exit: 0
