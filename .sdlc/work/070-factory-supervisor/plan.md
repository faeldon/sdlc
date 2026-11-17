---
id: 070
slug: factory-supervisor
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 070 — A supervisor that runs a factory change and calls the person only when needed · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `STARTS["build"]` gains `(2, "plan")` (`spec: true`);
  `find_change` finds a change's worktree from the main checkout (a `worktrees()` copy of
  `sdlc.py`'s, pinned); `factory.mode` (default `auto`, checked against claude's modes, read from
  the base branch's `.sdlc/factory.toml`); new `agent` (headless `claude -p --agent
  sdlc-factory:<role>` in the worktree, prompts composed from a `--task`, session ids in
  `runs/<role>.sessions`, the reply to `--to`) and `ready` (read-only, ordered, with overlaps).
- `plugins/factory/skills/build/SKILL.md`: rewritten around the supervisor: background agent
  runs, the spec-writer's draft before the one WAIT for a Tier 2 at `plan`, "ready to ship",
  `factory.py ready`; `Agent`/`SendMessage` and `Write` dropped from `allowed-tools`, `agent` and
  `ready` rules added; every pinned phrase kept, step numbers kept.
- `plugins/factory/agents/*.md`: "spawned by the skill" wording becomes "run by the supervisor as
  its own session in the change's worktree"; the builder gains `Agent` limited to `Explore` and
  `Plan` (R16), read-only, and says so.
- `scripts/metrics.py`: the `ident` rebinding bug in `read_events`; `first_approval`; on `main`,
  keep the typed `/sdlc-factory:build NNN` and each dialog naming the change; role sessions from
  a `roles` map folded into `subagent` events, and the builder session's own `subagents/` read;
  `REQUIRED` for factory Tier 1 and for a Tier 2 with no spec stage; docstring contract extended.
- `scripts/sdlc.py`: `measure_change` builds `roles` from the branch's `runs/*.sessions`.
- Tests: `tests/test_factory.py` (start from main, the flipped `STARTS` row, `mode`, `agent` with
  a fake `claude` on `PATH`, `ready`), `tests/test_metrics.py` (the bug, `first_approval`, an
  interleaved supervisor transcript, role sessions, the builder's subagents, `REQUIRED` rows),
  `tests/test_skills.py` (no "chief of staff", the builder's tools, build's rules),
  `tests/test_windows.py` (the `claude` call's text mode, the `worktrees()` pin).
- Docs: `plugins/factory/README.md`, `README.md`'s factory bullet, `AGENTS.md`'s factory
  paragraph, `docs/REFERENCE.md` (`factory.mode`).

## Work order

1. `metrics.py`: the `ident` bug, `first_approval`, `REQUIRED`; tests. Stops nothing else.
2. `factory.py`: `mode`, `find_change` from main, `STARTS`; tests.
3. `factory.py agent` and `ready`, with the fake `claude`; tests.
4. `metrics.py` membership for supervisor dialogs, role sessions, the builder's subagents, and
   `measure_change`'s `roles`; tests.
5. The build skill and the agents' text, the builder's `Agent`; skills tests.
6. Docs; `./check.sh`.

## Tests

- R1: a repo-wide test for "chief of staff" outside `.sdlc/work/`.
- R2–R3, R8–R11: the build skill's pins in `tests/test_skills.py`, kept and extended (rules for
  `agent`/`ready`, the question naming the change).
- R4: `start` from the main checkout finds the worktree; `(2, "plan", "build")` accepted.
- R5–R7: `agent` against the fake `claude`: argv, `cwd`, a new session id appended, `--resume`
  for rework, `--to` written and refused outside the folder, a non-zero exit and a timeout
  reported; `mode` from the base branch, a bad one warned.
- R11: `ready`'s order (dependencies first) and overlaps.
- R12: an interleaved main-branch transcript naming two changes, each keeping only its own
  dialogs; a role session's `Sdlc-Role`; the `ident` bug.
- R13: `first_approval` (revise then yes → one gate, one question); the `REQUIRED` rows.
- R16: `test_agents_have_their_tools_and_nothing_more` with the builder's `Agent` limited; a
  builder session's `subagents/` read into `Sdlc-Role`.
- R14–R15: docs read by hand; `./check.sh`.
- Manual (paid, the person's call): from the main checkout, `/sdlc-factory:build` on a scratch
  Tier 2 at `plan`, then a second before the first's draft lands.

## Rollback

`git revert <sha>`. Not covered: `runs/` and round files a real run left in an open change's
folder (delete by hand), and `Close` trailers written meanwhile, which keep their numbers.
