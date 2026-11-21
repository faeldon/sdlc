# 216-autopilot — entries

## [2026-11-21-47] [idea] Let autopilot take `next_up`'s cheap-nits lines

Left undone by 216-autopilot, carried forward when it landed: `next_up`'s cheap-nits lines (`rule: nits`) carry no seed id, so autopilot never takes them, though `READY_RULES` lists them.
See .sdlc/work/216-autopilot/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-48] [idea] Test the whole autopilot loop's subprocesses with a stand-in `claude`

Left undone by 216-autopilot, carried forward when it landed: `test_autopilot_end_to_end` drives the loop in process with `run_step` stood in for, as the train's tests do. Since round 1, `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs a real `run_step` child under the lock, but no test runs the whole loop's subprocesses with a stand-in `claude`.
See .sdlc/work/216-autopilot/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-49] [idea] Retro overturn rate for autopilot's calls

Left undone by 216-autopilot, carried forward when it landed: The retrospective's overturn rate for autopilot's calls (the spec's question 6) is left for a later seed, as the intent's resolution says.
See .sdlc/work/216-autopilot/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-50] [idea] Stop `_claude()` passing `TRAIN_RUN_ENV` to editing agent sessions. I did not file it as a bug: the Bugs severity words (`high`, `med`, `low`) describe wrong output or lost work, and none fits a guard weakness, so I carry it as a seed.

Left undone by 216-autopilot, carried forward when it landed: pre-existing: plugins/factory/scripts/factory.py:4292: `_claude()` passes `TRAIN_RUN_ENV` on to the agent sessions a `train --run` starts (`train-resolve`, `land-fix`, which edit). So an agent's own `factory.py train …` passes the `train_running()` check at landing.py:1978, which is meant for the loop's own children.
See .sdlc/work/216-autopilot/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-51] [nit] `cmd_answer` reads and rewrites `decisions.md` with no lock.

Raised by the code review of 216-autopilot, round 1: plugins/factory/scripts/factory.py:2417: `cmd_answer` reads and rewrites `decisions.md` with no lock. This is safe only because one step runs per change at a time. A comment saying so would help.

Theme: docs
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 216-autopilot (correctness)

## [2026-11-21-52] [nit] many `# fmt: skip` pragmas keep dense literals unformatted

Raised by the test review of 216-autopilot, round 1: tests/test_autopilot.py:263: many `# fmt: skip` pragmas keep dense literals unformatted

Theme: style
Paths: tests/test_autopilot.py
Cost: S
Value: low
Raised by: 216-autopilot (correctness)

## [2026-11-21-53] [nit] the "agent is refused" half of the real-step test calls `agent_env()` directly rather than going through `_claude`.

Raised by the test review of 216-autopilot, round 2: tests/test_autopilot.py:1139: the "agent is refused" half of the real-step test calls `agent_env()` directly rather than going through `_claude`. The stubbed test above covers `_claude`, so the two together close the gap.

Theme: tests
Paths: tests/test_autopilot.py
Cost: S
Value: low
Raised by: 216-autopilot (correctness)

## [2026-11-21-54] [nit] no test that a host's `[commands] check`, run by a `gate` step under the loop, lacks `AUTOPILOT_RUN_ENV`/`TRAIN_RUN_ENV`; `take_markers()` is untested

Raised by the security review of 216-autopilot, round 3: tests/test_autopilot.py:1140: no test that a host's `[commands] check`, run by a `gate` step under the loop, lacks `AUTOPILOT_RUN_ENV`/`TRAIN_RUN_ENV`; `take_markers()` is untested

Theme: tests
Paths: tests/test_autopilot.py
Cost: S
Value: med
Raised by: 216-autopilot (contract)

## [2026-11-21-55] [nit] R19 still gives the default guards as the docs plus `irreversible`, but D8 added `sensitive`.

Raised by the code review of 216-autopilot, round 4: `.sdlc/work/216-autopilot/spec.md`: R19 still gives the default guards as the docs plus `irreversible`, but D8 added `sensitive`. The spec should be brought in line with the ledger

Theme: docs
Paths: .sdlc/work/216-autopilot/spec.md
Cost: S
Value: low
Raised by: 216-autopilot (correctness)
