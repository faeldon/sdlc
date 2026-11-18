DECISION: ESCALATE

## Why
All three round-1 reviewers returned `VERDICT: PASS`. The gate record (`build/round-1.gate.md`) shows GATE: PASS, with 2867 passed and 28 skipped. Each of R1–R12 has code and a test, or an acceptance check for R12. On the reviewers' account and my own read of `cmd_check()` and `_run_check()`, this change is ready on its merits. The skill still requires ESCALATE, because the run was stopped as "builder reports a requirement it can't test." The builder's actual line is `- UNTESTABLE: none.`, so the stop looks like a misread "none" rather than a real gap.

## Open items
- None. No reviewer asked for a change. Three nits are left, each low severity:
  - code: a README line at `plugins/factory/README.md:170` runs over the wrap width.
  - code: `FACTORY_CHECK_RE` accepts a quoted path but `HAND_GATE_RE` doesn't.
  - test: the new R3/R4 tests carry no `portable` mark, which the reviewer judged probably right because they use `sh`/`sleep`.

## Decisions to confirm
- SETTLED: D1: R6 says "every prompt `_task()` sends the builder", and the spec's Design says "`_task()` appends it to every builder prompt". `resolve` and `land-fix` reach the builder through `_task()`/`_land_task()`. `builder.md` points to "the `check` command your prompt names". The code reviewer (round 1) found it reasonable, and it grants no new permission, because `check` runs only the base branch's command.
- SETTLED: D2: `read_evidence()` lives in `factory.py`, and `tests/test_evidence.py` tests the retro's `.sdlc/evidence.py`. `plan.md` (Tests, R10) records the move to `tests/test_factory.py`, and both the code and test reviewers confirm that's the right home for the test.

## Every other reason I escalate for
- ESCALATED: look: the run stopped as if the builder had reported an untestable requirement, but its report says `- UNTESTABLE: none.` (`build/round-1.md`, `runs/step.md`). Nothing in the build is untestable, and the person should confirm that this stop is spurious.
- ESCALATED: look: `AGENTS.md`'s policy sentence on *The factory* changes from "`factory.py gate` the one place it runs a host's command" to "`gate` and `check`, through one function (`_run_check()`)". The spec's Contracts touched section calls this a policy edit for the person to approve. It was built exactly as the spec words it, but it is the person's call.

## Reconsider the approach
Nothing kept coming back: round 1 converged with three PASSes and no CHANGE. The next step I'd take is in the factory, not this change. Make the stop rule that reads the builder's `- UNTESTABLE:` line treat `none` (with or without a trailing period) as no untestable requirements, and file that as a seed. Then land 155 as built. The spec, the plan and the model need no change.

## For the person at ship
- Read `cmd_check()` and `_run_check()` in `plugins/factory/scripts/factory.py`, around lines 3205–3241. Confirm that `gate` still captures output and writes its record unchanged, and that `check` writes nothing.
- Check `check_line()` and `_task()` (around line 3858). The prompt names this machine's absolute path to `factory.py`, so make sure it never reaches a committed file.
- Read the `AGENTS.md` policy sentence edit.

## Release impact
- IMPACT: minor — factory hosts get a new `factory.py check NNN` command that runs the base branch's check inside a gate slot. Agents' prompts now route full runs through it, and metrics count it as a test run. Nobody has to do anything differently.

## Undone items
- None. There is no `notes.md`, and the builder reports nothing left.
