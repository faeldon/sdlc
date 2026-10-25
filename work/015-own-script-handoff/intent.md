---
id: 015
slug: own-script-handoff
tier: 2
impact: none
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea:
depends_on:
serves: none
---

# 015 — Write stages run the change's own script in the plugin's repo

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In this repo every skill runs `sdlc.py` from `${CLAUDE_PLUGIN_ROOT}`: the clone's main checkout.
While a change is open its new code is in its worktree, not on `main`, so the stages that write
run `main`'s old copy, not the change's. 014's ship showed it: `sdlc.py ship 014` ran `main`'s
script, which stamped the change and did nothing else (no seed deleted, nothing staged), without
refusing. It was caught only by reading the output, and fixed by rerunning the worktree's
`scripts/sdlc.py ship 014` by hand.

So a change to `cmd_ship`, `cmd_drop`, `cmd_base` or `cmd_sync` is never run by its own code before
it lands, while a change to close is, through `_handoff()`, which re-runs close with the merged
code (how 013's own close was the first to report `reaches`). Today `_handoff()` is close's alone
(`HANDOFF_ENV = "SDLC_CLOSE_RAN"`).

## Outcome

- In the plugin's own repo only (`_own_repo()`), a command that writes, run from a change's
  worktree whose `scripts/sdlc.py` differs from the running copy, re-runs through the worktree's
  script, and its output and exit code are the command's: at least `ship`, `drop`, `base` and
  `sync`, the list settled in the spec.
- Its output says which code ran, as close's `ran` does, so a report can say "the change's own
  code".
- Close's own handoff stays as it is and never loops with the new one.
- In a host, nothing changes: no handoff, no new output, no new refusal, proven by a test as
  `test_a_host_repo_never_hands_off` proves it for close.
- Tests: a change to `cmd_ship` in a scratch plugin repo ships through its own code; a worktree
  script identical to the running one doesn't hand off; a host never does; a second handoff never
  happens.

## Affected

- **Area:** the script's entry point and the writing commands; close's handoff
- **Files & components:** `scripts/sdlc.py` (`_handoff()` generalised or a sibling, the dispatch in
  `main()`, `HANDOFF_ENV`), `tests/test_archive.py` (handoff tests), `tests/test_sdlc.py`; possibly
  `docs/CONTRIBUTING.md` ("When a change lands") and `AGENTS.md`'s close paragraph
- **Downstream:** the person developing the plugin, in this repo's change worktrees. Hosts are
  untouched by design.
- **Contracts:** "logic a permission rule must cover goes in the script": the handoff runs inside
  `sdlc.py`, so no skill gains a command or a rule. "Only publish pushes" untouched. Close's step
  order and its stale-copy handoff kept.

## Constraints

- Hosts never hand off: `_own_repo()` reads the repo's own files, never where the script was
  loaded from, so a host can't be taken for the plugin.
- A broken script in a change must not block a stage it didn't need to touch: a worktree whose
  `sdlc.py` doesn't even start shouldn't strand the person mid-ship with no way through.
- No loops: one handoff per command, guarded as `SDLC_CLOSE_RAN` guards close.
- No new writes before a WAIT: the handoff changes which code runs a write, not when it runs.

## Open questions

- ~~When the worktree's script is broken, refuse, fall back, or offer an opt-out?~~ Resolved:
  a crash (a traceback, or `uv` failing before it runs) falls back to the running copy with a
  warning, a clean refusal stands, and `SDLC_OWN_SCRIPT=off` gets past a script that runs but is
  wrong. Falling back is safe because all four commands are rerun-safe.
- ~~Which commands hand off?~~ Resolved: the ones that write from a change's worktree, `ship`,
  `drop`, `base` and `sync`; readers and `accept` don't, since the gate already runs the
  worktree's tests, and close keeps its own.
- ~~What counts as "differs"?~~ Resolved: the change edited `scripts/` (against its merge base with
  `main`, committed, uncommitted or untracked), which covers `trackers/` and `metrics.py`. A plain
  comparison would hand off to older code once `main` moves ahead.
- ~~Is the script handoff enough, given skill text can't hand off?~~ Deferred: CONTRIBUTING's
  "When a change lands" already says to `/reload-plugins`; a warning when a change edits the skill
  being run is a later seed.
- ~~Does close's handoff move into the shared mechanism?~~ Resolved: no; the two share only how a
  script is invoked, so close's tested path doesn't move.
