# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its arbiter's,
> never the person's, and the same fault worded differently is one more. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts
> ship's own alone into the `Sdlc-Findings` trailer (its `agents=` says how many it left out),
> words ship's question from the ones proposed `fix`, and `ship` refuses while one is still `open`
> or `fix`. On a diff that touches a sensitive path, this note also says `Fresh review: ran`, or
> `Fresh review: skipped, <why>`. Each of ship's further passes that applies says the same on a
> line of its own: `Security review:`, `Behaviour check:`, `UI review:` and `UX review:`, and
> their findings' `By:` is `ship-security`, `ship-behaviour`, `ship-ui` or `ship-ux`, counted as
> ship's own (`passes=` says how many). A behaviour check that ran ends the file with an
> `## Evidence` section: each command on a `$ ` line, the tail of its output, then `exit: <n>`.

Fresh review: skipped, the factory's rounds stand in

## F1. [important] [contract] plugins/factory/scripts/factory.py:4292 (`_claude`): `subprocess.run` passes no `env=`, so every agent session started by `factory.py agent` inherits `SDLC_FACTORY_AUTOPILOT_RUN` from the loop.

plugins/factory/scripts/factory.py:4292 (`_claude`): `subprocess.run` passes no `env=`, so every agent session started by `factory.py agent` inherits `SDLC_FACTORY_AUTOPILOT_RUN` from the loop. While the loop holds the lock, `autopilot_running()` is true inside those sessions. The builder, the resolver and the other agents that have `Bash` or `Edit` can then run `factory.py land --by autopilot`, `answer --by autopilot` or `write-spec --by autopilot` themselves. R2 and R6 say only the script's own children may pass the flag, and AGENTS.md repeats that. Fix: have `_claude()` build its env without `AUTOPILOT_RUN_ENV` (and without `TRAIN_RUN_ENV`). Decide the prompt addition and the `cmd_autopilot_agent` gate before `_claude` runs, as they are now. Add a test that a `_claude` call's env lacks the variable.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: fixed
By: code

## F2. [important] [correctness] plugins/factory/scripts/autopilot.py (`run_step`), tests/test_autopilot.py: the builder's report says `test_autopilot_end_to_end` drives the loop with `run_step` stubbed, so no test runs the real subprocess path under `AUTOPILOT_RUN_ENV` (the real lock, child env and JSON parsing).

plugins/factory/scripts/autopilot.py (`run_step`), tests/test_autopilot.py: the builder's report says `test_autopilot_end_to_end` drives the loop with `run_step` stubbed, so no test runs the real subprocess path under `AUTOPILOT_RUN_ENV` (the real lock, child env and JSON parsing). The spec's dry run calls for a fake `claude`. Fix: add one test that runs a real `run_step` for a command that needs the lock, such as `answer --by autopilot`, and checks that it succeeds with the env set, is refused without it, and that `_claude`'s env lacks the variable (this would catch the finding above).

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: fixed
By: code

## F3. [nit] [correctness] `cmd_answer` reads and rewrites `decisions.md` with no lock.

plugins/factory/scripts/factory.py:2417: `cmd_answer` reads and rewrites `decisions.md` with no lock. This is safe only because one step runs per change at a time. A comment saying so would help.

Evidence: plugins/factory/scripts/factory.py:2417
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F4. [important] [contract] **The builder can use `--by autopilot` too.** The rule is that only the loop's own child processes may use `--by autopilot`.

plugins/factory/scripts/factory.py:4292: **The builder can use `--by autopilot` too.** The rule is that only the loop's own child processes may use `--by autopilot`. In practice any process whose environment names the held lock gets in, and `_claude()` passes its whole environment on to every agent session it starts. So while autopilot runs, each `agent --task build|fix|rework` session inherits `SDLC_FACTORY_AUTOPILOT_RUN`. That includes the builder, which has `Bash`, `Edit` and `Write` and runs with `--permission-mode auto`. **Exploit:** a builder misled by a seed's text, possibly a public issue's, can run commands under `autopilot_running()` that the loop alone was meant to run. It can tick its own blocking lines (`factory.py answer NNN Dk --by autopilot`). Or it can run `stage NNN test` and then `train --begin <id> --by autopilot` with `train --run`, and land a change the loop is holding. A held change touches a guard or carries a `- CONTRACT:` line, which are exactly the cases autopilot must never land. `land-check` never sees `[autopilot] guards`, so nothing in the train stops it. **Fix:** in `_claude()`, pass `env=` with `AUTOPILOT_RUN_ENV` and `landing.TRAIN_RUN_ENV` removed. Add a test in `tests/test_autopilot.py` that stubs `subprocess.run` for an `agent` call made under the autopilot env and asserts the session's env doesn't contain `AUTOPILOT_RUN_ENV`.

Evidence: plugins/factory/scripts/factory.py:4292
Class: security review, round 1
Disposition: fixed
By: security

## F5. [pre-existing] [contract] `_claude()` passes `TRAIN_RUN_ENV` on to the agent sessions a `train --run` starts (`train-resolve`, `land-fix`, which edit).

plugins/factory/scripts/factory.py:4292: `_claude()` passes `TRAIN_RUN_ENV` on to the agent sessions a `train --run` starts (`train-resolve`, `land-fix`, which edit). So an agent's own `factory.py train …` passes the `train_running()` check at landing.py:1978, which is meant for the loop's own children.

Evidence: plugins/factory/scripts/factory.py:4292
Class: security review, round 1
Disposition: recorded
By: security

## F6. [nit] [contract] `starts()` reads `land.batch` from the main checkout's config on every pass instead of from the state fixed at `--begin` (the main checkout is the base branch, so this is safe today)

