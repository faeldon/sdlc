DECISION: ESCALATE

**Why.** All four round-1 reviewers (code, security, test, behaviour) returned `VERDICT: PASS`. The gate is green (`./check.sh`, 2989 passed, 28 skipped), and the test reviewer matched every requirement R1–R16 to code and a test. Two of the builder's defaults are still the person's call: D1 departs from R10's wording about what goes in the `Sdlc-Lead` line, and D3 picks the word written into the `Sdlc-Coverage` trailer. Both shape a published trailer, which I may not settle. The change also extends the contract every host gets (a new `opened:` frontmatter line, a new `Sdlc-Lead` trailer, `process.lead` in retro's JSON, new keys on the factory's run rows) through `closing.py`, which is a `[review] sensitive` file.

**Open items.** No CHANGE is open. Round 1's four nits are in `findings.md` as F1–F4, each `Disposition: recorded`:
- F1 (code): `opened` after the close is reported as `lead=bad-opened` (`scripts/closing.py:474`). This is D3.
- F2 (code): a factory change with no timed rows and no transcripts drops `ready_wait` (`scripts/closing.py:431`). This is D1.
- F3 (security): the broad `except Exception` turns a programming error into `lead=failed` and prints nothing to stderr.
- F4 (test): no close-level test covers `opened` after `closed` giving `lead=bad-opened`.

**Decisions to confirm.** No blocking line is unticked. R1 was decided by the person.
- ESCALATED: D1: R10 says the no-transcripts case records `lead`, `ready_wait` and `landing`, but the build records only `lead` and `landing` for a factory change. `plan.md`'s "Built differently" section explains this, and R5 ("a part that can't be known is left out, never 0") supports it. Still, it decides what the published `Sdlc-Lead` trailer holds, against the spec's own words, and the behaviour reviewer called it "the one to look at". Either confirm leaving the part out, or ask for the tip's author date as `ready`.
- SETTLED: D2: The spec's Design and R16 say lead time starts at `new`, so time before `opened` is outside lead time by definition. Clipping the first mark to `opened` is pure arithmetic inside `metrics.lead_time()`. It keeps the parts summing to `lead`, as R4 requires, and `test_agents_before_opened_are_clipped_to_it` pins it. It doesn't change the trailer's shape.
- ESCALATED: D3: This chooses which word goes into `Sdlc-Coverage`, part of the metrics trailer contract, which is a published interface. The choice is between reusing `lead=bad-opened` (`closing.py:474–475`) and adding a word such as `lead=clock`. Only the person can extend or reuse that vocabulary. F4 also notes this path has no close-level test of its own.

**Other reasons I escalate.**
- ESCALATED: look: This extends the host-facing contract. It adds `opened:` to every new `intent.md`, adds an `Sdlc-Lead` trailer and new `lead=` coverage words to the metrics format, adds `process.lead` to retro's JSON, and adds `started`/`ended`/`since` keys to the factory's run rows. The edits sit in `scripts/closing.py`, which is `[review] sensitive`. The person should confirm the extension as documented in `docs/REFERENCE.md` *Metrics* and *Retrospectives*.

**For the person at ship.** Look first at `scripts/closing.py`:
- `_lead_line()` (lines 459–478) and `_lead_marks()`, especially the precedence between the factory and hand-built cases (around line 431, D1). Check that every failure stays inside its own `try`, so close still lands.
- `measure_change()`'s `finish()`: confirm the new line is appended after the existing trailers and none of them changed.

Then read `metrics.lead_time()`/`lead_trailer()` and the contract added to its docstring, `_with_opened()` in `sdlc.py`'s `cmd_new`, and the doc edits in `docs/REFERENCE.md` and `docs/RETRO-SCORECARD.md`.

- IMPACT: minor — every host newly records lead time and its breakdown on each `Close` commit, and retro reports it. The `opened:` line, the trailer and the new run-row keys are all additive, and every existing figure is unchanged.

**Each undone item's disposition.** The change folder has no `notes.md`, so there is nothing to carry or drop.

**How to recover.** The prompt names no irreversible paths in the diff. R3 keeps `templates/` and `defaults/` untouched, so `plan.md`'s Rollback (`git revert`; the lines already written stay and nothing reads them) covers it.
