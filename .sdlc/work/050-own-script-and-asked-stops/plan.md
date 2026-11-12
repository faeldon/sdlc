---
id: 050
slug: own-script-and-asked-stops
kind: plan
created: 2026-11-12
updated: 2026-11-12
---

# 050 — Count ship's own questions as asked, and hand a change's own script every command ship runs · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `OWN_SCRIPT_CMDS` gains `preflight` and `findings`; `main()` hands off before
  `parse_args`; `_run_own()` puts a text report's `ran` line on stderr for `preflight`; `preflight`
  refuses its question flags without `--question` (nit 2026-10-27-6).
- `scripts/metrics.py`: `_ends_with_question()` for `asked`; `_harness()`, used by `read_events`
  and `_membership()`.
- `AGENTS.md`, `docs/CONTRIBUTING.md`: the handed-off commands, and the handoff before parsing.
- `tests/test_archive.py`, `tests/test_metrics.py`, `tests/test_preflight.py`.

## Work order

1. Handoff before parsing, the two commands added, `preflight`'s `ran` line on stderr; tests.
2. `preflight` refuses its question flags without `--question`; test.
3. `_ends_with_question()`; tests, with 049's two questions.
4. `_harness()` in `read_events` and `_membership()`; tests.
5. Docs; `./check.sh`.

## Tests

- 2026-11-12-3: `main()` hands `ship 001 --fixed F1 --through F1` off with the raw argv, never
  exiting on the unknown flags; `preflight` and `findings` hand off; `status` doesn't; `preflight`'s
  text report keeps stdout to the question.
- 2026-11-12-4: `_ends_with_question` cases; an answer to `…? (yes / edit the message)` before the
  gate counts `asked`.
- 2026-11-10-3: a compaction summary quoting `/sdlc:intent`, and a task notice quoting
  `/sdlc:close`, move no membership.
- Nit 2026-10-27-6: `preflight 001 --closing 5` exits 1 and prints no JSON.

## Rollback

`git revert <sha>` undoes it all. `Close` commits measured meanwhile keep their counts (more
`asked`, fewer `unprompted`, membership without harness entries); a revert doesn't re-measure them.
