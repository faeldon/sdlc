---
id: 030
slug: ship-preflight
kind: plan
created: 2026-10-27
updated: 2026-10-27
---

# 030 — One preflight call for ship's lookups · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

Ship (`skills/ship/SKILL.md`, 412 lines, 19 `Bash(...)` rules, 12 `sdlc.py` calls) runs `undone`,
`nits --change`, `closes`, `checks` and `context` one at a time, and builds its WAIT question in
prose. The spec (`.sdlc/work/030-ship-preflight/spec.md`, R1–R9) adds a read-only
`sdlc.py preflight <NNN>` that returns all five parts, and `preflight <NNN> --question …` that
renders the WAIT question with the clause rules in code. `preflight` and `nits` join `READ_ONLY`.

Baseline for R8: 412 lines, 12 `sdlc.py` calls (status, config, base, undone, nits, closes, check,
checks, context, next-entry, ship, sync), 19 rules. Target: 8 subcommands (status, config, base,
preflight ×2, check, next-entry, ship, sync), 15 rules.

## Files to change

- `scripts/sdlc.py`: split five readers into report + print; add `ship_question()`,
  `cmd_ship_question()`, `cmd_preflight()`, the `preflight` parser and dispatch; `READ_ONLY` gains `preflight`, `nits`.
- `skills/ship/SKILL.md`: Steps 0, 1, 3, 5 and `allowed-tools`.
- `.claude/settings.json`: the two new allow rules.
- `docs/REFERENCE.md`: name `preflight` with ship's lookups (near the `nits`/`checks` lines, ~263,
  ~340) and among the read-only commands setup allows.
- `tests/test_preflight.py` (new): R1–R5.
- `tests/test_skills.py`: update the ship tests that pin the old commands
  (`test_ship_checks_the_context_docs_inside_its_one_gate`,
  `test_nits_are_offered_early_recorded_at_ship_and_counted_by_retro`,
  `test_ship_lists_then_runs_the_changes_checks_under_a_prompt`,
  `test_ship_asks_about_each_issue_it_would_close_and_splits_off_the_rest`) to look for
  `preflight` instead; add a test that Step 5 runs `preflight <NNN> --question`.
- `tests/test_readiness.py` / `tests/test_acceptance.py`: no edit expected; they must still pass
  (no writer in `ALLOW_RULES`, `accept` not in it).
- `tests/test_adoption.py`: run `preflight 001` via `uv run --script` before `ship 001` (~line 166)
  and assert it exits 0 with every part.

## Work order

1. **Readers as reports (R2).** In `scripts/sdlc.py`, for each of `cmd_undone` (1901),
   `cmd_nits` (1921), `cmd_checks` (1969), `cmd_closes` (5467), `cmd_context` (6491): move the
   dict-building into `_undone_report(root, path)`, `_nits_report(root, path | None, touching)`,
   `_checks_report(path)`, `_closes_report(root, path)`, `_context_report(checkout, base)`; each
   returns its dict (and, for `context`/`nits --change`, `None` on no merge base so the `cmd_*`
   prints the same `⚠` and exits 1). `cmd_*` keep `_one_change()`, printing and exit codes.
   Stop: full suite passes unchanged.
2. **`cmd_preflight` (R1, R3).** Resolve with `_one_change()`; `rec = load_change(path, home)` for
   `tier`/`stage`; `folder` via `_shown(path, root)`; call each report, the context one with
   `checkout_of(path)` and `git.base`; collect `problems` as `"<part>: <detail>"` from nits' and
   checks' `problems` (and a missing merge base); print JSON; exit 1 if `problems`. Parser:
   `preflight id [--question] [--context] [--nits] [--closing N]* [--split N]*` (`type=int`,
   `action="append"`). Not in `OWN_SCRIPT_CMDS`. Add `preflight`, `nits` to `READ_ONLY` (5709).
   Stop: tests for R1, R3.
