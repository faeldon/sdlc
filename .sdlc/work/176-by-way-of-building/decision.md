DECISION: READY

**Why.** All 13 requirements have code and a named test that the reviewers checked would fail without the change. The builder saw each test fail before the code went in. The round-1 gate passed on `./check.sh` (3307 passed, 29 skipped), and all three reviewers returned `VERDICT: PASS`. What's left is two nits and one note item. Neither nit questions the spec, and the note asks whether a figure should read better.

**Open items**
- None. Round 1 has no unresolved CHANGE. The two nits from `code` are already in `findings.md`: F1, the long lines in `skills/retro/SKILL.md` (minor), and F2, the `introducer_way()` rescan (recorded).

**Decisions to confirm**
- SETTLED: D1: the approved spec's R5 sets the window's floor at "at least 1/7" week, and the build does exactly that; `test_by_way_gives_every_figure_for_each_way_with_its_n` covers it. The default departs from nothing the person approved. Moving to a one-week floor or a null `per_week` would change R5, so that idea goes forward as a seed (below) rather than being decided inside this change.

**For the person at ship**
- **Start with these two pieces of code:**
  - `scripts/sdlc.py`: `retired_entries()` and the `dropped` branch in `_milestone_verdicts()`. These change what `status` and `direction.milestones` report.
  - `scripts/retro.py`: `bugs_retro()` and the new `introducer_way()`. These give each escape and the window rate a way of building.
- **Small samples:** on this repo today the `manual` side has only 1 change, so its escape rate reads 1.0. That's correct, and the table shows each figure's `n` beside it, but it is easy to over-read.
- **Contracts you already approved:**
  - `direction.milestones` gains a `dropped` verdict for a grouped seed and a new milestone rule. Approved in the spec's *Contracts touched* ("`direction.milestones`' meaning changes … the intent is its approval") and in the intent's *Affected → Contracts*. `status` still calls done every milestone it called done before (R11, `test_status_counts_a_milestone_with_a_retired_seed_done`).
  - `Sdlc-Mode` is only read, never written or redefined. Approved in the spec's *Contracts touched*.
  - `retro`'s JSON gains a top-level `by_way`, `process.lead.ways`, throughput's `ways`/`classes`, `bugs.escapes[].way` and `rate.window.by_way`. All are specified in R2–R7 of the approved spec. No template or placeholder changed, so `TEMPLATE_READS` and `breaking` are untouched.
- **Test edits:** five existing tests in `tests/test_retro.py` and `tests/test_bugs.py` had their assertions extended for the new keys only. The builder's report lists them; a quick look confirms none was weakened.

- IMPACT: minor — a host's retrospective can now compare factory-built and hand-built changes on lead time, throughput, cost and escape rate, and see throughput by work class. A grouped seed retired with `inbox-commit` now reads `dropped` instead of `vanished`. Nothing a host already relied on stops working.

**Undone items**
- UNDONE: `by_way.throughput` floors the window at one day, as R5 says, so a retro run the day after the last retrospective gives `weeks: 0.1` and per-week figures many times the real rate (this repo, today: 196 factory changes a week over 1 day). A floor of one week, or `per_week` null under a week, would read better; it changes R5, so it is the person's call. → seed: Floor by_way throughput at a week, or leave per_week null under a week
