---
id: 204
slug: scorecard-reads-true
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 204 — The scorecard's null rows and retire list read true · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/retro.py`:
  - `_workarounds()`: the `unknown` block gets `n`, and the null-when-`n`-is-0 rule and
    `missing_because` the `outside` and `hand_record` blocks have.
  - `scorecard()`: a lead-time-by-way row whose way closed no change in the window takes the
    escape rate's reason, `no <way> change in the window`, through one helper `_no_way()` that
    `by_way()`'s `escapes()` uses too.
  - The surface: a new `_key_readers()` (cached) finds, from the code, which config keys each
    command reads by name (`_code_reads()`, an AST walk over the core's scripts and the trackers,
    following each command's calls, methods included, and a section handed to a function as an
    argument; not the factory's scripts, which read no `CONFIG_KEYS` key by name) and which keys
    each skill's files name (`section.key`). `_states()`
    then counts a key used when the config sets it or any reader of it was used in the window;
    `unused` when a reader that a record could show went unused, or nothing reads it; else
    `unmeasured`, with the readers' why. `surface()` and `_retire()` pass the readers in.
- `tests/test_retro.py`: the `unknown` block's `n`; the lead row's reason (the 184 R5 test's
  expected note changes from `none in the window` to `no factory change in the window`).
- `tests/test_surface.py`: `git.base`, `git.push` used when a command reading them ran; a key a
  command reads but whose readers weren't recorded is `unmeasured`; a key only a skill names is
  used by the skill's runs; a key nothing reads is `unused` and a retire candidate; the scan finds
  every key the code reads (none of `CONFIG_KEYS` is read by nothing).
- `docs/REFERENCE.md` (*Retrospectives*, the surface paragraph): how a key is counted used.

## Work order

1. The workarounds' `unknown` `n`: test, then the block.
2. The lead rows' reason: test, then `_no_way()` and `scorecard()`.
3. The key readers: tests on `_key_readers()` (git.base and git.push read by `ship`; a skill's
   named keys), then the scan.
4. The key states: tests on `surface()` (used by a reader's run, unmeasured, unused, retire),
   then `_states()` and its callers; the docs paragraph.

## Tests

- Outcome 1: `test_retro.py`, the workarounds tests assert `unknown`'s `n` and null count.
- Outcome 2: `test_a_figure_with_no_data_reads_a_dash_with_its_reason` reads the way's reason.
- Outcome 3: `test_surface.py`, the key tests above; `test_every_key_has_a_reader` pins that the
  scan reaches every key the code holds.

## Rollback

`git revert` undoes it all: `retro` is read-only but for its report, and a report already
committed keeps the figures it had.
