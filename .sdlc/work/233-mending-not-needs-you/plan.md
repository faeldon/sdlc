---
id: 233
slug: mending-not-needs-you
kind: plan
created: 2026-11-22
updated: 2026-11-22
---

# 233 — A card being mended says "mending", not "Needs you" · plan

> The Tier 1 change's plan, written by its builder after reading the code, since its Approach
> touches five files.

## Files to change

- `plugins/factory/scripts/factory.py`: `ROLE_RE` beside the step record's other regexes;
  `step_text()` writes `ROLE:` when the reading names one, `read_step()` reads it back as `role`;
  `_record_mend()` writes `runs/step.md` as `STEP: mend`, the mend's round
  (`mend_round()`), the old record's limit, reviewers and depth kept, `ROLE:` and a fresh `SINCE:`;
  `cmd_agent()` calls it for `--task mend` once nothing is left to refuse, before the session
  starts (where `_record_land()` is called for a landing task), and a session that fails puts
  the record back as it was (`_unrecord_mend()`), so no card says `mending` while nothing runs.
  `runs/stopped.md` is untouched: only `verdicts --record` writes or removes it, and its next
  reading rewrites `step.md` too.
- `scripts/factory_records.py`: `ROLE_RE` copy, `read_step()` reads `role`; `mending(folder)`
  (new) returns the mend `runs/step.md` names, `{"role", "round", "since", "deadline"}`, the
  deadline `since + AGENT_TIMEOUT` as a stamp, or None for any other step, no record or one
  without a `SINCE:`.
- `scripts/sdlc.py`: `mend_running(rec)` (new, beside `needs_of()`): the record's `mending` while
  its stop's way is `mend` and `now` is before its deadline, else None. `needs_of()` skips the
  stop's need while a mend runs, and names a mend past its deadline in its own words, no comma
  (`stopped: mending the <role> since <HH:MM> with no reply: rerun /sdlc-factory:build <id> if no
  session runs it`). `status` reads `mending` beside `stopped`, and its line says `mending, `
  rather than `stopped, `, and its `→` line that the factory is mending the role.
- `scripts/board.py`: `_entry()` reads `mending` beside `stopped`; `_progress()` shows a running
  mend's track instead of hiding it (`_mend_progress()`, new): the mended role's position
  (`MEND_AT`: the builder at `build` in round 1 and `rework` after, the arbiter at `arbitrate`,
  the approver at `approve`, a reviewer at `review`), labelled `mending <role>`, elapsed time and
  no typical figure (open-ended, as the landing's mend is); `next_action()` says the factory is
  mending it.
- `scripts/board.html`: a card being mended flags the stop's problems as `mending: `, not
  `stopped: `.
- `tests/test_board.py`: the three cases on the board and in `status`, the pinned copy of the
  step record (`ROLE_RE`, a record with `role`), `mending()`'s reading, and the keys a `status`
  record gains (`mending`, `mend_running`).
- `tests/test_sdlc.py`: `needs_of()` over the three cases.
- `tests/test_factory_agent.py`: `agent --task mend` writes the step before its session runs; a
  refused mend writes nothing; a failed one puts the record back.
- `tests/test_modules.py`: `ROLE_RE` and `mending` in `RECORD_NAMES`; `mend_running` in
  `CONSUMER_NAMES`.
- `plugins/factory/README.md`: the `stop` row of the step table and the `runs/step.md` line;
  `docs/REFERENCE.md`'s step-track paragraph; the docstrings naming who writes `runs/step.md`.

## Work order

1. The record: `ROLE_RE`, `step_text()`/`read_step()` with `role` in both scripts, the pinned
   copy test extended; `factory_records.mending()`.
2. The factory writes it: `_record_mend()` in `cmd_agent()`, its test (a fake `claude` that reads
   `runs/step.md` as it runs, as the existing agent tests fake it).
3. The rule: `mend_running()` and `needs_of()`, the three cases tested on bare records.
4. The readers: board (`_entry()`, `_progress()`, `next_action()`) and `status`, each case tested
   on a repo fixture.

## Tests

- Mend under way: `needs_of()` names nothing for a `mend` stop with a `mending` record before its
  deadline; the board's card is Building with a `mending builder` current step; `status` lists it
  under Building.
- Mend used up: a `rerun` stop with a `mending` record still needs `stopped: fix its cause and
  rerun`; the card is Needs you with no track.
- Mend left past its timeout: `needs_of()` names the mend and its rerun; the card and `status`
  are Needs you.
- `agent --task mend` writes `STEP: mend`, `ROLE:` and `SINCE:` before the session starts; a
  refused mend, or one whose session fails, leaves the record as it was.
- The board's `read_step()` and `ROLE_RE` are `factory.py`'s (pinned).

## Rollback

`git revert` undoes it all. A `runs/step.md` written as `STEP: mend` by this version is read by an
older board as an unknown step (no track, as a stop today), and the next `verdicts --record`
rewrites it, so nothing outlives the revert.
