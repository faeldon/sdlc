VERDICT: PASS

The change does what the spec says on the path I ran, and the gate record for this round is green. Three of the builder's own default decisions (D1–D3) are still unanswered; they are not blockers.

## Notes
- **End-to-end path:**
  - `sdlc.py new` in a scratch repo wrote `opened: 2026-11-18T22:25Z` on the line after `created:`. `id: 001` is intact and nothing else in the frontmatter moved (R1).
  - `metrics.lead_time()` and `lead_trailer()` on fixtures gave the expected output. With two overlapping agent intervals (10–40 and 30–50), `agents` counted 40 minutes, not 50. The parts sum to `lead`. The trailer read `Sdlc-Lead: lead=100 queued=10 agents=40 idle=10 ready_wait=30 landing=10 source=runs` (R4, R6).
  - With no `first` and no `landing`, only `lead` and `ready_wait` came back. `queued`, `agents` and `idle` were absent, not 0 (R5).
- **Gate:** `build/round-1.gate.md` reads `GATE: PASS`, `./check.sh`, exit 0.
- **Named tests I ran:** `tests/test_adoption.py` (11 passed), which runs a change from `new` to `close`. The `lead`-keyword tests in `test_metrics.py` and `test_retro.py` (12 passed).
- **checks.md:** the change has none, so there is nothing to read or run.
- **Open defaults:**
  - **D1:** a factory change with no timed rows and no factory sessions records `lead` and `landing` only, with no `ready_wait`. This reads as a departure from R10's wording ("`lead`, `ready_wait` and `landing`"). It agrees with R5's rule that an unknown part is left out. I'd keep it unless you say otherwise.
  - **D2:** a first agent run or edit that comes before `opened` is clipped to `opened`, and the split is kept.
  - **D3:** an `opened` after the close gives `lead=bad-opened` in the coverage line.
  - All three were left open by the builder and fit the spec; D1 is the one to look at.
- **Not run:** I did not run the full suite or `factory.py check`, which the gate record covers. I also did not run the retro-over-history figures, because the person dropped the 139–157 recompute.

## Evidence
$ cat .sdlc/work/162-lead-time/build/round-1.gate.md | head -15
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
Seconds: 118.4
Tree: unchanged
exit: 0

$ uv run --group dev pytest -q tests/test_adoption.py
11 passed in 20.38s
exit: 0

$ uv run --group dev pytest -q tests/test_metrics.py tests/test_retro.py -k "lead"
12 passed, 321 deselected in 0.04s
exit: 0

$ uv run --quiet --script scripts/sdlc.py new "try lead"   (scratch git repo)
created .sdlc/work/001-try-lead/intent.md  (plugin template)
■ 001-try-lead — tier 1, stage: plan
exit: 0

$ head -12 .sdlc/work/001-try-lead/intent.md   (scratch repo)
created: 2026-11-19
opened: 2026-11-18T22:25Z
updated: 2026-11-19
exit: 0

$ python3 -I -c "<lead_time and lead_trailer on fixtures>"
{'lead': 6000.0, 'queued': 600.0, 'agents': 2400.0, 'idle': 600.0, 'ready_wait': 1800.0, 'landing': 600.0}
Sdlc-Lead: lead=100 queued=10 agents=40 idle=10 ready_wait=30 landing=10 source=runs
{'lead': 6000.0, 'ready_wait': 2400.0}
exit: 0
