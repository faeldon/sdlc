VERDICT: PASS

The change does what the intent says, and the named tests pass.

## Notes
- **Gate:** `land-2.gate.md` for this round reads `GATE: PASS` with `Exit: 0`. I did not run the suite again.
- **Park hardening:** I read the diff, and each outcome in the intent is in it:
  - `[park] exit` is now accepted only from 2 to 255, and the warning names 75.
  - `busy_of()` drops C0 and C1 control characters.
  - `park --clear` now removes an unvouched record.
  - `status` and the board cut a park's deadline by the base branch's `[park] deadline`, as `verdicts` does.
  - `AGENTS.md` names `update`.
- **Slot-wait assertion:** I did not read the test diff itself. The named park, board, hand-gate and modules tests pass, and the diff touches them.
- **checks.md, "AGENTS.md's Skills list names update":** I expect this to pass. `AGENTS.md` has that line, and a grep I ran that mirrors the check's pattern exited 0.
- **checks.md, "The factory README says 75 is the exit to use":** I expect this to pass. `plugins/factory/README.md:483` has "75 (EX_TEMPFAIL) is the one to use".
- **Not run:** I ran no checks from `checks.md` and no end-to-end park scenario. The intent names no end-to-end command, so I used the park tests as the nearest path.

## Evidence
$ cat .sdlc/work/229-park-hardening/build/land-2.gate.md | head -12
GATE: PASS
## Attempt 1
Verdict: PASS
Command: ./check.sh
Build: 3b5fbbb2dcc193f0
Exit: 0
exit: 0

$ git diff 913d86075a75ac0066f0e29c3f750cb38cc1312c...HEAD -- scripts plugins/factory/scripts AGENTS.md
(diff reviewed; changes as described above)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_park.py tests/test_board.py tests/test_hand_gate.py tests/test_modules.py | tail -5
426 passed, 28 skipped in 38.01s
exit: 0

$ grep -q 'Skills that write (`intent`, `spec`, `ship`, `close`, `drop`, `update`,' AGENTS.md; echo $?
0
exit: 0

$ grep -n '75 (EX_TEMPFAIL)' plugins/factory/README.md; echo $?
483:  # parks; 75 (EX_TEMPFAIL) is the one to use; 2-255,
0
exit: 0
