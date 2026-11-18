---
id: 144
slug: factory-records-and-models
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on: [140]
fixes: [2026-11-18-41, 2026-11-18-42]
serves: [O6]
---

# 144 — The factory reads its models from the base branch, and files a change's own folder by its full name

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two bugs in how `factory.py` reads and writes its own records, both found on 2026-11-18:

- 2026-11-18-41: "factory.py reads [models] from the change's own worktree, while mode, [land],
  [ui] and gate_jobs come from the base branch (`_base_factory()`): a change only gets a [models]
  setting committed on main once its branch includes it, and a change can pick its own agents'
  models by editing its own .sdlc/factory.toml. Seen 2026-11-18: builder = "claude-fable-5-1"
  committed on main (329748d) left 140's and 143's builders on Opus."
- 2026-11-18-42: "An agent's record can cite a change by its bare number and fail the gate: 140's
  behaviour check ran `ls` on its own folder as a glob, `.sdlc/work/NNN*/…` with the number in
  place of NNN, and filed it in its ## Evidence, which matches test_nothing_local's
  `work/\d{3,}\b(?!-)` rule; the approver's decision and the code and test reviews then quoted
  the same glob while describing the failure, so the record kept re-committing it (2026-11-18, 7
  lines in 4 files fixed by hand). The gate ran before the behaviour check wrote it, so only the
  reviewers' own suite runs saw it."

## Outcome

- `[models]` is read from the base branch's `.sdlc/factory.toml`, as `mode` is. A test commits a
  `[models]` entry on the base branch only, and finds it in `start`'s `models_at` and in the model
  `agent` runs for a change whose worktree predates it; a `[models]` entry in the change's own
  checkout changes nothing.
- When `factory.py agent` files any agent's reply, a citation of the change's own folder by bare
  number or glob (`work/NNN*`, `work/NNN/`, `work/NNN` with no slug) is written as its full
  `NNN-slug`, beside `_placeholders()`'s path marks. A test files a reply citing the change that
  way and finds `test_nothing_local`'s patterns pass over the filed file.
- **Moves O6:** a factory run's records never fail the repo's own gate over how an agent wrote a
  path, and the repo's model settings reach every change the same way.

## Affected

`plugins/factory/scripts/factory.py` (`load_config()`'s `[models]`, `_placeholders()` or the step
that files a reply in `cmd_agent`), `plugins/factory/README.md` (where `[models]` is read from),
and `tests/test_factory.py`. Every factory host's runs. It waits on 140, which rewrites
`cmd_agent`'s reply filing, so it is built on 140's code.

## Constraints

- A change can't choose or loosen its own run's settings: what shapes a run is read from the base
  branch.
- Only the script rewrites what it files, and only marks and names, never an agent's verdict or
  finding.
- No other change's number is rewritten, only the change's own.

## Open questions

- Should a `[models]` entry in the change's own checkout warn, as a changed `mode` does, or be
  ignored silently?

## Approach

For 2026-11-18-41, read `[models]` through `_base_factory()` in `load_config()`, with the warning
`mode` already gives when the checkout's value differs. For 2026-11-18-42, extend the filing step
(`_placeholders()`, or a sibling beside it in `cmd_agent` on 140's code) to replace `work/<the
change's number>` not followed by `-`, glob or not, with `work/<NNN-slug>`. Say in the README that
`[models]` is the base branch's. A test for each.
