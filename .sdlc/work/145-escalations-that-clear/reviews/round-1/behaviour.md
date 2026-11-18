VERDICT: PASS

I found nothing in the change that fails its spec. I ran the board and hand-gate tests for escalation, column, train, answered and gate. I did not build a scratch repo and run `factory.py ask` or `sdlc.py gate` by hand, so the checks below rest on those tests.

## Notes
- `checks.md` does not exist for this change, so there were no acceptance checks to read.
- **Gate record:** `build/round-1.gate.md` shows the gate green, and I did not rerun it.
- **End-to-end path:** the spec names no command a person would run, so I ran the closest tests. Passing: a red-gate escalation going to Ready after a green hand gate (R8, R9), the look acknowledgement clearing (R4–R6), and the column placement and train cards (R15–R23). That is 115 passed and 8 skipped.
- **Not exercised:** the paid case run and the `/sdlc-factory:decide` dialog, since neither can run in a read-only session. Nothing here verifies R12's skill text.
- **Builder's ledger defaults:** D1 (one `Escalated` line per `gate` reason, in R13's exact words) and D2 (`wait` only for changes already committed) are the builder's own and still open. Both match the spec, so I raised neither.

## Evidence
$ cd .sdlc/work/145-escalations-that-clear && ls . build reviews; cat intent.md; cat build/round-1.gate.md | tail -15
(listing showed `build/round-1.gate.md` and `build/round-1.md`; no `checks.md`; `reviews` was absent, so ls exited 1; the gate record ended in "✔ Validation passed")
exit: 0

$ cat spec.md; cat decisions.md; git diff --stat $(git merge-base HEAD main); head -40 build/round-1.md
(spec R1–R27 read; 17 files changed, 1508 insertions, 228 deletions)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_hand_gate.py -k "escalat or column or train or answered or gate"
115 passed, 8 skipped in 5.64s
exit: 0

$ grep -n "def test.*\(cleared\|answered\|acknowledge\)" tests/*.py | head
(listed `test_an_answered_escalation_is_ready_to_ship`, `test_a_look_is_acknowledged_and_clears`, `test_land_check_shows_how_each_reason_was_cleared` and others)
exit: 0
