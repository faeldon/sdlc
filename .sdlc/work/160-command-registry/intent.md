---
id: 160
slug: command-registry
tier: 2
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: none
---

# Each command registers itself, so adding one doesn't edit main

## Problem

`scripts/sdlc.py`'s `main` (476 lines) and `plugins/factory/scripts/factory.py`'s `main` (184
lines) build every subcommand's argparse parser and route it, by hand, in one function each. They
are the most-rewritten functions in both scripts: 13 and 22 changes rewrote them in the window
before the retrospective of 2026-11-18. Every change that adds or alters a command edits the same
few hundred lines, so changes built in parallel conflict there when they land as a train, and
every diff to a command carries an unrelated edit to `main`. `docs/RETRO-SCORECARD.md` ranks it
first among the refactors (R1), and the waves plan lands it before anything else, so later
changes stop meeting it.

## Outcome

- Each command in both scripts declares its own parser (name, help, arguments) and its handler in
  one place beside the handler, and `main` builds the parsers from that registry and dispatches,
  with no per-command code of its own.
- A pure move: for every command in both scripts, `--help`, flags, defaults, output and exit
  codes are byte-identical before and after (compared from a checkout of the base), and the whole
  suite passes with tests changed only in how they reach a moved name.
- `READ_ONLY` and `ALLOW_RULES` still cover exactly the same commands, and `test_skills.py`'s
  rule checks pass unchanged.
- The commands that live in `scripts/closing.py` and `plugins/factory/scripts/landing.py`
  (`close`; `land`, `land-check`, `train`, `resolve`, `land-verdicts`) are still routed to those
  modules, which stay loaded by path, never imported.
- A test fails if a command's parser is built outside the registry, so `main` doesn't grow back.

## Affected

`scripts/sdlc.py` and `plugins/factory/scripts/factory.py` (`main` and each command's
definition), possibly `scripts/closing.py` and `plugins/factory/scripts/landing.py` where their
commands register, and the tests that build a parser or check rules (`tests/test_skills.py`,
`tests/test_sdlc.py`, `tests/test_factory.py`). Every skill runs these commands, but nothing a
skill or a host sees may change. `closing.py` and `landing.py` are listed in `[review] sensitive`,
so if the diff touches them, the run is reviewed at full depth.

## Constraints

- Nothing a command does or prints changes. No new command, flag, default or alias, and no shim.
- Modules stay loaded by path and bound live (*Modules loaded by path*); `factory.py` never
  imports `sdlc.py`.
- `sdlc.py`'s one git push stays in `closing.py`'s `_push()`, and its callers stay the same
  (`test_only_the_named_steps_push`).
- The scripts run on Windows (`tests/test_windows.py`).
- `board` stays out of `READ_ONLY` and `ALLOW_RULES`; `run-cases` stays out of `ALLOW_RULES`.

## Open questions

- ~~The registry's shape: a decorator on each handler, a table of entries, or each module
  exporting its commands. Which keeps `--help`'s order and grouping identical most simply?~~
  Resolved: a `@command` decorator on a `cli_<name>` adapter beside each handler, with
  `HELP_ORDER` pinning today's top-level order (spec R1, R2, R11).
- ~~Whether `closing.py` and `landing.py` register their own commands, or the scripts keep
  registering them on the modules' behalf, so the sensitive modules aren't touched.~~ Resolved:
  the scripts register them; the modules stay out of the diff (spec R8).
- ~~Whether `READ_ONLY` and `ALLOW_RULES` are derived from the registry (one place) or kept as they
  are and checked against it.~~ Resolved: kept as they are and checked against the registry
  (spec R9).
