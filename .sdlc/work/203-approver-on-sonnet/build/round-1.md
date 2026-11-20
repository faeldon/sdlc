I set the approver to Sonnet in this repo's `.sdlc/factory.toml`. The acceptance check passes, but `factory.py config` and `start` won't show Sonnet until the change lands on main.

That's by design: the factory reads `[models]` only from the base branch's copy of the file, so a change can't pick its own agents' models. Run from this worktree, `config` still shows `"models": {}`, which means the approver stays on Opus. So the intent's step "run `factory.py config` and check `models_at`" can only pass after the change has landed. I checked this checkout's file through the factory's own code instead (below). Run `factory.py config` once more after landing to confirm it in place.

**What changed** (Tier 1, one file, so no `plan.md`):
- **New `[models]` table:** `approver = "sonnet"`, which covers both depths. Its comment says this is a one-window trial from the retrospective of 2026-11-20, and what the next retrospective judges it by: READY changes that escaped, and ESCALATEs the person found empty.
- **File header:** reworded to say `[models]` now differs from the defaults too.
- **Plugin defaults:** untouched.

**Acceptance check:** `.sdlc/work/203-approver-on-sonnet/checks.md` has one check. It reads the worktree's file through the factory's own model lookup and asserts:
- no warnings;
- the approver is on Sonnet at both depths, light and full, for both Tier 1 and Tier 2;
- the trial's comment is present.

It failed first, with the approver still on Opus at the light depth, and passes now. No test in the suite reads this repo's own `factory.toml`; the tests build scratch repos.

**Tests:** `tests/test_nothing_local.py` (8 passed) and the model tests in `tests/test_factory_depth.py` (2 passed). Nothing is left in `notes.md`.

- UNTESTABLE: none

## Evidence

$ sh /tmp/203check.sh   # the checks.md block, before the edit
AssertionError: (1, 'light', 'opus')
exit: 1

$ sh /tmp/203check.sh   # after the edit
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py config
"models": {},   (base branch's copy; parses with no error)
exit: 0

$ uv run --group dev pytest -q tests/test_nothing_local.py
8 passed in 10.32s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_depth.py -k "model"
2 passed in 1.35s
exit: 0
