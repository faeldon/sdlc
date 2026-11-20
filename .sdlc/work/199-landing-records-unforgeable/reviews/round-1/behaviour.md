VERDICT: PASS

Every requirement the spec names has a test, and the ones I ran pass. The spec's by-hand path (`factory.py accept` on a scratch host, then tamper with the record and run `land`) was not run end to end. Its three steps are covered by tests that do the same on fixtures: `test_accept_vouches_for_its_record_and_refuses_one_it_didnt_write` and `test_land_refuses_a_hand_written_record`.

## Notes
- **Gate record:** `build/round-1.gate.md` is `GATE: PASS`, `./check.sh`, exit 0, tree unchanged.
- **Tests I ran:** 97 passed. They were `tests/test_records_ledger.py`, `tests/test_hand_gate.py`, `tests/test_modules.py`, and the named tests in `tests/test_land.py` and `tests/test_train.py`.
- **R1:** `test_gate_vouches_for_its_record` and `test_accept_vouches_for_its_record_and_refuses_one_it_didnt_write` cover the factory's writers. `test_the_hand_gate_vouches_for_its_record` covers `sdlc.py gate`.
- **R2:** `test_vouched_reads_the_ledger_alone`, plus `test_a_crlf_record_stays_vouched`, which is marked `portable`.
- **R3:** `test_land_refuses_a_hand_written_record`.
- **R4:** `test_land_verdict_stops_on_a_hand_written_record`.
- **R5:** `test_train_run_stops_on_a_hand_written_record`.
- **R6:** `test_a_hand_written_hand_gate_clears_nothing`.
- **R7:** `test_no_writer_appends_to_an_unvouched_record` and `test_the_hand_gate_refuses_an_unvouched_record`.
- **R8:** `test_the_ledger_writer_is_pinned_to_core`, and the existing pins in `tests/test_modules.py` and `tests/test_hand_gate.py` pass.
- **R9:** `test_two_writers_at_once_leave_whole_lines`.
- **R10:** a grep of the four docs found the ledger, its file name, and the limit sentence ("not one into the git common dir") where the spec wants them.

**checks.md** has one check, "The docs say the script vouches for its records, and the limit". I did not run it. Reading it against the docs, I expect it to pass, since each phrase it looks for is present:
- AGENTS.md line 257 says "records ledger".
- `sdlc-factory-records.jsonl` is in `docs/REFERENCE.md` (line 690) and `plugins/factory/README.md` (line 187).
- "not one into the git common dir" is in `docs/REFERENCE.md` (line 694) and `plugins/factory/README.md` (line 191).
- `plugins/factory/skills/land/SKILL.md` line 234 mentions the ledger and holds "not one into the git".
- The check also wants the word "records" in `plugins/factory/skills/land/SKILL.md`, and I did not confirm it there. The ledger line alone doesn't show it.

## Evidence
$ head -12 .sdlc/work/199-landing-records-unforgeable/build/round-1.gate.md
GATE: PASS … Verdict: PASS, Command: ./check.sh, Exit: 0, Tree: unchanged
exit: 0

$ git status --short
 M AGENTS.md, docs/REFERENCE.md, plugins/factory/README.md, factory.py, landing.py, land/SKILL.md, scripts/factory_records.py, scripts/sdlc.py, tests/test_hand_gate.py, test_land.py, test_train.py; ?? tests/test_records_ledger.py
exit: 0

$ grep -n "records ledger\|records-ledger\|sdlc-factory-records" AGENTS.md docs/REFERENCE.md plugins/factory/README.md plugins/factory/skills/land/SKILL.md
AGENTS.md:257, plugins/factory/README.md:187,345, docs/REFERENCE.md:690, land/SKILL.md:234
exit: 0

$ grep -n "git common dir\|into the git" plugins/factory/skills/land/SKILL.md plugins/factory/README.md docs/REFERENCE.md | grep -i "not one\|not a write"
land/SKILL.md:234, README.md:191, REFERENCE.md:694 (each "not one into the git common dir")
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_records_ledger.py tests/test_hand_gate.py tests/test_modules.py "tests/test_land.py::test_land_refuses_a_hand_written_record" "tests/test_land.py::test_land_verdict_stops_on_a_hand_written_record" "tests/test_land.py::test_accept_vouches_for_its_record_and_refuses_one_it_didnt_write" "tests/test_train.py::test_train_run_stops_on_a_hand_written_record"
97 passed in 22.63s
exit: 0

$ grep -n "^def test.*\(hand_written\|unvouched\|forged\|vouch\|crlf\|ledger\|concurrent\)" tests/*.py
(lists the tests named above)
exit: 0

$ grep -n "^def test\|Thread\|portable" tests/test_records_ledger.py
(lists test_gate_vouches_for_its_record … test_the_ledger_writer_is_pinned_to_core, two marked portable)
exit: 0
