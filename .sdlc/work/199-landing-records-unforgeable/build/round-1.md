I've built change 199, and the full suite passes on a fresh run (3556 passed, 29 skipped, lint and plugin validation clean). A gate, build or accept record the script didn't write is now refused wherever a landing reads it. Everything is uncommitted, and `HEAD` is still at `74436ab`.

**Slices built** (I wrote `plan.md` after reading the code):
1. **The ledger** (R1, R2, R9): the factory adds a line to `sdlc-factory-records.jsonl` in the git common dir before it writes each record, and reads a record as a verdict only while the ledger holds a matching line (`vouched()`). Writes take a lock on `sdlc-factory-records.lock`.
2. **Writers refuse a record they didn't write** (R7): `factory.py gate` and `factory.py accept` refuse before running anything or recording a landing step. The refusal names the file and says to remove it.
3. **`land` refuses the change** (R3) if any of the five record kinds in its folder isn't vouched for, before it writes anything.
4. **A landing round stops** (R4): an unvouched `land-<n>.gate.md` or `land-accept.md` is a `stop` in `land_verdict()`, never a pass or a mend.
5. **The train stops** (R5): it never copies an attempt from an unvouched gate or build record into its state, and stops naming the file. Before this fix, a hand-written `land-1.build.md` landed the whole train.
6. **Hand gate** (R6, plus core's half of R1 and R7): a green `build/gate.md` clears the approver's `gate` reasons only if it is vouched for. `sdlc.py gate` adds its own ledger line and refuses to add to a record it didn't write.
7. **Docs** (R10): `AGENTS.md`, `docs/REFERENCE.md`, the factory README and the land `SKILL.md` each say this, and state the limit: it guards against a write in a worktree, not one into the git common dir. `checks.md` holds one acceptance check that greps for those sentences.

**Tests added, by requirement:**
- R1: `test_gate_vouches_for_its_record`, `test_accept_vouches_for_its_record_and_refuses_one_it_didnt_write` (R7 too), `test_the_hand_gate_vouches_for_its_record`
- R2: `test_vouched_reads_the_ledger_alone`, `test_a_crlf_record_stays_vouched` (portable)
- R3: `test_land_refuses_a_hand_written_record[accept|round gate]`
- R4: `test_land_verdict_stops_on_a_hand_written_record[land gate|accept]`
- R5: `test_train_run_stops_on_a_hand_written_record[gate|build]`
- R6: `test_a_hand_written_hand_gate_clears_nothing`
- R7: `test_no_writer_appends_to_an_unvouched_record`, `test_the_hand_gate_refuses_an_unvouched_record`
- R8: `test_the_ledger_writer_is_pinned_to_core`; the existing pins in `test_modules.py` and `test_hand_gate.py` pass unedited
- R9: `test_two_writers_at_once_leave_whole_lines`

Each new test failed for the expected reason before its code existed. That evidence is in the previous round's report and isn't rerun here.

**Where the build departs from the spec** (`plan.md` now says so):
- Core's copies of the ledger's name, hash, line and reader are in `scripts/factory_records.py`, not `sdlc.py`. AGENTS.md says core's copies of factory records live only there. `sdlc.py` keeps only the locked write (`_vouch()`) and `_hand_vouched()`.
- `forged_records()` is in `landing.py`, not `factory.py`, because only the landing calls it. `test_modules`' rule failed when it sat in `factory.py`.
- I added no vouching helper to `tests/conftest.py`. No existing test broke, because the board, `status`, retro and metrics read records through core, which doesn't check the ledger.

**`notes.md`:** nothing to add.

- UNTESTABLE: none
- DECISION: [default] Should `sdlc.py gate`'s refusal (R7) cover changes built by hand, not only factory runs? Going ahead with every change, as the spec says, unless told otherwise.
  - OPTION: every change — one rule; an in-flight hand-built `build/gate.md` needs one `rm` before its next hand gate
  - OPTION: only factory runs — no friction where the record clears nothing the factory reads; the two hand gates then behave differently
  - WHY: R7 as written
- DECISION: [default] Should records left by changes already in flight be refused until removed and run again? Going ahead with the refusal, as the spec draft took it.
  - OPTION: refuse — no exception to the rule; each in-flight record is removed and its gate or checks rerun
  - OPTION: a one-time "vouch what's there" command — no reruns; it vouches files the script didn't write, which is the hole this change closes
  - WHY: the spec's "Left for you" question
- DECISION: [default] Should `build/land-<n>.checks.md` (the approver's `CHECKS: HARMLESS` judgement) stay unprotected here? Going ahead with leaving it out; it could become a seed.
  - OPTION: leave it out — within the intent's scope; a forged judgement can still let a changed `checks.md` run unattended in `train --run`
  - OPTION: add it — closes that hole too; one more writer and one more reader beyond the approved requirements
  - WHY: the intent names only gate, build and accept records

## Evidence

$ uv run --group dev pytest -q -n 8 tests/test_records_ledger.py tests/test_hand_gate.py tests/test_modules.py tests/test_feature_map.py tests/test_land.py::test_accept_vouches_for_its_record_and_refuses_one_it_didnt_write tests/test_land.py::test_land_refuses_a_hand_written_record tests/test_land.py::test_land_verdict_stops_on_a_hand_written_record tests/test_train.py::test_train_run_stops_on_a_hand_written_record
106 passed in 51.51s
exit: 0

$ sh -c "<the sh block of .sdlc/work/199-landing-records-unforgeable/checks.md>"
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 199
All checks passed!
335 files already formatted
3556 passed, 29 skipped in 208.88s (0:03:28)
✔ Validation passed
✔ Validation passed
exit: 0

$ git log --oneline -1
74436ab Close 198-landing-stages-its-own-paths
exit: 0
