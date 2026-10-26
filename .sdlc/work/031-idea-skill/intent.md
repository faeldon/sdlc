---
id: 031
slug: idea-skill
tier: 2
impact: minor
stage: shipped
created: 2026-10-27
updated: 2026-10-27
shipped: 2026-10-27
idea: 2026-10-27-2
depends_on:
serves: [O3]
---

# 031 — An /sdlc:idea skill, and inbox-commit for every kind of entry

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`sdlc.py bug-commit` already commits any change to `.sdlc/work/inbox.md`: it diffs the register
against `HEAD` and writes `File <id>`, `Update <id>` or `Retire <id>` for each entry, whatever its
kind, and `/sdlc:triage` uses it to file ideas split off from issues. But its name says bugs (in
AGENTS.md, `docs/REFERENCE.md` and the script's help, which all call it the one code that commits
the inbox), its retire reasons (`RETIRE_REASONS` in `scripts/sdlc.py`: `duplicate`, `not-a-bug`,
`wontfix`, `cant-reproduce`) only fit bugs, and no skill files an idea someone dictates
mid-session: `/sdlc:bug` files bugs, triage files issues, ship files nits and carried items, retro
its own seeds. So ideas get committed by hand, under `Seed <id>: …` subjects nothing in history
reads; this change's own seed (`f305c10`) is one.

## Outcome

- `sdlc.py inbox-commit` commits the register as `File`/`Update`/`Retire <id>`, as `bug-commit`
  does today; `bug-commit` is gone, and the bug and triage skills, the docs and the tests name the
  new command.
- Retiring an idea takes `superseded`, `declined` or `duplicate`; a bug keeps its reasons; a reason
  that doesn't fit the entry's kind is refused, and a nit is ship's to retire, so it is refused here.
- `/sdlc:idea` takes an idea in the person's words, drafts a neutral entry with an id from
  `next-entry` (an `After:` line when it follows another seed), and after its one WAIT appends it
  and runs `inbox-commit`. Editing or retiring an existing idea goes through the same skill.
- **Moves O3:** filing a dictated idea, from any checkout, costs the person one stop (the skill's
  WAIT), where today it takes a hand-written commit.

## Affected

- **Area:** the inbox register's commit path, and a new skill.
- **Files & components:** `scripts/sdlc.py` (the subcommand, `RETIRE_REASONS`, retire validation
  by kind), `skills/bug/SKILL.md`, `skills/triage/SKILL.md`, a new `skills/idea/SKILL.md`,
  AGENTS.md, `docs/REFERENCE.md`, README.md where it lists the skills, and `tests/test_bugs.py`,
  `test_archive.py`, `test_skills.py`, `test_adoption.py`.
- **Downstream:** hosts running `/sdlc:bug` or `/sdlc:triage`, which get the renamed command with
  the skills that call it, at `/reload-plugins`. Retro's `bugs_retro()` and anything reading
  `File`/`Retire`/`Update` subjects from history, which must keep reading them.
- **Contracts:** a skill's `allowed-tools` and a new WAIT (always Tier 2); the skills invariants
  (one WAIT heading, description over 80 characters saying when not to use it, a `Bash(...)` rule
  per command); the register's format (`BODY_KEYS`, entry ids); a shim needs a
  `.sdlc/deprecations.toml` entry.

## Constraints

- `bug-commit`'s guarantees carry over: it commits the inbox alone, on `main` in the main
  checkout (runnable from a worktree for named entries), and a triaged record is committed before
  the issue is told.
- Subjects history already holds keep being read.
- Bug retire reasons keep their meaning.

## Open questions

- ~~Is "no shim" right? `bug-commit` shipped in v1.2.0, so a host's own scripts, notes or habits
  could name it, though the plugin's allow rules don't.~~ Resolved: no shim; nothing setup writes
  names it (spec R1).
- ~~Does `/sdlc:idea` file only from the main checkout, as `bug-commit` must, or also from inside
  a change's worktree?~~ Resolved: from any checkout, `/sdlc:bug` too; from a worktree,
  `inbox-commit <id>` files the named entries on `main` in the main checkout (spec R5–R7, R9).
- ~~Should the hand-written `Seed <id>: …` commits already in history be read as `File` commits,
  or left alone?~~ Resolved: left alone; nothing reads those subjects, and `next_entry_ids()`
  already reads every commit that held the register.
- ~~Does `/sdlc:bug` grow to cover ideas, or do the two skills stay separate and share only the
  commit?~~ Resolved: two skills, sharing `inbox-commit` (spec R8, R9).
