---
id: 103
slug: landing-does-what-ship-does
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 103 — The factory's landing does what ship does · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: the landing.
  - New constants beside `IMPACT_RE`: `UNDONE_RE`, `RECOVER_RE`, `CASES_RE` (copy of `sdlc.py`'s),
    `FRESH_RE` (copy), `CASE_CAP_USD = 5` (copy of `CASE_CAP["change"][1]`), `ACCEPT_FILE`.
  - `_review_list(root, base, key)`: `_sensitive()`'s body, generalised; `_sensitive()` and a new
    `_irreversible()` call it.
  - `_preflight(folder, worktree)`: the one `sdlc.py preflight` call; `land_signals()` takes its
    result (optional, so the existing caller and test still work).
  - `land_signals()`: the three exclusions become signals; the one exclusion left is an irreversible
    path with no `- RECOVER:` line (`unrecovered()`).
  - `land_parts(folder, pre)` (new): R2's `checks`, `cases`, `undone`, `assumed`, `recover`, built
    from `preflight`, `decision.md` (`read_proposals()`) and `read_ledger()`.
  - `land_question(batch, base)` (new): R3's wording; `cmd_land_check()` adds the parts to each
    entry and prints `question`.
  - `accept_path()`, `accept_build()`, `_accept_state()`, `cmd_accept()` (new): R4. `accept_build()`
    is `landed_build()` once `intent.md` is past `stage: test`, else a digest of `_tree_hashes()`
    plus `checks.md`'s hash, so the record (in the change's folder) never changes what it records.
  - `_note_line(folder, regex, line)` (new): set one line in `findings.md`'s note, creating the file
    as the landing already does; the `FRESH_SKIPPED` write uses it too, so a findings.md that
    `cases` created first still gets its `Fresh review:` line.
  - `cmd_cases()` (new): R5.
  - `_dispose(root, folder, pre)` (new): R8's writes, by line, a rerun writing nothing twice.
  - `cmd_land()`: R7's refusals, then `_dispose()`, before `_set_impact` and `ship`.
  - `land_message()`: R9's `Carried forward:`, `Dropped:` and `How to recover:` paragraphs, read
    from `notes.md`'s ticks and `decision.md`'s `- RECOVER:` lines.
  - `cmd_land_verdicts()`: R11's `next: accept`.
  - `_task(…, "approve")`: R10's irreversible paths and the `RECOVER`/`UNDONE` ask.
  - `main()`: `accept <NNN>` and `cases <NNN>` subcommands.
  - `cmd_resolve()` (found while building R13, not in the spec): when `.sdlc/last-id` is the only
    file a rebase conflicts on, it settled the counter and then refused, leaving the rebase
    stopped, so every batch of two or more locally numbered changes stopped at its second. It now
    continues the rebase while the counter is all that conflicts (at most `RESOLVE_STEPS`
    commits) and reports `clean`; the skill's Step 3 goes on as for `rebased`, and runs the
    builder only when `conflicted` lists files, so its chained block is split in two.
- `plugins/factory/agents/approver.md`: the `- UNDONE:` and `- RECOVER:` lines under *What you
  return*.
- `plugins/factory/skills/land/SKILL.md`: description, Steps 0–4, Out of scope (R14); the WAIT asks
  `land-check`'s `question`; Step 3 names `factory.py accept`/`cases` in prose only, no rule.
- `plugins/factory/README.md`: the landing's paragraph; "shipped by hand" goes for checks, cases,
  notes.
- `tests/test_land.py`: R1–R5, R7–R13.
- `tests/test_skills.py`: R6 (`test_no_skill_lets_accept_run_unasked` gains the factory commands).
- `tests/test_factory.py`: the copies (`CASES_RE`, `FRESH_RE`, `CASE_CAP_USD`) pinned to
  `sdlc.py`'s, beside the `risk_paths` pin.

Reused, not re-derived: `_sdlc()` (every `sdlc.py` call), `read_gate_file()` (the accept record has
the gate's attempt shape: `## Attempt k`, `Verdict:`, `Build:`), `_placeholders()`,
`_tree_hashes()`, `landed_build()`, `read_ledger()`/`LEDGER_RE`/`DECIDED`, `risk_paths()`,
`_set_impact()`. `sdlc.py`'s `accept`, `run-cases`, `next-entry`, `preflight`, `config` and `ship`
are called as they are.

## Work order

1. **The copies and the parts.** `UNDONE_RE`, `RECOVER_RE`, `read_proposals()`, `land_parts()`,
   `land_signals()` without the exclusions, `land_question()`, `cmd_land_check()` printing both.
   Tests: R1, R2, R3, and the pins. (Before `land` refuses or writes anything new, a change with
   checks reaches `land`; it lands only when nothing else refuses, and slice 3 closes that.)
2. **`factory.py accept`.** `accept_build()`, the record, `_accept_state()`. Test: R4.
3. **`factory.py cases`** and `_note_line()`. Test: R5 (stand-in `_sdlc`).
4. **`land` refuses** without a passing accept on the build as it stands, or without the cases
   note, or with an unrecovered irreversible path. Test: R7, R10's exclusion.
5. **`land` disposes and confirms**, and the message carries the paragraphs. Tests: R8, R9.
6. **The approver's prompt** and `approver.md`. Test: R10.
7. **`land-verdicts` asks for `accept`** after a rebase. Test: R11.
8. **End to end**: R13, three changes through `factory.py` alone; `resolve`'s counter-only
   conflict, which R13 reaches.
9. **Docs and the skill**: R6, R14; `./check.sh`.

## Tests

- R1: `test_a_change_with_acceptance_checks_or_undone_items_is_in_the_batch_behind_the_persons_yes`
  (replaces `…_is_shipped_by_hand`).
- R2: `test_land_check_shows_each_changes_checks_cases_notes_decisions_and_recovery`.
- R3: `test_the_landing_question_names_only_what_the_batch_holds` (pure, over `land_question()`).
- R4: `test_factory_accept_records_sdlc_accepts_verdict`.
- R5: `test_factory_cases_writes_the_note_ship_reads_or_stops` (stand-in `_sdlc`; the note read
  back through `sdlc.py`'s `findings_entries()`).
- R6: `tests/test_skills.py::test_no_skill_lets_accept_run_unasked`, extended.
- R7, R12: `test_land_refuses_a_change_whose_checks_or_cases_havent_run` (cases through a stand-in
  that adds a scope to the real `preflight`'s output).
- R8: `test_a_landing_carries_drops_and_confirms_once` (ship refused once by an open finding, then
  rerun; the seed read back through `sdlc.py`'s `inbox_entries()`).
- R9: `test_a_landed_commit_says_who_passed_its_gate_and_carries_no_review_count`, extended.
- R10: `test_the_approver_proposes_dispositions_and_recovery`.
- R11: `test_a_rebased_change_runs_its_checks_again_before_its_review`.
- R13: `test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone`.
- The copies: `test_the_factorys_copies_of_ships_notes_and_cap_match_sdlcs` in `test_factory.py`.
- R14: `./check.sh` (the skills' WAIT, dialog and rule tests).

## Rollback

`git revert` of the change's commit undoes all of it: code, skill, docs and tests. It does not
undo what a landing already did with it in a host: seeds it appended to the register, ticks in a
landed change's `notes.md` and `decisions.md`, and `How to recover:` in its commit. All of those
are committed history, written behind the person's yes, and stay correct after a revert (they are
what `/sdlc:ship` would have written). Nothing is created outside the repo; `run-cases` writes
only under the ignored `.sdlc/reports/`.
