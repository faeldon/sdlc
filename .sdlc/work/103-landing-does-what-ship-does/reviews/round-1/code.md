VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:2500 (`accept_build`) and 2689 (`cmd_land`): a rerun after `ship` refuses is refused for a change that has acceptance checks and a carried seed.
  - `accept_build()` digests every changed path outside the change folder before the commit. `_dispose()` appends to the register (`.sdlc/work/inbox.md`), and the register is outside the change's own folder, so `_changed_paths` includes it.
  - On the rerun the digest no longer matches the `Build:` recorded by `factory.py accept`. `_accept_state` returns None, and `land` refuses with "its acceptance checks haven't passed on the change as it stands". A person would have to rerun `accept` after the writes.
  - This breaks R8's "a rerun writes no second seed and no second tick", and the recovery path R13 relies on.
  - `test_a_landing_carries_drops_and_confirms_once` has no `checks.md`, so it doesn't catch this.
  - Fix: leave the register out of the digest. Pass the register's repo-relative path from `config`'s `work.register`, or skip it in `accept_build`. Then add a test where a change with `checks.md`, a seed and a `ship` refusal lands on a rerun without running `accept` again.

## Notes

- **Verified:**
  - I ran `pytest tests/test_land.py tests/test_factory.py tests/test_skills.py -n auto`: 519 passed. I did not run the full `./check.sh`.
  - I read the full `factory.py` diff and the R8 test.
  - I did not read the `SKILL.md`, README or `approver.md` diffs closely.
- **Unsure:** I haven't run the rerun scenario. The mechanism follows from `_changed_paths` including untracked and modified files outside the change folder, so a quick test would confirm it.
- **Done well:**
  - Every refusal comes before the first write in `cmd_land`.
  - `land_question` words the text only from what the batch holds.
  - The approver's missing `UNDONE` line falls back to a seed instead of a drop.
  - `Sdlc-Landed: by=person` stays enforced in the script, not only the skill.
- **Optional:** `unrecovered()` accepts a glob or comma-separated subjects. That is lenient, and a test with an irreversible path covered only by a different directory would pin it.
- **Nit:** the `cmd_resolve` docstring wraps awkwardly after the edit. D1 (keep the counter-only conflict fix here) is a default I'd accept.
