---
id: 153
slug: risky-code-in-its-own-modules
tier: 2
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-43
depends_on: [147, 149, 150, 151, 154, 156]
serves: [O6]
---

# 153 — Close, push, the lock and the landing live in modules the deep review can name

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The deep review is chosen by path: a diff touching a `[review] sensitive` path runs full depth with
the security reviewer, anything else may run light. The code where a mistake costs most lives in the
two files every change touches: close, push and the main lock in `scripts/sdlc.py`, and the landing
and train in `plugins/factory/scripts/factory.py`. Listing those files would make nearly every run
full depth (60 and 50 commits this month), so they aren't listed. In the seed's words:
"139-landing-train rewrote close's lock and the landing at light depth with no security review";
on 2026-11-18 so did 144's records fix and 147's unattended loop, both of which change what the
landing commits and pushes.

## Outcome

- Close, push and the main lock move out of `sdlc.py` into a module of their own, and the landing
  and train out of `factory.py` into another, each loaded by path as `retro.py` and `board.py` are,
  with its docstring as its contract. Behaviour is unchanged: the whole suite passes before and
  after, and no command's output moves.
- Both modules are listed in `[review] sensitive`, so a later change touching them runs full depth
  with the security reviewer, while a change elsewhere in `sdlc.py` or `factory.py` stays light.
- This change's own run is reviewed at full depth: `[review]` is read from the base branch, so the
  new paths are listed there before it builds, or its run is chosen some other way the spec says.
- A test changes a line in each new module and finds `verdicts` choosing full depth; another
  changes a line elsewhere in `sdlc.py` and finds it light.
- **Moves O6:** the factory's riskiest code is always reviewed in depth, so its autonomy elsewhere
  is trusted for the right reason.

## Affected

`scripts/sdlc.py` (`cmd_close()`, `_push()`, `_push_plan()`, `_main_lock()` and their helpers),
`plugins/factory/scripts/factory.py` (`cmd_land()`, `cmd_train()`, `cmd_resolve()` and theirs), two
new modules beside them, `.sdlc/config.toml`'s `[review] sensitive`, AGENTS.md's map (*Closing*,
*Modules loaded by path*, *The factory*) and CONTRIBUTING.md, and the tests that load these
functions through `sdlc.py`'s or `factory.py`'s namespace. Every host runs this code at every close
and factory landing. It waits on 147, 149, 150 and 151, which edit the same code, so the move is
made on quiet files; the seed also says to open it after the release.

## Constraints

- A move only: no behaviour, output, trailer or command changes; anything that would change one is
  a change of its own.
- The invariants the moved code holds stay exactly as they are: only `_push()` pushes, behind its
  question; close holds `_main_lock()` from its merge to its `Close` commit; `factory.py` never
  imports `sdlc.py`; the pinned copies stay pinned; `test_only_the_named_steps_push` still finds the
  one push.
- Loaded by path, never imported, as the other modules are: the tests and `uv run --script` put
  different directories on `sys.path`; a test's stand-in for an `sdlc.<name>` still reaches the moved
  code, as `retro.py`'s and `board.py`'s do.
- The modules run on Windows as the scripts do.

## Open questions

- ~~How does this change's own run get full depth: a small commit listing the new paths on `main`
  first, or a way for a person to ask a run for full depth?~~ Resolved: the listing on `main` first
  (158), so the diff that creates both modules runs full (spec R10, R11).
- ~~Where does the line fall: which helpers move with close and the landing, and which stay shared in
  the scripts?~~ Resolved: by a rule a test holds, a helper moves only when moved code alone calls it
  (spec R3).
- ~~One module per script, or more (`close.py`, `push.py`, `lock.py` from `sdlc.py`; `landing.py` from
  `factory.py`)?~~ Resolved: one per script, `closing.py` and `landing.py` (spec R1, R2).
- Does it wait for the release, as the seed says, so the move lands on a released base?
