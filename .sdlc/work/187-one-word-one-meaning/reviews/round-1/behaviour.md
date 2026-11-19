VERDICT: PASS

The end-to-end path does what the spec says. `sdlc.py vet` runs, `check` is gone with no alias, and the three checks I could evaluate hold. I did not run the whole suite or the acceptance checks; I read `checks.md` and the round-1 gate record instead.

## Notes
- **Round-1 gate record:** PASS, `./check.sh`, exit 0.
- **`vet`:** it prints `■ Problems: 0` with exit 0, and `vet --strict` also exits 0 on this clean folder. I did not run a failing case. The spec's `test_vet_strict_fails_on_a_problem` covers that, and the gate was green.
- **`check`:** argparse refuses it with exit 2, and `vet` is listed in its place.
- **Retired-phrasing test:** `test_no_doc_uses_a_retired_phrasing` passes.
- **Board and landing:** the board's tracks use `arbitrate` and `acceptance`. The landing question says "approved as shown" in `landing.py`. I did not run the board itself or check its gate badge.
- **checks.md, "The two test nits are gone":** I expect it to pass. My equivalent grep (`'179 R1'`, `'# 183'`) exited 0.
- **checks.md, "The arbiter's agent and prompts sit under its name":** I expect it to pass. I ran only a partial equivalent. It tested `arbiter.md`, `arbitrate.md`, `land-arbitrate.md` and that `agents/verifier.md` is gone, and exited 0. I did not test that `prompts/verify.md` and `prompts/land-verify.md` are gone.
- **checks.md, "The release says what a host must change":** I expect it to pass. `impact: minor` is set, and the `REFERENCE.md` greps match: the three-phrase pattern gave 3 lines and the `[models] verifier` pattern gave 1.

## Evidence
$ head -12 .sdlc/work/187-one-word-one-meaning/build/round-1.gate.md
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0

$ uv run --quiet --script scripts/sdlc.py vet
■ Problems: 0
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
sdlc.py: error: argument cmd: invalid choice: 'check' (choose from status, new, vet, ...)
exit: 2

$ uv run --quiet --script scripts/sdlc.py vet --strict | tail -3
■ Problems: 0
exit: 0

$ uv run --group dev pytest -q tests/test_feature_map.py -k retired
2 passed, 7 deselected
exit: 0

$ test -f plugins/factory/agents/arbiter.md && test -f plugins/factory/prompts/arbitrate.md && test -f plugins/factory/prompts/land-arbitrate.md && ! test -e plugins/factory/agents/verifier.md
exit: 0

$ ! grep -q '179 R1' tests/test_metrics.py && ! grep -q '# 183' tests/test_skills.py
exit: 0

$ grep -c 'sdlc.py check` is now `sdlc.py vet`\|sdlc.py vet --strict` instead\|setup proposes it on its next run' docs/REFERENCE.md
3
exit: 0

$ grep -c '`\[models\] verifier` is now `\[models\] arbiter`' docs/REFERENCE.md
1
exit: 0

$ grep -n '^impact' .sdlc/work/187-one-word-one-meaning/intent.md
5:impact: minor
exit: 0

$ grep -n "arbitrate\|arbiter:\|acceptance" scripts/board.py | head -8
64:TRACK = ("build", "gate", "review", "arbitrate", "rework", "approve")
… 76: LAND_TRACK = (…, "acceptance", …, "arbitrate", …)
exit: 0

$ grep -n "approved as shown" plugins/factory/scripts/landing.py | head -2
615: … cases approved as shown …
639: parts.append("its failed or skipped skills' cases approved as shown")
exit: 0
