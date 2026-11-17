---
id: 111
slug: factory-loose-ends
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 111 — Close four small gaps in the factory · plan

> Written by the factory's builder after reading the code. A Tier 1 change, so the intent's
> Approach is the spec; this plan exists because the Approach touches six files.

## Files to change

- `plugins/factory/scripts/factory.py`: `shots()` starts the dev server up to `SERVE_TRIES` (3)
  times, each on a new `_free_port()`, when the port was lost to another process: something already
  answers on it before the serve starts, or the server has exited and the port won't bind. Only a
  port that won't bind is lost, for every way the server ends (exited before answering, or
  answered and then exited): `_up()` has one exit for an ended server, and it asks one helper,
  `_lost()` (`not _binds()`), so no branch decides on its own. `_binds()` sets `SO_REUSEADDR`
  (not on Windows, where it would bind over a held port), so a port left in TIME_WAIT by a
  connection the server closed first reads as free, not held. A port that binds means the server
  failed on its own, started once. Each lost try is recorded in `shots.json`'s `retries`
  (`port`, `why`); a timeout or a serve that can't start is not retried. The fixture copy is made
  afresh for each try (`_fixture_copy()`, reused), since a server may have written into the last.
- `plugins/factory/scripts/factory.py`: `_resolve()` takes the round's label, not its number;
  `read_verified()` words it from the folder of the file it reads: `land-<n>` for
  `reviews/land-<n>/`, `round <n>` otherwise.
- `plugins/factory/skills/spec/SKILL.md`: Step 0 runs `factory.py fresh <NNN>` after `start`
  refuses nothing, with the same rule and the same stop on a refusal as the build skill; Step 1
  shows `behind` and what `fresh` did beside the draft. `allowed-tools` gets the `fresh` rule.
- `plugins/factory/skills/build/SKILL.md`: `start`'s `ui` summary names `fixture`.
- `plugins/factory/README.md`: the UI reviewers' paragraph says a lost port is tried again; *Built
  on current code* names the spec skill's `fresh`.
- `AGENTS.md`: *Writes before a WAIT* and *The factory* name `fresh` from the spec skill too.
- `tests/test_factory.py`: the port retry; `_resolve()`'s wording for a landing round.
- `tests/test_land.py`: the landing verifier's problem names `land-1`, not `round 1`.
- `tests/test_skills.py`: the spec skill's `fresh` and the build skill's `fixture` (skill text is
  pinned where every other skill's is).

## Work order

1. `_resolve()` wording: the test in `tests/test_factory.py` and `tests/test_land.py`, then the
   label.
2. Port retry: a test that hands `shots()` a held port, then the retry loop.
3. Spec skill's `fresh`: the test in `tests/test_skills.py`, then the skill's text and rule.
4. Build skill's `fixture`: the test, then the line.

## Tests

- Landing wording: `test_a_landing_verifiers_answer_names_its_landing_round` (test_factory) and
  the land-verdicts assertion in `tests/test_land.py`.
- Port: `test_shots_take_a_new_port_when_theirs_is_lost` (a port already answering, then one
  bound but not listening, then a free one: shot on the third, two retries recorded) and the same
  with every try lost (a problem, no server left running);
  `test_a_server_that_fails_on_its_own_is_started_once` (a serve that exits without binding: one
  start, no retries, its exit the problem).
  `test_a_port_is_lost_only_when_it_wont_bind_whichever_way_the_server_ended` (round 3: `_up()`
  driven with a stub process that answered and then exited, once with the port freed, not lost,
  once with it still held, lost).
  `test_a_server_that_answered_and_closed_first_has_not_lost_its_port` (round 4: a real
  connection the server closes first leaves its port in TIME_WAIT; the server then exits, and the
  port is not lost).
- Spec `fresh`: `test_factory_spec_brings_the_change_up_to_date_before_its_spec_writer`.
- Build `fixture`: `test_build_names_every_ui_key_start_gives`.

## Rollback

`git revert` covers everything: no data written outside `.sdlc/reports/`, which ignores itself,
and no key a host writes is renamed.
