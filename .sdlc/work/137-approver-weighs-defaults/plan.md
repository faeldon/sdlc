---
id: 137
slug: approver-weighs-defaults
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 137 — The approver weighs the defaults it can, and the person decides the rest one at a time, with the alternatives in view · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`:
  - new `OPTION_RE`, `WHY_RE`, `SETTLED`, `SETTLED_RE`, `ESCALATED_RE`, `KEPT_ANSWER`.
  - `read_ledger()` gains `options`, `why`, `settled` (sub-lines attached to the line above;
    the settled mark partitioned off like `SUPERSEDED`).
  - `raised_decisions()` returns each raise's sub-lines too (a 4-tuple).
  - `cmd_decisions()` writes sub-lines, fills a bare line once, marks `SETTLED` from the current
    `decision.md` only, reports `settled`, `unsettled`, `bare`.
  - `_task()`'s `approve` prompt names every open default and both line shapes.
  - `land_parts()` (`assumed` by `open`, new `settled`), `land_shown()` (its own heading),
    `land_signals()` (open-only predicate, new settled signal). `_dispose()` is unchanged: it
    matches unticked lines only.
  - new `cmd_ask()` and its `ask` subparser; the docstring's usage and *Decisions* paragraph.
  - Reused: `find_change()`, `read_ledger()`, `frontmatter()`, `read_decision()`'s file, `emit()`,
    `_supersede_refusal()`'s shape for `_settle_refusal()`.
- `scripts/sdlc.py`: `FACTORY_SETTLED`; `factory_reading()` leaves settled lines out of
  `ledger_lines`; `_factory_files()` counts `defaults_settled`.
- `scripts/board.py`: `SETTLED`, the reader leaves settled lines out of `ledger_lines`.
- `scripts/metrics.py`: `rework()` writes `defaults_settled` when the factory gave it; docstring.
- `plugins/factory/agents/approver.md`: weigh each open default (`SETTLED`/`ESCALATED`), what it
  may never settle, a settled line is not the person's, an earlier approver's settlement.
- `plugins/factory/agents/builder.md`, `reviewer-{code,security,ui,ux,test,behaviour}.md`: the
  `OPTION`/`WHY` sub-lines with an example.
- `plugins/factory/skills/decide/SKILL.md` (new): `/sdlc-factory:decide NNN`.
- `plugins/factory/skills/build/SKILL.md`: the approver sentence, Step 1's restart and Step 4's
  report name settled lines apart.
- `skills/ship/factory.md`: Step 0 and Step 4 show settled lines apart, open defaults with options.
- Docs: `plugins/factory/README.md`, `docs/REFERENCE.md` (needs paragraph), `AGENTS.md` (writing
  skills list gains the factory's `decide`).
- Tests: `tests/test_factory.py` (ledger, settlements, approve prompt, `ask`),
  `tests/test_land.py` (R8 and R9 run a real landing there, beside the other `_ready` tests),
  `tests/test_skills.py`, `tests/test_metrics.py`, `tests/test_board.py`, `tests/test_sdlc.py`
  (`factory_reading`), and `tests/test_archive.py`, whose close-trailer test now expects
  `defaults_settled=0` on a factory change: a count taken, so a true zero, while a change built
  by hand still has no key.
- As built: `read_ledger()`'s sub-lines come from `sub_lines()` and are written by `sub_text()`;
  the approver's lines are read by `approver_weighing()`, refused by `_settle_refusal()`, and asked
  for by `weigh_text()`; `ask`'s `reply` comes from `reply_path()`. The skill's dialogs live in
  `plugins/factory/skills/decide/SKILL.md` alone, with no side file.

- Round 1's rework: `sdlc.py`'s `decide_step()` names `/sdlc-factory:decide NNN` for an
  escalation at `test` that still holds a decision or a default. Status ends that change's
  `■ What needs me` line with it, and `board.py`'s `next_action()` makes it the card's next step,
  before ship or land. `needs_of()`'s texts are unchanged. The decide skill's Step 0 says what to
  do instead when `ask` refuses. Tests: the board's precedence table and `test_status_ends_with_what_needs_me`,
  plus `test_decide_says_what_to_do_instead_when_ask_refuses`.

## Work order

1. **Alternatives in the ledger** (R1–R3). `OPTION_RE`/`WHY_RE`; `raised_decisions()` collects
   the run of sub-lines after each `DECISION`; `cmd_decisions()` writes them indented, and fills
   a bare line once; `read_ledger()` reads `options`/`why`. Tests first; the pinned readers in
   `sdlc.py` and `board.py` already skip indented lines, proved by the not-garbled tests.
2. **The approver's settlements** (R5–R7). `SETTLED`, `SETTLED_RE`, `ESCALATED_RE`;
   `cmd_decisions()` reads the current `decision.md`, ticks settled defaults, fills an escalated
   bare line's options, reports `settled`/`unsettled`/`bare`; `read_ledger()` reads `settled`;
   the approve prompt; `approver.md`. `decided` already refuses a non-decided line.
3. **The landing** (R8, R9). `land_parts`, `land_shown`, `land_signals`.
4. **Status, board, metrics** (R10, R11). The `SETTLED` copies, their pins, `ledger_lines`, and
   `defaults_settled`.
5. **`ask`** (R13, R14). Read-only command, refusals, `next`.
6. **Prompts and skills** (R4, R12, R15, R16). Agent prompts, ship's `factory.md`, the build
   skill, the new `decide` skill, `GATED`/`READS_CONFIG`/`test_skills_were_found`.
7. **Docs** (R17), then `./check.sh`.

## Tests

- R1: `test_a_defaults_alternatives_reach_the_ledger_under_its_line` (test_factory).
- R2: `test_a_ledger_without_alternatives_reads_as_before` (test_factory);
  `test_a_ledger_with_alternatives_is_not_garbled` (test_sdlc via `factory_reading`, test_board).
- R3: `test_options_fill_a_bare_line_once` (test_factory), bytes equal after a second run, and the
  approver's ESCALATED options filling a bare line.
- R4: `test_agents_give_a_defaults_alternatives` (test_skills).
- R5: `test_the_approver_is_asked_to_weigh_each_open_default` (test_factory, on `_task`'s
  prompt); `test_the_build_session_brings_the_persons_decisions_to_them` updated.
- R6: `test_the_approver_settles_one_default_and_escalates_another`;
  `test_a_settle_that_cant_apply_marks_nothing` over blocking, decided, superseded, unknown.
- R7: `test_a_settled_default_is_not_the_persons_word` (assumed, `decided` refused, upgrade).
- R8: `test_the_landing_shows_settled_defaults_apart_and_never_confirms_them`; the superseded test
  gains its land_parts assertion.
- R9: `test_a_settled_default_keeps_the_batch_from_passing_itself`.
- R10: `test_an_escalation_with_only_settled_defaults_is_not_answered` (test_sdlc, test_board);
  the `SETTLED` pins.
- R11: `test_a_settled_default_is_counted_apart` (test_metrics); the absent-never-zero test.
- R12: `test_ship_shows_settled_defaults_apart` (test_skills).
- R13: `test_ask_lists_open_items_with_their_background_and_writes_nothing`,
  `test_ask_refuses_a_change_not_at_test`.
- R14: `test_ask_says_rebuild_when_an_answer_overturns_a_default`,
  `test_ask_says_ship_when_every_default_is_kept`, and an undecided id refused.
- R15: `GATED`, `READS_CONFIG`, `test_skills_were_found`; `test_decide_writes_answers_only_after_its_wait`,
  `test_decide_never_takes_words_on_a_command_line`.
- R16: the existing supervisor tests, unedited but for R5's assertion.
- R17: read by the reviewers; the docs are prose.

## Rollback

`git revert` undoes everything: the change writes nothing outside the repo. Ledgers written by a
run while this change was in place keep their indented sub-lines and `→ settled by the approver:`
marks; the old readers skip the sub-lines (they never match `LEDGER_RE` nor start `- [ ]`), and
read a settled line as a ticked one, which is what a revert would leave. `Sdlc-Rework` trailers
already written with `defaults_settled=` stay in history; the old parser ignores an unknown key.
