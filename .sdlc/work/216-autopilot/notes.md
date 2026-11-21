# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Departures from the spec, each raised as a decision in the build report

- The weight tables are `[autopilot.debt_weights]` and `[autopilot.risk_weights]`, not
  `[autopilot.debt]` and `[autopilot.risk]`: TOML can't hold a table named `debt` beside the limit
  `[autopilot] debt = 40`, which R24 and R26 both ask for.
- R17's "the approver is then run again" after autopilot answers the open calls at `done` isn't
  built: `agent --task approve` is refused once `verdicts` says `done` (`TASK_STEP`), and the
  landing reads the answered ledger (`escalation_lines()`) as it does after `/sdlc-factory:decide`.
- R27: a spent debt or risk budget starts no wave, intent or train, but every change already opened
  is taken on to `stage: test`, which the spec's dry run (`debt = 1`) asks for; a spent dollar cap
  or hours start no agent session at all.
- R13 reads the `Close` commits through `factory.closes()`, the factory's own reader of the base
  branch's first-parent line, not a `sdlc.py` command: none prints them.
- `--level` is the highest tier autopilot opens (1 or 2); the intent didn't say what "the level"
  bounds.
- R5's decide skill lists autopilot's calls from `ask`'s `autopilot` list, so its text never holds
  the words R6 forbids every other skill.

## Left undone

- [x] The board shows nothing of `opened_by: autopilot` or a run under way: `status` does; the → dropped: already carried by seed 2026-11-21-34, so a second seed would duplicate it.
  board's is seed 2026-11-21-34, which waits on this change.
- [x] `next_up`'s cheap-nits lines (`rule: nits`) carry no seed id, so autopilot never takes them, → seed: 2026-11-21-47
  though `READY_RULES` lists them.
- [x] `test_autopilot_end_to_end` drives the loop in process with `run_step` stood in for, as the → seed: 2026-11-21-48
  train's tests do. Since round 1, `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does`
  runs a real `run_step` child under the lock, but no test runs the whole loop's subprocesses
  with a stand-in `claude`.
- [x] The retrospective's overturn rate for autopilot's calls (the spec's question 6) is left for a → seed: 2026-11-21-49
  later seed, as the intent's resolution says.

## Round 1

- `sdlc.py status --json` didn't exist (R10 assumed it): added, read-only, printing `next_up`'s
  items and warnings.
- Agent sessions now run with `agent_env()`, the environment without `AUTOPILOT_RUN_ENV` and
  `TRAIN_RUN_ENV`, so nothing an agent runs is one of a loop's children.

## Round 2

- `agent_env()` covered the agent session alone: the host's check (`gate`), the acceptance checks
  (`accept`, through `sdlc.py`), git and its hooks still ran with the marker. `factory.py` now takes
  both loop markers out of its own env as it starts (`take_markers()`), and only `loop_env()`, used
  by `autopilot.run_step()` and the train's `_run_env()`, gives them back to a loop's own child.

## Round 4

- The person confirmed every default (D1–D10) after the round-3 escalation. Reviewers raised D8,
  D9 and D10 as defaults that nobody had built, so this round builds them: sensitive paths in the
  default guards, Issue seeds only when named and opened with `closes:`, and the marker's limit
  written down.
- `status --json`'s `next_up` items now carry `issues`. The text `status` doesn't print it.

- [x] pre-existing: plugins/factory/scripts/factory.py:4292: `_claude()` passes `TRAIN_RUN_ENV` on to the agent sessions a `train --run` starts (`train-resolve`, `land-fix`, which edit). So an agent's own `factory.py train …` passes the `train_running()` check at landing.py:1978, which is meant for the loop's own children. → seed: 2026-11-21-50
