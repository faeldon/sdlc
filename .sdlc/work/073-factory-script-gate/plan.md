---
id: 073
slug: factory-script-gate
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 073 — Run the gate as a script step before a factory round's reviewers · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`:
  - a pinned `_sh()` copy;
  - `_base_check()`, `_tree_hashes()` (lifted out of `cmd_snapshot`), `gate_path()`,
    `build_hash()`, `read_gate()` and `cmd_gate()`;
  - the `gate`, `fix` and stop branches in `loop_state()`;
  - the `fix` task;
  - `max_runs()` with `GATE_FIXES`;
  - the `gate` subcommand.
- `plugins/factory/skills/build/SKILL.md`: the `gate` rule, Steps 0, 1 and 4, the WAIT clause,
  and the `gate` and `fix` branches.
- `plugins/factory/agents/reviewer-behaviour.md`: reads the gate file and no longer runs the gate.
- `plugins/factory/agents/builder.md`: what a `fix` prompt is.
- `scripts/sdlc.py`: `_factory_files()` counts `gate_fail`.
- `scripts/metrics.py`: `rework()` passes `gate_fail` on.
- `skills/ship/factory.md`: names the gate file as the script's record.
- `plugins/factory/README.md`, `AGENTS.md`, `docs/REFERENCE.md`: docs.
- `tests/test_factory.py`, `tests/test_windows.py`, `tests/test_skills.py`, and
  `tests/test_metrics.py` or `tests/test_sdlc.py`: tests.
- `.sdlc/work/073-factory-script-gate/notes.md`: the duty R12 leaves to 072.

## Work order

1. `factory.py`:
   - `_sh`, `_base_check`, `_tree_hashes`, `cmd_gate` and the `gate` subcommand;
   - gate tests (base-branch command, PASS, FAIL, timeout, changed tree, appended attempts);
   - the `_sh` pin.
2. `loop_state` `gate` / `fix` / stop, the `fix` task and `max_runs`, with the loop tests (the
   sequence, the cap, no command, old rounds, `fix` refused unless named) and the `max_runs`
   expectations.
3. `_factory_files` `gate_fail` and `rework()`, with their tests.
4. The build skill and the two agents, with the skill tests (rule, WAIT clause, branches).
5. Ship's `factory.md`, the READMEs, `AGENTS.md`, `REFERENCE.md` and `notes.md`.
6. `./check.sh`.

## Tests

| Requirement | Proved by |
|---|---|
| R1, R2 | gate tests in `test_factory.py` |
| R3, R4, R5, R6, R14 | loop tests in `test_factory.py` |
| R7 | a light-depth loop test still names `gate` |
| R8 | `test_what_runs_the_change…` and `test_no_agent_but_the_builder_runs_checks` |
| R9 | `test_skills.py` (rules used, WAIT clause, branches) |
| R10 | the `gate_fail` test |
| R11 | the `_sh` pin and `test_windows.py` |
| R12 | `notes.md`, checked at ship |
| R13 | read at ship |
| R15 | `./check.sh` |

Manual: in a scratch repo whose `main` has `check = "exit 1"`, run `gate` (expect FAIL), then
`verdicts` (expect `fix`), then append to the report and snapshot, then `verdicts` (expect
`gate`).

## Rollback

`git revert <sha>` of the change's commit undoes all of it. Run folders written while it was in
place keep their `build/round-<N>.gate.md` files, which the reverted code never reads. `Close`
trailers already written keep `gate_fail=`, which older readers ignore as an unknown key.
