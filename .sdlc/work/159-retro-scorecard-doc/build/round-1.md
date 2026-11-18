I added the scorecard as `docs/RETRO-SCORECARD.md` and listed it in `docs/CONTRIBUTING.md`. I checked every "captured" status in the draft against the code, and six of them claimed more than the code records. I corrected those six in the doc. The full gate passes and nothing is committed.

**What was built (Tier 1, two files, so no `plan.md`):**
- `docs/RETRO-SCORECARD.md` is `draft.md` with its structure and wording kept, except for the six corrected statuses.
- `docs/CONTRIBUTING.md` has one new Layout row for the doc.

**The six statuses that overstated** (each also explained in `notes.md`):
- **Throughput:** the retro counts it per week by tier, not by impact. Now "partly"; by impact needs S2.
- **Test health:** the retro never reads the skills' cases' scores; only ship and release do. Now "partly".
- **Cost per landed change:** dollars exist per factory change in `runs/costs.jsonl` and are shown by `factory.py ready`, but the retro adds up no dollars across changes. Now "partly, needs S4".
- **Spend by role and model:** the retro's `spend.agents` groups runs by role and model, but counts how the agents worked, not what they cost. Now "partly, needs S4".
- **Cost per unit of output:** `spend.out_per_line` is output tokens per added code line, not dollars per 100 lines. Now "partly"; dollars need S4.
- **Context per run:** only an estimate exists (`prose`, bytes / 4); no trailer measures what a skill run read. Now "captured as an estimate".

The rest of the draft's "captured" claims held.

**Tests:** this change adds code to no test file. Its two outcomes could only fail if someone deleted the doc or the row, so they are acceptance checks in `checks.md`:
- "The scorecard doc holds the framework": the file exists with its title, the Value band, all five pillars, the Trust band, Insights, the seeds section, S16 and R6.
- "CONTRIBUTING's layout lists the doc": the Layout row is there.

Both checks failed before the doc existed and pass now. `tests/test_nothing_local.py` passes, and it scans untracked files too, so it covered the new doc.

**`notes.md`:** the corrections above, and nothing left undone. `draft.md` stays in the folder as the approved source.

No decisions raised.

## Evidence

$ uv run --quiet --script scripts/sdlc.py accept 159   (before the doc and the row existed)
"name": "The scorecard doc holds the framework", "exit": 1, "passed": false
"name": "CONTRIBUTING's layout lists the doc", "exit": 1, "passed": false
"passed": false
exit: 1

$ uv run --quiet --script scripts/sdlc.py accept 159
"name": "The scorecard doc holds the framework", "passed": true
"name": "CONTRIBUTING's layout lists the doc", "passed": true
"passed": true
exit: 0

$ uv run --group dev pytest -q tests/test_nothing_local.py
8 passed in 0.53s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 159
✔ Validation passed   (plugin directory warning only: ICON_MISSING, which doesn't change the result)
✔ Validation passed
exit: 0
