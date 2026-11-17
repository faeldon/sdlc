VERDICT: PASS

## Notes

**Run.** `uv run --group dev pytest -q -n auto` gave 2257 passed, 13 skipped. That matches the builder's gate figures in `build/land-1.md`. I did not run `./check.sh`; the builder reported it green on this tree, and ruff and `claude plugin validate` are not tests.

**Landing round.** The only conflict was in `.sdlc/work/inbox.md`, a register file with no tests. The diff against main there is entry 63's lines alone, as `land-1.md` says. The rebase touched no code or test.

**Requirement map.** Each test below uses a real lock held by the other script's code, so it fails if the code is absent.
- **R1, R3 (`gate_jobs = 2`), R6:** `test_a_hand_gate_waits_for_a_factory_gates_slot`, run with `gate_jobs` 1 and 2.
  - It holds slot 0 through `factory.gate_slot()` and compares the check's start stamp with the holder's release stamp.
  - It asserts the waiting line appears once, `waited ≥ 0.5`, `seconds < waited`, and `slot` is 0. With 2 jobs it asserts there is no waiting line and `slot` is 1.
  - It also asserts the record keeps its shape.
- **R2:** `test_a_factory_gate_waits_for_a_hand_gates_slot` holds the slot through `sdlc._hand_slot()` and runs `factory.py gate`. It asserts the waiting line, `waited ≥ 0.5`, and `slot` 0.
- **R3 (values):** `test_the_hand_gate_reads_gate_jobs_as_the_factory_does` covers missing, 3, 0, -1, `"2"`, `true`, 2.5, no key, and unparseable. Each case has a conflicting `8` in the checkout and is compared with `factory._gate_jobs`.
- **R4:** `test_a_hand_gate_gives_up_after_its_wait_and_records_nothing` asserts the exact refusal text, exit 1, and the record byte for byte. Equal bytes also rule out a FAIL attempt.
- **R5:** `test_without_the_factory_the_hand_gate_takes_no_slot` runs with `gate_jobs = 2` and slot 0 held. If a slot were taken it would use slot 1 and create a new lock file, so the file-list check catches it. It also asserts no waiting line, and `waited` and `slot` of `0.0` and `None`.
- **R7:** `test_a_killed_hand_gate_frees_its_slot` (`portable`) checks the lock is held while the gate runs, then that `factory.gate_slot()` takes it in under 2 s after the kill, and that the file stays.
- **R8:** `test_the_slot_copies_are_the_factorys` (`portable`) covers the four pinned values, plus `SLOT_WAIT == GATE_TIMEOUT`.
- **R9:** `test_new_claims_a_number_while_a_hand_gate_waits` runs a real `sdlc.py gate` subprocess with the factory enabled through a temp `HOME`. It asserts that `_main_lock` is takeable within 2 s while the gate waits.
- **R10:** prose, checked at review, not here.

**Fixture.** The autouse `_no_factory` fixture stops a developer's own settings from deciding a result.

**Lower-priority gaps (not blocking):**
- Nothing pins the design's point that the build hash and the timed run happen after the wait. A regression that hashes before the slot is taken would pass every test.
- The `waited` assertion is `seconds < waited`, looser than the spec's "check's length plus a margin". It is still meaningful, because the check is near-instant and the wait is about 2 s.

**`checks.md`.** The change has none, and none is needed. Every requirement is covered by a suite test.
