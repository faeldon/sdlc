---
id: 161
slug: function-heat
tier: 1
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O4]
---

# Retro sees which functions are hotspots

## Problem

The retrospective's architecture pass reads hotspots by file only (`architecture.hotspots`), so
it can say `factory.py` was touched by 23 of the last 30 changes but not which part of it. On
2026-11-18 the function-level ranking was worked out by hand with a one-off script (commits per
function since the last retrospective, from `git blame`, with each function's size from Python's
`ast`), and it found the real candidates: both scripts' `main`, `_task_prompt`, `_land_task`, the
factory's run loop and `cmd_close`. `docs/RETRO-SCORECARD.md` makes this the Quality pillar's
structural debt index (S7), and `retro.indicators` is the hook meant for it, but this repo has
never set one, so every retrospective's `architecture.host` is empty.

## Outcome

- `.sdlc/function-heat.py` (PEP 723, stdlib only) prints, for each top-level function in
  `scripts/sdlc.py`, `scripts/closing.py`, `plugins/factory/scripts/factory.py` and
  `plugins/factory/scripts/landing.py`, how many commits since the last retrospective rewrote some
  of it, and its size, ranked by commits then size, top 15 a file, as a plain-text table.
- "Since the last retrospective" is the newest `Retrospective YYYY-MM-DD` commit on the base
  branch, the same boundary `sdlc.py retro` uses; with none, the whole history.
- `.sdlc/config.toml` sets `retro.indicators` to run it, and `sdlc.py retro` from the main
  checkout shows its table under `architecture.host`, exit 0, well inside the 60-second limit
  `retro.evidence` commands have.
- It reads files as of the base branch, so running it from any checkout gives the same answer,
  and it writes nothing.
- **Moves O4:** the next retrospective's architecture findings name functions, with the commits
  and size behind each, rather than whole files.

## Affected

`.sdlc/function-heat.py` (new) and `.sdlc/config.toml`'s `[retro]`. Read only by `sdlc.py retro`
at a retrospective, through the existing indicators hook. Nothing a host has changes: it is this
repo's own indicator, and the core stays language-neutral.

## Constraints

- No change to `scripts/` or the core: the hook already passes a command's output through.
- It runs under `sh -c` from the repo root, as every retro command does, and on Windows.
- It cites no machine path (`test_nothing_local`), and prints only function names and numbers.

## Open questions

- Whether to rank by commits × size or by commits alone with size beside it. The hand-run
  analysis ranked by commits, then size.
- The output's shape: S8 later asks for structured rows (JSON). Plain text now and JSON in S8, or
  JSON from the start?

## Approach

Write `.sdlc/function-heat.py`: find the boundary commit with `git log --grep`, then for each of
the four files, `git show <base>:<file>`, parse it with `ast` for top-level functions' line
ranges, run `git blame --line-porcelain <base> -- <file>`, and count the distinct commits after
the boundary within each range. Set it in `.sdlc/config.toml`'s `[retro] indicators`, with a
comment, and take nit 2026-11-18-102 (split the `[review]` comment into a sentence per group)
in the same edit. Check with `sdlc.py retro` that `architecture.host` holds the table, and run
`./check.sh`.
