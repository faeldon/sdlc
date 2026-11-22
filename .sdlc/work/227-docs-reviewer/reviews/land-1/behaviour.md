VERDICT: PASS

The change's gate is green and the tests for the new docs reviewer pass. Drift reports nothing to refresh. The spec names no separate end-to-end command, so I ran the closest path: the change's own tests, plus the drift check and a read of ship's `SKILL.md`. I did not run a live factory round or a ship session.

## Notes
- `checks.md` does not exist for this change, so there were no acceptance checks to read.
- The gate record for round 2 (`build/round-2.gate.md`) says `GATE: PASS`, with `Exit: 0` and build `c106e909d3fc5912`. I did not rerun the gate.
- The focused tests cover the factory docs reviewer, ship's preflight passes, finding tags and the feature map: 163 passed.
- `docs.reviewed` appears in `docs/REFERENCE.md` (2 matches).
- `sdlc.py drift` shows `breaking: []` and `refresh: []`, so the record matches what the change ships.
- `skills/ship/SKILL.md` names `docs.md` and the `sdlc:docs` reviewer in Step 3's Context pass, as R10 asks.
- I did not run `./check.sh` or the whole suite, because the gate record already covers it.

## Evidence
$ ls .sdlc/work/227-docs-reviewer/checks.md
ls: .sdlc/work/227-docs-reviewer/checks.md: No such file or directory
exit: 1

$ head -8 .sdlc/work/227-docs-reviewer/build/round-2.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: c106e909d3fc5912
Exit: 0
exit: 0

$ uv run --group dev pytest tests/test_factory_docs.py tests/test_preflight.py tests/test_findings.py tests/test_feature_map.py -q -n auto | tail -5
163 passed in 13.66s
exit: 0

$ grep -c "docs.reviewed" docs/REFERENCE.md
2
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift | head -8
{
  "base": "manifest",
  "version": {
    "manifest": "1.11.0",
    "plugin": "1.11.0"
  },
  "breaking": [],
  "refresh": [],
exit: 0

$ grep -n "docs" skills/ship/SKILL.md | head
107:- **`context`**: the docs the context pass weighs in Step 3.
112:  `security.md`, `behaviour.md`, `ui.md` and `docs.md` as `passes` applies, `cases.md`, `conflict.md`.
198:4. **Context** — whether the docs that give a session its context still tell the truth after this
202:   each listed doc, then ask of it (when `branches` names `docs.md`, its `sdlc:docs` reviewer
exit: 0
