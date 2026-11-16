---
id: 064
slug: retro-reranks-inbox
kind: spec
created: 2026-11-16
updated: 2026-11-16
---

# 064 — Retro re-ranks the inbox · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py retro` prints `entries`: each open idea and bug not being built (not tagged
   `[building]`, not named on an open change's `idea:` or `fixes:`), with `id`, `title`, `kind`,
   `priority` (`high`, `med`, `low` or null), `theme` (or null) and `age_days`. Nits are left out.
   A test pins the fields and both exclusions.
2. **R2.** The retro skill, after its passes, drafts a table of **only the lines that change**: each
   entry's id and title, its priority and theme from → to, and one reason. Rules: `Priority: high`
   for what the new direction or milestones make urgent, or what a pass found biting now;
   `Priority: low` for what the direction puts off; removing a `Priority:` that no longer holds; a
   `Theme:` for an entry without one, reusing a theme already in use when one fits. It never ranks a
   nit or an entry being built. Seeds it judges no longer wanted are named in its report with
   `/sdlc:idea <id>`, for the person to retire; retro never removes them. A test asserts the text.
3. **R3.** Retro's WAIT question gains `set these <M> priority and theme lines in
   .sdlc/work/inbox.md` when M > 0, left out when nothing changes; still the one `WAIT`. A test
   asserts the question text.
4. **R4.** Retro's write step `Edit`s each approved line in place in the entry's body (added,
   replaced or removed), and appends new seeds as before. A test asserts the text.
5. **R5.** `retro-commit` refuses, writing nothing, when an entry the committed register held is
   gone, or changed anything but its `Priority:` and `Theme:` lines (heading, tag, prose, other
   `Key:` lines). Entries appended after the last are allowed. Tests: a changed priority or theme
   passes; a removed entry is refused; edited prose is refused; a new seed passes.
6. **R6.** `AGENTS.md` (the retrospective paragraph: `retro-commit` guards the register) and
   `docs/REFERENCE.md` (what a retrospective writes to the register).
7. **R7.** `./check.sh` exits 0.

## Design

**R1.** `retro()` builds `entries` from `inbox_entries(home)`, dropping nits (`is_nit`), entries
tagged `[building]` (`is_building`) and any `_open_claims(home)` names (by `ref_matches`); each
with `entry_priority()`, `entry_theme()` and `_age_days()` on its date.

**R5.** A pure helper, `register_drift(old_text, new_text) -> list[str]`, parses both with
`parse_entries()`. For each old entry with an id: missing in the new → "`<id>` was removed: retire
it with /sdlc:idea"; otherwise compare heading (tag, title), prose and every body line but
`Priority:` and `Theme:` → "`<id>` changed beyond its Priority: and Theme: lines".
`cmd_retro_commit` reads the register at `HEAD` and on disk and adds each to `refusals`; a register
missing at `HEAD` has nothing to compare.

**Skill.** Step 2's direction pass gains the re-rank, reading `entries`; Step 4 shows the table
after the seeds; Step 5's question adds the clause; Step 6 writes the lines; Step 7 reports the
retire candidates. `allowed-tools` unchanged: retro already has `Edit` and its commands.

## Contracts touched

- **Always Tier 2, a skill's WAIT, what it approves**: the approval widens to the priority and
  theme lines, named in the question; still one WAIT, nothing written before it.
- **`retro-commit` writes the direction doc, the register and the product doc, nothing else**:
  unchanged; it gains a refusal, never a path, and every refusal still comes before any write.
- **An entry leaves the register through ship, `/sdlc:idea` or `/sdlc:bug` and `inbox-commit`,
  never through retro**: R5 enforces it.
- **`Priority:` words**: retro writes only `high` or `low` from `PRIORITIES`; `check` already
  reports any other, and one on a nit.
- **Nits ranked by `Cost:`/`Value:`; an entry being built is untouched**: R1 leaves both out of
  what retro sees.
- **Retro's output size (059)**: `entries` adds about 30 short rows here, no per-change blob.

## Alternatives rejected

- **Retro retires seeds too**: the person chose to keep removal per seed, through `/sdlc:idea`,
  with its own reason and commit.
- **A `Why:` line on each priority retro sets**: a new key on entries for a reason the retro's table
  already showed at approval, and the next retro re-judges anyway.
- **Showing every open entry in the table**: 28 rows with no change bury the few that do; only the
  changes are what the one approval needs to see.
- **Calling `/sdlc:idea --themes`**: a second approval and commit; the retro proposes themes itself,
  behind its one stop.

## Verification

```bash
uv run --group dev pytest -q tests/test_retro.py tests/test_skills.py
uv run --quiet --script scripts/sdlc.py retro | jq '.entries | length'
./check.sh
```
