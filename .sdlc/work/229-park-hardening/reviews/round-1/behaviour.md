VERDICT: PASS

## Notes
- Checks in `checks.md`:
  - "AGENTS.md's Skills list names update": I expect it to pass. The grep matches the line in AGENTS.md; I ran the same pattern as a read-only `grep` and it exited 0, but I did not run the check itself.
  - "The factory README says 75 is the exit to use": I expect it to pass. Line 483 of the README holds `75 (EX_TEMPFAIL) is the one to use`.
- Gate: `build/round-1.gate.md` records `GATE: PASS`. I did not rerun it.
- End-to-end, the park-related tests (`test_factory_park.py` and `test_hand_gate.py`) pass, 81 tests. A direct `busy_of` call with ESC, C1 and BEL characters in the busy lines returns lines with the control characters dropped. The `[31m` left in the resource is plain text, not control characters, since the ESC itself was removed.
- `_park()` now refuses a `[park] exit` of 0 or 1, and its warning names 75. `park --clear` removes an unvouched record whatever its deadline. `status` and the board now cut a park's deadline to the base branch's `[park] deadline`.
- The two defaults in `decisions.md` (D1: refuse `exit` 0 and 1; D2: clear an unvouched record whatever its deadline) match what the intent's Approach says. They are unanswered, not blocking.

## Evidence
$ git diff --stat $(git merge-base HEAD main) | tail -8
 scripts/board.py                   |  6 ++++--
 scripts/factory_records.py         | 32 +++++++++++++++++++++++------
 scripts/sdlc.py                    | 26 +++++++++++++++++++++++-
 tests/test_board.py                | 27 +++++++++++++++++++++----
 tests/test_factory_park.py         | 41 +++++++++++++++++++++++++++++++++++++-
 tests/test_hand_gate.py            | 17 ++++++++++++++++
 tests/test_modules.py              | 20 ++++++++++++++++++-
 11 files changed, 181 insertions(+), 31 deletions(-)
exit: 0
$ grep -q 'Skills that write (`intent`, `spec`, `ship`, `close`, `drop`, `update`,' AGENTS.md; echo agents=$?
agents=0
exit: 0
$ grep -n '75 (EX_TEMPFAIL)' plugins/factory/README.md
483:                                          # parks; 75 (EX_TEMPFAIL) is the one to use; 2-255,
exit: 0
$ uv run --group dev pytest tests/test_factory_park.py tests/test_hand_gate.py -q -n 4 2>&1 | tail -4
81 passed in 22.81s
exit: 0
$ python3 -I - (calls busy_of(75, "SDLC-BUSY-RESOURCE: db<ESC>[31m<C1>x\nSDLC-BUSY-HOLDER: a<BEL>b", {"park":{"exit":75}}))
{'resource': 'db[31mx', 'holder': 'ab', 'until': None}
exit: 0
$ cat .sdlc/work/229-park-hardening/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0
