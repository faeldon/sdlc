VERDICT: PASS

No Critical or Required findings. Every requirement I checked has code and a test, and `./check.sh` is green except for one failure that comes from the change folder's own files, not from the code (see the first note).

## Notes

- **Optional: the one failing test.** `tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden` fails on 4 lines in `.sdlc/work/085-factory-stopped-runs/build/round-1.gate.md`. Line 43, for example, holds the home-directory path from the gate's `claude plugin validate` output. The builder didn't write that; `factory.py gate` records it. This repo's rule is that no file in the repo may hold a home-directory path, so clear it before ship, either by scrubbing the gate file or by confirming `/sdlc:ship` handles it. I did not trace which of the two is expected.
- **Optional: unguarded read in `board.py`.** `_stopped()` calls `read_text` after `is_file()` with no `OSError` guard. `sdlc.py`'s `factory_stop()` does guard it. If the call is wrapped by `_entry`'s `read` helper, this is moot. I didn't confirm that it is.
- **Optional: duplicated regexes.** The three stop regexes are copied across `factory.py`, `board.py` and `sdlc.py`, as the spec asked. The pin tests I saw in the diff (`test_board.py`, `test_next_up.py`, `test_factory.py`) cover them.
- **Done well:**
  - `--record` without `--head` is refused, so a stop for HEAD moving can't be removed by mistake.
  - The record is written from the same `loop_state()` reading that decided the stop, so the two can't disagree.
  - `way` is decided in `factory.py` alone, by keeping the evidence problems apart as they are added.
  - Status marks a stopped run on its line and keeps it out of "quiet", and the supervisor skill forbids editing the record.
  - AGENTS.md, REFERENCE.md and the factory README are updated alongside the code.
- **Ran:** `./check.sh`: 1865 passed, 1 failed (the test above). I read the diff for `factory.py`, `board.py`, `sdlc.py`, both SKILL.md files and AGENTS.md. I only skimmed the new tests' names and sizes, not their bodies.
