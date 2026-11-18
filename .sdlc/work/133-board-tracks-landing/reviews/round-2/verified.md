- KEPT: ui: C1: scripts/board.py:731: a stopped landing at `shipped` says `/sdlc:ship … by hand`, but the change is already committed and the way on by hand is `/sdlc:close`
- KEPT: ux: C2: plugins/factory/scripts/factory.py:4496: both moved paths still call `_record_land(..., "rebase")`, so the card shows a running rebase after `moved`, and `tests/test_land.py:2138` pins `rebase`
- KEPT: ux: C3: scripts/board.py:730: a stopped landing at `shipped` names `/sdlc:ship`, which `sdlc.py ship` refuses at sdlc.py:3710; it should name `/sdlc:close` at `shipped` and `/sdlc:ship` only at `test`
- KEPT: ux: C4: plugins/factory/scripts/factory.py:4449: the `_amend_record` and `auto` stop reasons reach the card as raw text, and the `_land_refused` calls at 4362, 4483, 4486, 4493, 4498, 4506 and 4509 pass no `plain` line

## Notes
I read `board.py`'s `next` logic and `factory.py`'s `cmd_land_close`, `_amend_record` and `_land_refused`, and checked `test_land.py:2138` and `sdlc.py:3710`. I ran no tests and no `checks.md` commands.

- C1 and C3 describe the same `board.py` defect. I kept both because each is a real finding. The fix is a single edit, and the next-step wording for a stopped landing at `shipped` should be settled once.
- C2 matches the round-1 kept finding listed under Settled. The code still writes `rebase` at both moved paths, so it is unfixed and not a repeat.
