A hand gate now shares the factory's gate slots, and the gate (`./check.sh`) is green: 2254 passed, 13 skipped. Everything is left uncommitted on branch `113-hand-gate-slots`.

## What changed

**Slice 1: the copies and `gate_jobs`.** `scripts/sdlc.py` has copies of the factory's `SLOT_NAME`, `SLOT_POLL`, `FACTORY_CONFIG` and `GATE_JOBS_DEFAULT`. It also has its own `SLOT_WAIT` (30 minutes) and a new `_gate_jobs_at()`. That function reads `gate_jobs` from the base branch, never the checkout, and any value the factory would refuse gives 1.

**Slice 2: the slot in `cmd_gate()`.** When `factory_enabled(home)` is true, the hand gate takes a slot through `_try_lock()` and a new `_hand_slot()`, a copy of the factory's `gate_slot()` with a time limit added. The build hash and the timed run now happen inside the slot. The JSON summary gains `waited` and `slot`, and the record's shape is unchanged. With the factory off it takes no slot, as before. I reused sdlc.py's existing `_unlock()`, which already does the same as the factory's, rather than adding a second copy.

**Slice 3: giving up.** If no slot frees within `SLOT_WAIT`, the hand gate refuses with "no gate slot came free in 30 minutes (1 of 1 in use): nothing was judged, run it again" and exits 1. `build/gate.md` is left as it was.

**Slice 4: the other direction.** R2 shows a factory gate waits for a slot the hand gate holds; R7 shows a killed hand gate frees its slot.

**Slice 5: docs.** Updated REFERENCE.md's *The gate, run by hand*, the factory README's *One gate at a time* and *Mechanism*, and `factory.py`'s docstring and slot comment. AGENTS.md's factory paragraph now names `gate_jobs` and the slot lock files that sdlc reads for the hand gate, which you approved in the intent's open questions.

## Tests added

| Requirement | Test | What it proves |
|---|---|---|
| R1, R3, R6 | `test_a_hand_gate_waits_for_a_factory_gates_slot[1,2]` | With one slot held by a factory gate, the hand gate prints the waiting line once, starts only after release, and keeps the wait out of its run time (`seconds < waited`). With two slots it runs at once on slot 1. |
| R2 | `test_a_factory_gate_waits_for_a_hand_gates_slot` (`tests/test_factory.py`) | A factory gate waits for a slot the hand gate holds. |
| R3 | `test_the_hand_gate_reads_gate_jobs_as_the_factory_does` | Nine base-branch values, with `8` in the checkout, all match `factory._gate_jobs()`. |
| R4 | `test_a_hand_gate_gives_up_after_its_wait_and_records_nothing` | The refusal is given, the exit is 1, and the record is unchanged byte for byte. |
| R5 | `test_without_the_factory_the_hand_gate_takes_no_slot` | No wait, no waiting line, no new lock file. |
| R7 | `test_a_killed_hand_gate_frees_its_slot` (portable) | Killing the hand gate frees its slot for the factory within 2 s. |
| R8 | `test_the_slot_copies_are_the_factorys` (portable) | The copies match the factory's values. |
| R9 | `test_new_claims_a_number_while_a_hand_gate_waits` | A waiting hand gate doesn't block `_main_lock`. |

An autouse fixture in `test_hand_gate.py` turns the factory off by default, so a developer's own settings can't decide a result.

To check the tests catch drift, I temporarily renamed sdlc's `SLOT_NAME`: R1 (both cases), R2, R7 and R8 all failed, and I restored it.

The first full gate run failed once: R2 recorded only 0.3 s of waiting because starting the factory process ate most of the child's one-second hold. R2 now releases the slot only after the factory gate prints its waiting line, so its result no longer depends on timing. R1 now holds for 2 s and compares against `waited`. Three more runs of the slot tests under `-n auto` passed.

## plan.md

Written before the code. One change since: it now says `_wait_text()` was added and `_unlock()` was reused rather than copied.

## notes.md

Nothing left; none was written.

No decisions raised.

## Evidence

```
$ ./check.sh > /tmp/113-check.log 2>&1   (first run, before the R2 fix)
FAILED tests/test_factory.py::test_a_factory_gate_waits_for_a_hand_gates_slot
E       assert (0.3 >= 0.5)
1 failed, 2253 passed, 13 skipped in 100.64s (0:01:40)
exit: 1

$ ./check.sh > /tmp/113-check.log 2>&1
All checks passed!
249 files already formatted
2254 passed, 13 skipped in 67.97s (0:01:07)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable -k slot
3 passed, 2264 deselected in 21.53s
exit: 0

$ for i in 1 2 3; do uv run --group dev pytest -q -n auto tests/test_hand_gate.py tests/test_factory.py -k "slot or gate_jobs or waits or gives_up or one_after" | tail -1; done
16 passed in 3.54s
16 passed in 3.44s
16 passed in 4.06s
exit: 0

$ (SLOT_NAME temporarily renamed in scripts/sdlc.py) uv run --group dev pytest -q tests/test_factory.py tests/test_hand_gate.py -k "hands_gates_slot or hand_gates_slot or factory_gates_slot or killed_hand or copies_are"
FAILED tests/test_factory.py::test_a_factory_gate_waits_for_a_hand_gates_slot
FAILED tests/test_hand_gate.py::test_a_hand_gate_waits_for_a_factory_gates_slot[1]
FAILED tests/test_hand_gate.py::test_a_hand_gate_waits_for_a_factory_gates_slot[2]
FAILED tests/test_hand_gate.py::test_the_slot_copies_are_the_factorys - Asser...
FAILED tests/test_hand_gate.py::test_a_killed_hand_gate_frees_its_slot - File...
5 failed, 1 passed, 240 deselected in 4.09s
exit: 1
```
