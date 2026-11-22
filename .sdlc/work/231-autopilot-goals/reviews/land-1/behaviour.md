VERDICT: PASS

The end-to-end path does what the spec says. R5 and R2 hold at the CLI, and the 630 named tests pass on the rebased tree.

## Notes
- There is no `checks.md` in the change folder, so there are no acceptance checks to read.
- **Gate record:** `build/round-1.gate.md` is `GATE: PASS` (exit 0, `Build: aaef47f11717abbf`, 4044 passed). It covers the pre-rebase build. I did not re-run the gate.
- **Landing-resolved tests:** `build/land-1.md` changed two 228 tests so they work with 231's rules, and resolved the one conflict in `tests/test_autopilot.py`. Both tests are in the 630 that passed.
- **`--preview` with no goal:** it proposed `theme:factory` with the alternative `theme:board`, because no open milestone in the direction doc has a ready candidate. This follows R4, which falls back to a theme when no milestone qualifies.
- **Question wording:** the question begins `Run autopilot toward theme:factory "the factory theme" (register) until …`, as R5 requires.
- **`shown`:** it opens with the `Goal:` block and lists the alternative.
- **`--goal M999`:** it refuses with "M999 isn't an open goal or milestone in the direction doc" and exits 1, as the spec's by-hand check says.
- **Writes:** the `git status` I ran came after the preview commands and shows nothing outside this change's own `runs/` and `reviews/` folders.

One small point, not a failure: the alternative line reads "1 candidates". I did not raise it as a CHANGE.

## Evidence
$ uv run --quiet --script plugins/factory/scripts/factory.py autopilot --preview --usd 1 --hours 1 | head -c 2500
{ "goal": {"source": "register", "arg": "theme:factory", "title": "the factory theme", "count": 1}, "alternatives": [{"arg": "theme:board", ...}], ... "question": "Run autopilot toward theme:factory \"the factory theme\" (register) until $1.0 or 1.0 hours are spent, ... (yes / no)", "shown": "Goal:\n- theme:factory ... suggested from the register: 1 candidate within the bounds\n- or theme:board ... (register, 1 candidates)\n- another goal ...", "warnings": [] }
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py autopilot --preview --usd 1 --hours 1 --goal M999 > /tmp/m999.out 2>&1; head -c 400 /tmp/m999.out
{
  "refusals": [
    "M999 isn't an open goal or milestone in the direction doc"
  ],
  "warnings": []
}
exit: 1

$ git status --short | head
 M .sdlc/work/231-autopilot-goals/runs/costs.jsonl
 M .sdlc/work/231-autopilot-goals/runs/land-step.md
 M .sdlc/work/231-autopilot-goals/runs/land-times.jsonl
 M .sdlc/work/231-autopilot-goals/runs/reviewer-*.sessions
?? .sdlc/work/231-autopilot-goals/reviews/land-1/
exit: 0

$ uv run --quiet --group dev pytest -q tests/test_autopilot.py tests/test_skills.py tests/test_modules.py tests/test_feature_map.py -n auto | tail -4
630 passed in 32.90s
exit: 0

$ cat .sdlc/work/231-autopilot-goals/build/round-1.gate.md | tail -15
(plugin validation: ✔ Validation passed; ICON_MISSING warning only)
exit: 0

$ grep -n "exit\|passed\|failed" .sdlc/work/231-autopilot-goals/build/round-1.gate.md
62:    4044 passed, 29 skipped in 289.73s (0:04:49)
80:    ✔ Validation passed
94:    ✔ Validation passed
exit: 0

$ cat .sdlc/work/231-autopilot-goals/build/land-1.md | head -60; sed -n 1,166p .sdlc/work/231-autopilot-goals/spec.md; git diff 17d57f4fdc1dfdab696c5b683f4f85a83d1b99d9...HEAD --stat | tail -20
(read: land-1.md summary, spec.md requirements R1–R13, 39 files changed, 2225 insertions, 155 deletions)
exit: 0
