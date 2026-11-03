---
id: 038
slug: factory-review-loop
kind: plan
created: 2026-11-04
updated: 2026-11-04
---

# 038 — The factory's review rounds verify, converge and scale to risk · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

Read before planning: `factory.py` (`load_config`, `read_rounds`, `cmd_verdicts`, `cmd_carry`,
`max_runs`), the build skill, the reviewer and approver agents, `sdlc.py`'s `_factory_files()` and
`risk_paths()`, `metrics.rework()` (`Sdlc-Review` lines), and the tests pinning the factory's
formats (`tests/test_metrics.py`, `tests/test_skills.py`, `tests/test_factory.py`).

- `plugins/factory/scripts/factory.py`
  - `ROLES` gains `verifier`; `DEFAULTS["light"]` (`["code"]`, 2); `KEPT_RE`, `DROPPED_RE`,
    `PREEXISTING_RE`; `RECONSIDER`.
  - `load_config` validates `[light]` like the top level (R10); `max_runs` counts the verifier
    (R11).
  - `_base`, `_changed_paths` (merge-base diff + untracked, no `.sdlc/work/`), `_sensitive`
    (`git show <base>:.sdlc/config.toml`), a pinned copy of `risk_paths()` (R8).
  - `cmd_snapshot`: `build/round-<N>.files` (R4).
  - `read_rounds`: every reviewer file present, `PREEXISTING` lines, `verified.md` (R1, R6).
  - `cmd_verdicts`: depth (R9), `verify` (R1), rework only on a kept line (R2), `reworked`,
    `settled`, `repeats`, `untouched` (R4–R6), the exhausted decision rule (R7).
  - `cmd_carry`: kept lines and `PREEXISTING` lines (R2, R6).
- `plugins/factory/agents/verifier.md` (new) (R3); the reviewers (later rounds, `PREEXISTING`),
  the approver (exhausted), the builder (KEPT lines).
- `plugins/factory/skills/build/SKILL.md`: Steps 0, 2 (R11), 3; `factory.py snapshot` rule.
- `scripts/sdlc.py`: `FACTORY_KEPT_RE`, `FACTORY_DROPPED_RE`; `_factory_files()` counts `dropped`
  (R12).
- `skills/ship/SKILL.md` Step 0: `verified.md` (R13).
- `plugins/factory/README.md`, `docs/REFERENCE.md`, `AGENTS.md` (R14).
- `.sdlc/work/inbox.md` at ship (R15).
- Tests: `tests/test_factory.py`, `tests/test_metrics.py`, `tests/test_skills.py`.

## Work order

1. `factory.py` config (`[light]`, roles, `max_runs`); tests.
2. Risk helpers and the snapshot command; tests.
3. `read_rounds`, `verdicts`, `carry`; tests.
4. Agents and the build skill; skill tests.
5. `sdlc.py` `_factory_files` and the regex copies; ship Step 0; tests.
6. Docs; `./check.sh` with its exit code read directly.

## Tests

- R1, R2: verify step; a missing and an extra line stop; all dropped → approve; kept → rework;
  carry of kept lines.
- R3: the verifier's tools hold no `Write` or `Edit`.
- R4: snapshot file and `reworked`.
- R5, R6: `settled`, `repeats`, `untouched`; carry of pre-existing lines.
- R7: an exhausted run's decision without ESCALATE or the section stops.
- R8, R9: no list → full; list, no hit → light with `[light]`; a hit → full; a full round then no
  hit stays full; deepened `missing`; the list read from the base branch, not the worktree; the
  `risk_paths` copy equals `sdlc.py`'s.
- R10, R11: `[light]` defaults and warnings; `max_runs`; the question's two forms.
- R12: pinned regex names; `_factory_files` `dropped`; `Sdlc-Review` `dropped=`.
- R13: ship Step 0 names `verified.md`.
- R14, R15: read at ship.

## Rollback

`git revert` of the ship commit. Nothing outside the repo: the factory writes only change folders,
and `Sdlc-Review` lines written with `dropped=` meanwhile read fine in older code. Seeds -9 to -11
would be refiled by hand (`/sdlc:idea`).
