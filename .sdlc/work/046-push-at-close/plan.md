---
id: 046
slug: push-at-close
kind: plan
created: 2026-11-09
updated: 2026-11-09
---

# 046 — Close and release push behind their own approval, and status nudges unpushed work · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `CONFIG_KEYS["git"]` gains `push` and `nudge_after_changes`; `load_config()`
  validates `push`, `_resolve_docs()` resolves its default from `archive.target`; `_push()`,
  `_pushed()` and `_unpushed()` beside `_remote_sha()`; `cmd_publish` uses them and drops its
  moved-past refusal once the tag is on the remote; `cmd_release` pushes after `tag`; `cmd_close`
  reports `push` at `--check`, pushes after `delete branch`, and carries the nudge when it doesn't;
  `print_status` prints `■ Unpushed`.
- `skills/close/SKILL.md`, `skills/release/SKILL.md`, `skills/publish/SKILL.md`,
  `skills/status/SKILL.md`: questions, reports and precedence (R10); release's long lines (R12).
- `tests/test_push.py` (new): R1–R9 against a bare `origin`.
- `tests/test_skills.py`: `test_only_publish_pushes` becomes the `_push()` callers test (R7).
- `tests/test_release.py`: the moved-past test keeps its refusal only while the tag is unpushed.
- `tests/test_config_resolution.py`: the `git` section's expected defaults.
- `AGENTS.md`, `docs/REFERENCE.md`, `guide/process.md`, `README.md` (R11); `.sdlc/setup.json` by
  `record`.

## Work order

1. Config keys, validation and default; config tests.
2. `_push`/`_pushed`/`_unpushed`; publish on them, with the tag-on-remote branch; publish tests.
3. Release's push; close's plan, push step and nudge; their tests.
4. Status's `Unpushed`; its tests.
5. Skills, the push test in `test_skills.py`, docs, `record`, `./check.sh`.

## Tests

- R1: default `["close", "release"]` with `archive.target = "github"`, `[]` otherwise, explicit
  wins, a bad value warns.
- R2: `nudge_after_changes = 0` hides `Unpushed`.
- R3: `close --check` lists the unpushed commits and the coming `Close`, or `push_off_because`.
- R4: close with `push = ["close"]` leaves the remote at the `Close` commit; without, untouched; a
  refused push (remote moved) is exit 0 with `push_failed` and the worktree and branch gone.
- R5: release with `push = ["release"]` pushes main and the tag.
- R6: publish after a pushed tag and a later close pushes main alone; with an unpushed tag and
  main past it, still refused.
- R7: `test_skills.py` caller test.
- R8: status shows `Unpushed` with the issue a `Closes #N` names, at and past the threshold only,
  and nothing without a tracking ref.
- R9: close with push off carries `unpushed`.
- R12: no line in `skills/release/SKILL.md` past 100 characters.

## Rollback

`git revert` of the change's commit puts the code back. Pushes already made reach GitHub and stay
there: a pushed commit isn't taken back (never a force-push); the next release carries it. Hosts
reading from a clone stop pushing at their next session once reverted, or at once with
`[git] push = []`.
