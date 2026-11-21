The build is done and left uncommitted: `start` now records what an intent's `closes:` names, and a build can no longer remove that by editing its own intent. Tests: the 4 `closes` tests pass, and 8 related test files (635 tests) pass too. I didn't run the whole suite; the gate runs it.

There is one departure from the Approach. Autopilot never runs `start`: its `start` step is only `stage build`. So recording at `start` alone would leave autopilot runs unprotected, and 216's D9 is the reason this change exists. I also record in `agent`, just before `claude` runs. That is raised as a default below.

**What was built**
- **The record:** `start` (once it has no refusals) and `agent` (once nothing is left to refuse) write a `{"change", "closes"}` line to the records ledger in the git common dir. It is written only when the intent has a `closes:`, and only once per value, using the same lock as the existing records. If it can't be written, that step refuses.
- **Old checks are unaffected:** the new line has no `record` or `sha256`, so neither the factory's `vouched()` nor core's `vouched_in()` can mistake it for a vouched record. The ledger's format is extended, not redefined.
- **The union:** `intent_closes()` now returns what every past record named plus what the intent says now. If the intent already holds everything recorded, it returns the intent's text exactly as before. Otherwise it returns `[a, b]`, recorded issues first.
- **The landing:** `land_signals()` raises its `issue` signal from `preflight`'s `closes` or from `intent_closes()`. Before, it read only `preflight`, which takes `closes:` from the branch's own intent.
- **Files:** most of this is in `factory.py`; the landing change is in `landing.py`. The factory's README paragraph on the ledger now mentions the record.

**Answers to the intent's open questions**
- **Restarts and upgrades:** the union covers every record of the change, not just the latest run's, so a restart can't lose an issue an earlier run recorded.
- **Core:** the board, `status` and `factory_records.py` don't read the new line, so it is the factory's alone and nothing in core needed a pinned copy.

**Tests added** (in `tests/test_factory_decisions.py`)
- `test_closes_recorded_at_start_outlives_an_edit`: `start` records once, even when run twice. After `closes:` is deleted, `no_confirm_why()` still names `closes: [12]` and `land_signals()` still gives the `issue` signal. Changing the intent to `[15]` gives `[12, 15]`.
- `test_a_change_closing_nothing_records_nothing`: no `closes:` means no ledger line, `None`, and no `issue` signal.
- `test_an_agent_run_records_closes_without_start`: covers the autopilot path.
- Before the code changed, the first and third failed because the ledger was empty, which is the expected reason. The second already passed, which is correct, since it checks today's behaviour.

**`plan.md`:** written before the code. It was then updated to add the README and to note the order of the union.

**`notes.md`:** nothing left there.

- DECISION: [default] Record `closes:` in `factory.py agent` as well as `start`? Going ahead with both unless told otherwise.
  - OPTION: start and agent — covers autopilot, which never runs `start`; it re-reads the ledger on every agent call, but only appends once per value
  - OPTION: start only — exactly what the Approach says; autopilot runs, the ones D9 relies on, record nothing and a build could still remove `closes:` there
  - WHY: the intent's goal is that what a change closes is fixed before any agent runs, and autopilot reaches its agents without `start`

## Evidence

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "closes_recorded or closing_nothing or records_closes_without"   (before the code)
FAILED tests/test_factory_decisions.py::test_closes_recorded_at_start_outlives_an_edit
FAILED tests/test_factory_decisions.py::test_an_agent_run_records_closes_without_start
2 failed, 1 passed, 96 deselected in 2.94s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "closes_recorded"   (first implementation, union order)
E       assert '[15, 12]' == '[12, 15]'
exit: 1

$ uv run --group dev ruff check plugins/factory/scripts tests/test_factory_decisions.py && uv run --group dev ruff format --check plugins/factory/scripts tests/test_factory_decisions.py
All checks passed!
5 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_decisions.py tests/test_factory_agent.py tests/test_autopilot.py tests/test_land.py tests/test_records_ledger.py tests/test_modules.py tests/test_train.py tests/test_hand_gate.py
635 passed, 1 skipped in 277.63s (0:04:37)
exit: 0

$ uv run --group dev pytest -q tests/test_nothing_local.py tests/test_feature_map.py
17 passed in 9.25s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "closes or closing"
4 passed, 95 deselected in 3.35s
exit: 0

$ git status --short
 M plugins/factory/README.md
 M plugins/factory/scripts/factory.py
 M plugins/factory/scripts/landing.py
 M tests/test_factory_decisions.py
?? .sdlc/work/219-closes-at-start/
exit: 0

I fixed the red gate; the change is still uncommitted. All 72 tests in `tests/test_prompts.py` pass now, and the change's own 4 `closes` tests still pass. I didn't rerun the whole suite; the gate runs it again.

**What failed:** the 12 failures were all in `tests/test_prompts.py`. That test's fixture replaces `factory._git` with a stand-in that rejects any git call it wasn't written for. The approve prompt now goes through `intent_closes()`, which reads the records ledger. Finding the ledger takes one `git rev-parse --path-format=absolute --git-common-dir` call, and the stand-in rejected it.

**The fix:** one line in the fixture's setup, `mp.setattr(factory, "recorded_closes", lambda folder: [])`. It stubs the ledger read the same way the fixture already stubs `read_ledger`, so these tests still don't touch git. All 12 prompts, `approve-defaults-closes` included, still match their recorded copies. The change's own code is unchanged.

`plan.md` and `notes.md` are unchanged. No new decisions; the round's one default (record `closes:` in `agent` as well as `start`) still stands.

## Evidence

$ grep -n "FAILED\|Error\|error\|failed\|passed" .sdlc/work/219-closes-at-start/build/round-1.gate.md | head -30
    E       AssertionError: ('rev-parse', '--path-format=absolute', '--git-common-dir')
    FAILED tests/test_prompts.py::test_every_prompt_part_is_rendered - AssertionE...
    FAILED tests/test_prompts.py::test_every_prompt_matches_its_recorded_copy[approve-upgraded]
    12 failed, 3938 passed, 29 skipped in 262.13s (0:04:22)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_prompts.py
72 passed in 26.28s
exit: 0

$ uv run --group dev ruff check tests/test_prompts.py && uv run --group dev ruff format --check tests/test_prompts.py
All checks passed!
1 file already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "closes or closing"
4 passed, 95 deselected in 3.70s
exit: 0
