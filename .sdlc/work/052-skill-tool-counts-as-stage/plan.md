---
id: 052
slug: skill-tool-counts-as-stage
kind: plan
created: 2026-11-12
updated: 2026-11-12
---

# 052 — A skill started through the Skill tool counts as its stage · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/metrics.py`: `PLUGIN_SKILL`, shared by `SKILL_RE` and a new `SKILL_NAME_RE`;
  `read_events()` remembers the person's last message and reads a `Skill` tool call; `_started()`
  (new) turns that call into the `skill` event a typed command makes.
- `tests/test_metrics.py`: three tests beside the stage tests.
- `.sdlc/work/052-skill-tool-counts-as-stage/intent.md`: open questions struck.

## Work order

1. The tests, failing on today's `metrics.py` (the two that open a stage).
2. `_started()` and its call; the tests pass.
3. Measure 051's real transcript with `main`'s `metrics.py` and the change's; then `./check.sh`.

## Tests

- `test_a_skill_the_session_starts_counts_as_typed`: ` /sdlc:ship` as text plus a Skill call
  gives the same segments, coverage, stops, `ship_runs` and no extra stop, as the typed command.
- `test_a_typed_command_and_its_skill_call_count_once`: one `skill` event, not two.
- `test_a_skill_started_unasked_opens_at_its_call`: no mention opens the stage at the call; a
  non-plugin skill (`simplify`) opens nothing.
- Manual, done: 051's own transcript reads `stages=intent,build,ship,close ship_runs 1` and one
  gate a stage, against `main`'s `stages=intent,build,close ship_runs 0`.

## Rollback

`git revert <sha>`. It does not rewrite the trailers already on `Close` commits measured with the
old reader (051's among them): history keeps what was measured then.
