DECISION: READY

**Why.** Both outcomes in the intent are built, and the reviewers confirmed it. The retrospective's drift check (`tests.drifted`) now counts only the code a test loads and never flags data files, with tests for each case. The eight slow tests were merged, cut back or removed. In the builder's back-to-back timing they now take 36% of the old wall time, below the half the intent asked for. Mutations show each ejection cause the removed test checked still fails a remaining test. Round 1 is `VERDICT: PASS` from both reviewers, the gate (`./check.sh`) is green on the build as it stands, and the two findings left are nits already in `findings.md`.

**Open items.** None. Two nits are recorded and need no change:
- `scripts/indicators.py:478`: the `_names()` docstring wraps mid-sentence (code reviewer, F1).
- `notes.md:8`: the paragraph says "one is left" before listing several kept tests (code reviewer, F2).

**Decisions to confirm.** None. `decisions.md` has no lines, so there are no blocking decisions and no open defaults.

**For the person at ship**
- **Look first at `tests/test_train.py`.** Check that each merged test still makes every assertion the tests it absorbed made:
  - `test_train_run_stops_at_a_kept_change_and_resumes`
  - `test_a_killed_train_run_resumes`
  - `test_a_move_mid_train_re_stacks_the_rest_and_counts_once`, which now runs under `[land] moves = 1`
- **Then the removal of `test_every_ejection_names_its_cause`.** The mutation output in `build/round-1.md` backs it.
- **The behaviour reviewer did not re-time the tests.** It called the "under half" claim unchecked. The only timing evidence is the builder's report: 356.8 s before, 126.8 s after.
- **`scripts/indicators.py` (`loads()`, `_names()`, `DATA_SUFFIXES`) and the `git show` reader in `scripts/retro.py`.** These go beyond the intent's *Affected* list, but `plan.md` explains why. The reader only reads, so `retro` still writes nothing but its report.
- **Published interfaces.** The change touches none beyond the documented meaning of `tests.drifted`. The intent's *Affected* names `docs/REFERENCE.md` (*Retrospectives*), and that section is updated to match.

- IMPACT: patch — a host's retrospective names fewer false drifted tests: exact goldens are never named, and code a test doesn't load no longer counts. Nobody has to do anything differently.

**What happens to each unfinished item**
- UNDONE: The train's reading runs about 1,500 git calls for a driven train of three (723
  `rev-parse`, 418 `show`), which is most of each train test's time and of a real landing's
  bookkeeping. Caching what doesn't change within one reading would speed both. → seed: Cache the train's reading within one pass to cut its ~1,500 git calls
- UNDONE: No test fails when the train's readiness refusal (`_land_readiness()`'s `refusal`, in
  `cmd_train`) is ejected under another cause: mutating its `"refusal"` to `"review"` passed
  every train and landing test. The removed `test_every_ejection_names_its_cause` never reached
  that path either: its stray file is the `failed` path, which `test_train_run_stops_at_a_refusal`
  covers. → seed: Test that the train's readiness refusal is ejected with cause `refusal`
