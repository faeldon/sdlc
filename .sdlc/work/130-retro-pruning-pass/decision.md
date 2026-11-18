DECISION: ESCALATE

**Why.** The build looks finished. All 12 requirements have code and a named test, round 2 is `VERDICT: PASS` from both reviewers, and the gate passes (2364 passed, 13 skipped, both validations). The only kept finding, the stale *Retrospectives* line in `AGENTS.md`, is fixed. I'm escalating for one reason: the change adds `retro.test_times` to the host-facing contract in `docs/REFERENCE.md`, and that key makes `sdlc.py retro` run a host's commands with a 600 s timeout and a 5,000,000-character limit. Any change to a published interface needs a person to look before landing. This should be a short look, not a sign of trouble.

**Open items**
- None. F1 (`code`) is fixed. F2 and F3 (`code`) and F4 (`test`) are nits marked `minor`, and nothing was carried to `notes.md`.

**Decisions to confirm**
- None. The change has no `decisions.md`, and the builder raised no decisions. The builder did make three small calls where the spec was silent, and `plan.md` records them under *Departures from the spec*:
  - A `time` of 0, a negative one, or one that isn't a number counts as untimed.
  - If listing the base branch's files fails, every test file counts as present.
  - `slow` holds the same rows as `slowest`, and the skill works out the multiple of the median itself.

**For the person at ship**
1. `docs/REFERENCE.md` and `scripts/sdlc.py`: check that the new key, its default `[]`, its JUnit-on-stdout contract and its limits are what you want hosts to rely on.
2. `scripts/retro.py`, in `_evidence()`, `_times()` and `_lookback()`:
   - Only `_times()` passes the larger limits.
   - A cut report counts as `failed`.
   - No raw output survives into the `tests` block.
   - `_architecture()`'s output is unchanged now that `_lookback()` has been taken out of it.
3. `.sdlc/setup.json`: the spec said it wouldn't change, but `record` rewrote it. The builder says the only difference is `retro.test_times` added to the known-key list. Confirm the diff shows only that.
4. `skills/retro/SKILL.md`: the pruning pass should be one seed, and nothing in it should edit or delete a test.

Also note: neither reviewer ran the manual real-fixture check, but the builder's evidence shows it ran. On this repo's own `--junitxml` report it gave `error None`, 2,377 cases and 13 skipped.

- IMPACT: minor — hosts can newly set `[retro] test_times` so the retro proposes a pruning pass from run times and history. It's an optional key with default `[]`, so nobody has to change anything.

There are no undone-item lines because the change has no `notes.md`. There are no recover lines because the prompt names no irreversible paths. If you need a way back anyway, `plan.md`'s Rollback is `git revert` of the change's commit.
