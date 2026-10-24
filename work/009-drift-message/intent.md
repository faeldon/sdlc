---
id: 009
slug: drift-message
tier: 1
impact: none
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea: The drift gate's message names the right fix
depends_on:
serves: none
---

# 009 — The drift gate's message names the right fix

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

008 added `test_this_repos_setup_record_is_current` (`tests/test_defaults.py`). It fails on
anything `sdlc.py drift` reports and tells you to run `record` whatever the cause. For part of what
it catches, that advice is wrong:

- **Every `breaking` entry:** a retired config key, a template override missing what the script
  reads, a `config.toml` that won't parse, or a malformed product or project doc. `record` clears
  none of these, and each entry already carries its own `fix`.
- **Two `report` entries:** an `unknown` key in `config.toml` and an `unknown` template in
  `.sdlc/templates/`. `record` doesn't clear these either.

Someone who follows the message runs `record`, sees the test fail again, and has to read `drift`'s
JSON to find out why. It was flagged as a Nit at 008's ship and approved unfixed, so only the
`Sdlc-Findings` count on `f4bf8f0` records it.

## Outcome

- When the test fails, each line names the drifted entry and how to fix that entry. An entry with
  a `fix` shows it. One that `record` clears (a `refresh` block, a `conflict`, a `new` config key,
  a `changed` template, a `moved` doc, a `downgrade`) says to run `record` from this checkout. One
  that neither covers says what's wrong, e.g. "the plugin doesn't read it".
- The message suggests `record` only when at least one failing entry is something `record` clears.
- When nothing has drifted the test passes, and it still fails on everything it fails on today.

## Affected

- **Area:** this repo's test suite only.
- **Files & components:** `tests/test_defaults.py`, the one test and perhaps a small helper beside
  it. `drift()` is unchanged.
- **Downstream:** whoever reads a failing `./check.sh` in this repo. Hosts see nothing.
- **Contracts:** "This repo's process docs track the defaults" in AGENTS.md, whose last sentence
  (added by 008) says the gate fails while `drift` reports anything. That stays true.

## Constraints

- The test must not get narrower: anything `drift` reports still fails it.
- The test reads `drift()`'s entries as they are and doesn't redefine its classes. If which classes
  `record` clears is worth knowing outside this test, that belongs in `sdlc.py`, not in a list kept
  only here.

## Open questions

- ~~Should the test keep its own list of the classes `record` clears, or should `drift()` mark each
  entry?~~ Resolved: the test keeps it (`RECORD_CLEARS`). `/sdlc:setup` always runs `record` after
  it writes, so nothing outside this test needs the list, and a marker in `drift()` would be
  speculative. Tier 1 holds.
- ~~Does it need a negative test that builds a drifted repo?~~ Resolved: a test of the line
  builder on a made-up `drift` result (`test_drift_lines_name_each_fix`), plus the hand checks:
  a drifted default, a retired key and an unknown key, each reverted.

## Approach

Build each failure line from the entry: its `where` and `unit`, then its `fix` when it has one,
else "run `record`" for the classes `record` clears, else its `detail`. Print the `record` command
once, in the heading, only when some line needs it. Check it by hand the same way 008 did: an
edited default for a `refresh` and a `conflict`, an unknown key added to a copy of `config.toml`
for the other path, then revert.
