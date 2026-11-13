---
id: 056
slug: ship-reads-rare-branches
kind: plan
created: 2026-11-13
updated: 2026-11-13
---

# 056 — Ship reads its rare branches only when preflight says they apply · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `SHIP_BRANCHES` (new), the ordered table of file → condition over
  `preflight`'s parts and the folder: `factory.md` (`decision.md` on disk), `undone.md`
  (`undone.items`), `closes.md` (`closes.closes`), `recover.md` (`risk.irreversible`), `fresh.md`
  (`risk.deep`), `cases.md` (`cases.available` and `cases.scope`). `ship_branches(parts, path)`
  (new); `cmd_preflight()` adds the `branches` part. `prose_metrics()`: sizes stay `SKILL.md`'s, a
  `branches` object gives each side file's, and `commands`/`script_calls` count across them all.
- `skills/ship/SKILL.md`: cut the six branches; Step 0 lists the `branches` part and says to `Read`
  each named file at `${CLAUDE_PLUGIN_ROOT}/skills/ship/<file>`, and no other; one pointer line at
  each cut. Frontmatter unchanged.
- `skills/ship/{factory,undone,closes,recover,fresh,cases}.md` (new): `# <Branch>`, a sentence on
  when `preflight` names it, then `## Step N` sections with the text moved verbatim (cross-refs
  adjusted). Agent verdicts from Steps 0 and 4; undone items from Steps 4 and 6; issues it closes
  from Steps 4 and 6; How to recover from Step 4; the fresh review from Step 3; the skills' cases
  from Steps 1 and 3. Kept in `SKILL.md`: Step 2's deep build line, Pre-existing bugs, nits,
  `fixes:`, checks, fix-first, all of Step 5.
- `tests/test_skills.py`: `_skill_files()`/`_skill_text()` helpers; the uv, rule-coverage and
  stale-rule tests read the joined text (R8); new tests for side files named and gate-free (R4, R9),
  `SHIP_BRANCHES` matching the files (R7), ship's line budget (R3); moved-text tests read the file
  the text went to and assert the pointer (R10).
- `tests/test_preflight.py`: the fixture's `branches`, `decision.md` adding `factory.md`, and one
  condition case per file plus a plain change (R5).
- `tests/test_retro.py`: ship's prose `lines` is `SKILL.md`'s and its `branches` the six (R11).
- The `landing_reach` test: `skills/ship/undone.md` reads as `sdlc:ship` (R12).
- `tests/test_work_folder.py`, `tests/test_defaults.py`: text-wide globs take `skills/*/*.md` (R10).
- `evals/ship/graders/never-reads-a-branch.md` (new): no `Read` under `skills/ship/` but
  `SKILL.md` on the plain fixture (R13).
- `skills/retro/SKILL.md`: its `prose` line names a skill's `branches`.
- `AGENTS.md` (and `docs/CONTRIBUTING.md` if it restates it): side files are part of a skill for
  its rules, script calls and one WAIT (R14).
- `.sdlc/work/056-ship-reads-rare-branches/notes.md` (new): the final line and byte counts (R3).

## Work order

1. Script: `SHIP_BRANCHES`, `ship_branches()`, the `preflight` part, and `test_preflight.py`'s cases.
2. `test_skills.py`'s helpers and new tests; the budget and `SHIP_BRANCHES` tests fail until 3.
3. Split `skills/ship/SKILL.md`; Step 0's instruction and the pointers; fix the moved-text tests.
4. `prose_metrics()` and its test; the `landing_reach` pin; the text-wide globs; the eval grader.
5. Docs: `AGENTS.md`, retro's `prose` line; `notes.md` with the counts.
6. `./check.sh`. If `claude plugin validate --strict` rejects the extra `.md` files, stop and
   revisit the layout.

## Tests

- R1, R2, R4, R6, R9: the side-file test, the one-WAIT test, and the diff read as a verbatim move.
- R3: the budget test; `wc -l skills/ship/SKILL.md` ≤ 475.
- R5: `test_preflight_names_the_branches_that_apply`, `test_ship_branches_condition`.
- R7: `test_ship_branches_are_the_files_beside_ship`.
- R8: the rule tests over the joined text; `test_the_rule_matcher_can_fail` unchanged.
- R10: the updated ship tests; the globs. R11: the retro prose test. R12: the `landing_reach` pin.
- R13: the new grader, and `sdlc.py run-cases 056` at ship, under its prompt (paid).
- R14: `./check.sh` exits 0.
- Manual: `sdlc.py preflight 056` shows `branches` (`[]`, or `["cases.md"]` when ship's cases are
  in scope).

## Rollback

`git revert <sha>` restores `SKILL.md` whole and removes the side files, the `branches` part and the
test changes. Nothing lives outside the repo: no config key, no trailer, no host file (`defaults/`
and `templates/` are untouched). Sessions running from a clone pick the revert up at
`/reload-plugins`.