plugins/factory/scripts/autopilot.py:1036: `starts()` reads `land.batch` from the main checkout's config on every pass instead of from the state fixed at `--begin` (the main checkout is the base branch, so this is safe today)

Evidence: plugins/factory/scripts/autopilot.py:1036
Class: security review, round 1
Disposition: fixed
Reason: weighed S med: handed to the builder's rework, and not raised again
By: security

## F7. [nit] [correctness] many `# fmt: skip` pragmas keep dense literals unformatted

tests/test_autopilot.py:263: many `# fmt: skip` pragmas keep dense literals unformatted

Evidence: tests/test_autopilot.py:263
Class: test review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: test

## F8. [important] [correctness] `status_items()` runs `sdlc.py status --json`, but `sdlc.py status` takes only `--all`.

plugins/factory/scripts/autopilot.py:289: `status_items()` runs `sdlc.py status --json`, but `sdlc.py status` takes only `--all`. Argparse rejects `--json`, so `autopilot --preview` prints the warning `sdlc.py status couldn't be read: … unrecognized arguments: --json` and `candidates` is always `[]`. A real `--run` would never find a seed and would stop at once. The spec's R10 assumes `status --json` exists, and no part of this change adds it. Either add a `--json` output with `next_up.items` (id, group, theme) to `sdlc.py status`, or read the candidates another way. The tests don't catch this, apparently because the call is stubbed.

Evidence: plugins/factory/scripts/autopilot.py:289
Class: behaviour review, round 1
Disposition: fixed
By: behaviour

## F9. [important] [contract] **The builder can still use `--by autopilot` through the gate and `accept`.** `_run_check()` runs the base branch's `[commands] check` without an `env=`.

plugins/factory/scripts/factory.py:3499: **The builder can still use `--by autopilot` through the gate and `accept`.** `_run_check()` runs the base branch's `[commands] check` without an `env=`. So when the loop runs `gate NNN` through `run_step()`, which sets `AUTOPILOT_RUN_ENV` (autopilot.py:390–400), the host's check inherits the variable while the loop holds the lock. That check runs the change's own code: its tests, a `conftest.py`, anything they import. The `accept` step works the same way. `_sdlc()` removes only `UNSET_FOR_SDLC` (`SDLC_CLOSE_RAN`, `SDLC_OWN_SCRIPT`, `VIRTUAL_ENV`), so `sdlc.py accept` runs the `checks.md` commands, the builder's tests included, with the variable set. A train's tip gate (`gate --land`, and `--build`) inherits it too, through `_run_env()`, which builds on `os.environ`. **Exploit:** a builder misled by a seed's text doesn't need its own `Bash` anymore. It writes a test module that runs `factory.py answer NNN Dk --by autopilot` when it is imported (or `stage NNN test`, then `train --begin … --by autopilot` and `train --run`). The next `gate` step then runs that code as one of the loop's children, and `autopilot_running()` is true for it. This is the same breach last round's kept finding named. `agent_env()` closed only the direct agent-session path, and the change's own code still runs under the variable. **Fix:** remove `AUTOPILOT_RUN_ENV` and `landing.TRAIN_RUN_ENV` (use `agent_env()`) wherever the factory runs a host's command or code the change wrote:

Evidence: plugins/factory/scripts/factory.py:3499
Class: security review, round 2
Disposition: fixed
By: security

## F10. [nit] [correctness] the "agent is refused" half of the real-step test calls `agent_env()` directly rather than going through `_claude`.

tests/test_autopilot.py:1139: the "agent is refused" half of the real-step test calls `agent_env()` directly rather than going through `_claude`. The stubbed test above covers `_claude`, so the two together close the gap.

Evidence: tests/test_autopilot.py:1139
Class: test review, round 2
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F11. [nit] [contract] no test that a host's `[commands] check`, run by a `gate` step under the loop, lacks `AUTOPILOT_RUN_ENV`/`TRAIN_RUN_ENV`; `take_markers()` is untested

tests/test_autopilot.py:1140: no test that a host's `[commands] check`, run by a `gate` step under the loop, lacks `AUTOPILOT_RUN_ENV`/`TRAIN_RUN_ENV`; `take_markers()` is untested

Evidence: tests/test_autopilot.py:1140
Class: security review, round 3
Disposition: recorded
Theme: tests
Cost: S
Value: med
By: security

## F12. [nit] [correctness] R19 still gives the default guards as the docs plus `irreversible`, but D8 added `sensitive`.

`.sdlc/work/216-autopilot/spec.md`: R19 still gives the default guards as the docs plus `irreversible`, but D8 added `sensitive`. The spec should be brought in line with the ledger

Evidence: .sdlc/work/216-autopilot/spec.md
Class: code review, round 4
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F13. [nit] [contract] `_default_guards()` drops the policy and review docs without a word when `sdlc.py config` fails; add a warning to `load_config`'s list, or stop at `--begin`

plugins/factory/scripts/autopilot.py:211: `_default_guards()` drops the policy and review docs without a word when `sdlc.py config` fails; add a warning to `load_config`'s list, or stop at `--begin`

Evidence: plugins/factory/scripts/autopilot.py:211
Class: security review, round 4
Disposition: minor
Reason: past the cap of 5 nits a change files
By: security

## F14. [nit] [correctness] the test that uses the real `status --json` is marked `@needs_uv`, so it is skipped where `uv` is absent.

tests/test_autopilot.py:1218: the test that uses the real `status --json` is marked `@needs_uv`, so it is skipped where `uv` is absent. The D9 and `issues` coverage there then rests on the stubbed `candidates` test alone

Evidence: tests/test_autopilot.py:1218
Class: test review, round 4
Disposition: minor
Reason: past the cap of 5 nits a change files
By: test