3. **`ship_question()` (R4, R5).** Pure function of `(folder, closes, target, context, nits,
   closing, split, register)` returning `(question | None, refusal | None)`, called by
   `cmd_ship_question()`, which reads `closes:` and the config. With no clause at all, it reads
   `Commit this, with <folder>/ stamped shipped…`, since a bare `, and` would have nothing before it.
   Validate first (number not on `closes:`, in both, or in neither). Render from Step 5's
   sentence: `Commit this` + `, with the context update shown` + `, the nits shown recorded in
   <work_rel>/inbox.md` + `, closing #A and #B when it lands` (+ ` and splitting #C off as a
   seed`/`seeds`) + `, and <folder>/ stamped shipped` + `, then update its issue` unless target is
   `none` + `? (yes / fix a finding first / edit the message)`. Numbers joined `#1`, `#1 and #2`,
   `#1, #2 and #3`. The `and`/comma before "folder stamped" follows from how many clauses precede
   it — pin the sentences in tests, matching today's full example exactly. `--question` prints
   plain text; refusal is `⚠` on stderr, exit 1. Stop: tests for R4, R5.
4. **Ship skill (R7, R8).** Step 0: keep status/config/git and `base <NNN>`; replace the
   `undone`/`nits`/`closes` blocks with one `preflight <NNN>` block and a short paragraph per part
   (what Step 4 does with it), keeping the factory-files paragraph. Step 1: checks come from
   `preflight`'s `checks`; keep "`sdlc.py accept <NNN>`" in prose, after the listing. Step 3: the
   context pass reads `preflight`'s `context`. Step 5: run
   `preflight <NNN> --question [--context] [--nits] [--closing N]… [--split N]…` with the flags
   Step 4 decided, ask exactly what it prints; keep the full-clause sentence as the example; drop
   the "Leave out …" paragraph. `allowed-tools`: remove `undone`, `nits`, `closes`, `checks`,
   `context`; add `preflight`. Update the four `test_skills.py` tests. Stop: `test_skills.py` passes.
5. **Settings, docs, adoption (R6, R9).** `.claude/settings.json` gains the two rules;
   `docs/REFERENCE.md` names `preflight`; `test_adoption.py` runs it. Then `./check.sh`.
6. **Dogfood.** From the worktree, `uv run --quiet --script scripts/sdlc.py preflight 030` and
   `… preflight 030 --question --context`; record `wc -l` and the command count for the ship
   commit.

## Tests

- R1: `test_preflight_parts_equal_the_single_commands` — fixture change with notes.md `- [ ]`,
  a nit on a changed path, `closes: [12, 15]` (no tracker configured, so the part carries its
  `unavailable` reason, as `closes` does), a `checks.md` and an `AGENTS.md` above a changed path;
  compare each part with the matching `cmd_*` output.
- R2: existing `test_nits.py`, `test_acceptance.py`, `test_intake.py`, `test_archive.py::test_closes_*`
  pass unchanged.
- R3: `test_preflight_writes_nothing` (porcelain + folder listing before/after);
  `test_preflight_exits_1_on_a_part_s_problems_and_prints_every_part`;
  `test_preflight_refuses_an_unknown_id`.
- R4: parametrized `test_question_clause` (each flag on/off, target `none`/`github`, one/two/three
  numbers, seed/seeds); `test_question_with_every_clause_matches_ship_s_example`; one CLI run.
- R5: parametrized `test_question_refuses_issues_that_don_t_partition_closes` (not on closes,
  given to both, left out), and the refusal through the command in
  `test_question_through_the_command`.
- R6: `test_readiness.py` unchanged passes; add an assert that `preflight` and `nits` are in
  `READ_ONLY`.
- R7: the updated `test_skills.py` ship tests plus the generic rule tests.
- R8: manual — `wc -l skills/ship/SKILL.md` < 412 and `sdlc.py` calls < 12, in the ship commit.
- R9: `test_adoption.py` with the `preflight` run.

## Rollback

`git revert <sha>` covers everything. Not covered: hosts that ran `/sdlc:setup` after release
keep the `preflight`/`nits` allow rules in `.claude/settings.json`; harmless (they match nothing
or a read-only command), and `/sdlc:uninstall` removes them only while `ALLOW_RULES` still lists
them — remove by hand otherwise.
