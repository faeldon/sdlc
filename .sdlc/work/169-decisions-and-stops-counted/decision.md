DECISION: READY

**Why.** In the only round, all three reviewers (code, test, behaviour) returned `VERDICT: PASS`. The test reviewer matched every requirement from R1 to R14 to a test that would fail without it, and R15 is docs that appear in the diff. The gate record shows `./check.sh` green on the build as it stands (3094 passed, 28 skipped, exit 0). Nothing in the reviews suggests the spec was wrong. The diff touches neither `closing.py` nor `landing.py`, and there is no `decisions.md` and no `notes.md`, so no ledger line or undone item is waiting.

**Open items.** None. The three findings are nits, already in `findings.md`:
- F1 (code): a one-line comment saying settled or superseded marks apply only to defaults. Recorded.
- F2 (code): REFERENCE could say "only" `escalations.n` leaves out a decision file it can't read. Marked minor.
- F3 (test): R8's rate test can't tell `kept/(kept+changed)` from `kept/total`, because its ledger gives 1 kept and 1 changed. Recorded.

**Decisions to confirm.** None. The change has no `decisions.md`, no blocking line and no open default.

**For the person at ship:**
- **The new trailer.** Look first at `scripts/metrics.py`: `trailers()` and `parse_trailers()` with the new `Sdlc-AfterGate` line. It adds to the documented `Sdlc-*` trailer contract. The spec you approved covers it, and the test checks that the `Sdlc-Extra` and `Sdlc-Totals` lines are unchanged. Still, it is the one part that reaches every host's history.
- **The new reader.** Next, `factory_records.autonomy_counts()`. Check that it compares answers by exact match, since `KEPT_ANSWER` is a prefix of `CONFIRMED`, and checks the marks in this order: superseded, then settled, then unticked.
- **Status placement.** Then `_by_state()`'s fallback to `column()` in `scripts/sdlc.py`. It is meant to place everything as before; a quick `sdlc.py status` will show whether it does.
- **The live retro run.** The behaviour check's live `sdlc.py retro` ran past its 120s timeout and was stopped, likely on the host's evidence and test-time commands. The builder's own run finished: 13 factory changes, 1 built by hand, tree unchanged. Run it once yourself from the main checkout to confirm `autonomy` appears and `git status` stays clean.

- IMPACT: minor — `retro`'s JSON gains `autonomy`, and each `Close` commit gains an `Sdlc-AfterGate` line that `metrics.extra.after_gate_by` reads back. Both are new things a host can read, and no existing key or trailer changes shape.
