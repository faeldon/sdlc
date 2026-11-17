- DROPPED: code: C1: plugins/factory/scripts/factory.py:2500: rerun after ship refuses is refused when checks and a carried seed exist — `accept_build` hashes only `_changed_paths()` plus `checks.md`. `_changed_paths()` leaves out everything under `.sdlc/work/`. That covers the folder, so `_dispose`'s edits to `notes.md` and `decisions.md` don't count. It also covers the register, `.sdlc/work/inbox.md`. The digest therefore doesn't change after `_dispose`, and `_accept_state` still reads PASS on the rerun.

## Notes
- I read `accept_build`, `_accept_state`, `_changed_paths`, `work_rel`, `_tree_hashes`, `cmd_land` and `_dispose`. I also read `test_a_landing_carries_drops_and_confirms_once`. I ran nothing, and no tests.
- The existing rerun test covers a carried seed and a ship refusal, but the change has no acceptance checks, so it doesn't reach this path.
- The claim could still hold if the host's `work.register` points outside `.sdlc/work/`. Then `_dispose` would change the digest after the first attempt. A test with a custom register path and an acceptance check would settle it.
