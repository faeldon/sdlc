---
id: 025
slug: idea-tag
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 025 — Tag ideas [idea], and call every inbox entry a seed · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. The inbox template defines the terms.** `templates/inbox.md`'s `>` note opens with the
   concept: every entry is a seed, something a change may grow from, and a seed's kind is its tag:
   `[idea]` a proposed change, `[bug]` something already broken, `[nit]` a finding ship approved
   unfixed; `[building]` marks an idea a change is building; a `[seed]` tag from before this change
   reads as `[idea]`. Then each kind's body lines, naming, and what status and intent do, as now.
   Its example heading uses `[idea]`. A test asserts the note names `[idea]`, `[bug]`, `[nit]`,
   `[building]` and `[seed]`, and `test_defaults.py`'s shape test still passes.
2. **R2. `[seed]` and `[idea]` read the same, for good.** One test, parametrized over the two
   tags, asserts the same status next-up line, retro idea count, milestone verdict and ship's
   deletion by `idea:`. Reading `[seed]` is not a shim and gets no `deprecations.toml` entry.
3. **R3. Status's last rule is `idea`.** `NEXT_RULES`'s `("seed", "every other ready seed, oldest
   first")` becomes `("idea", "every other ready idea, oldest first")`, its label `idea`. The
   `bug`, `milestone`, `series` and `nits` rules are unchanged. `docs/REFERENCE.md`'s rule list and
   `skills/status/SKILL.md` say so.
4. **R4. Retro counts ideas as ideas.** `retro`'s `ideas` becomes `{"open": N, "oldest": …}`,
   counting the same entries as today; `skills/retro/SKILL.md` reads it by that name.
5. **R5. `migrate-inbox` retags.** It rewrites each `[seed]` heading tag outside a fence to
   `[idea]`, id, title and body untouched, and lists each under `retagged` in its report.
   `inbox_migration()` lists "retag N [seed] entries as [idea]", so readiness warns and setup
   offers it. It refuses on uncommitted edits as now, and a rerun has nothing to do. The retag
   goes with the rest of `migrate-inbox` in 1.4.0: a `[[shim]]` entry `seed-tag-retag`,
   `remove_in = "1.4.0"`, with its test.
6. **R6. The writers write `[idea]`.** `ship` (carried notes), `retro` (findings), `bug` (retagging
   a request filed as a bug) and intent's examples write `[idea]`. A test asserts no skill,
   `templates/`, `defaults/` or `docs/REFERENCE.md` shows an entry heading tagged `[seed]`;
   `[seed]` appears only where a sentence explains the old tag.
7. **R7. One vocabulary.** "Seed" means any inbox entry wherever it appears: the skills,
   `defaults/SDLC.md` and its mirror `.sdlc/SDLC.md`, `docs/REFERENCE.md`, `README.md`,
   `AGENTS.md`, `templates/direction.md`, `templates/notes.md`, factory's copy of the notes
   template, and `sdlc.py`'s docstrings, comments and messages. Where the text means only the idea
   kind, it says "idea" (e.g. `retro`'s local `seeds` → `ideas`). Checked by the review, not a test.
8. **R8. `idea:` and `[building]` stay.** The `idea:` key keeps its name and meaning, the idea entry
   a change grew from (bugs use `fixes:`); `[building]` stays a tag intent writes over `[idea]` (or
   `[seed]`). Existing tests on `idea:`, `[building]` and ship's deletion pass unchanged.
9. **R9. This repo's inbox is retagged** by running `migrate-inbox` in this change's checkout, so
   `work/inbox.md` holds no `[seed]` heading at ship.
10. **R10. The gate passes.** `./check.sh`, and `sdlc.py drift` reports nothing after
    `sdlc.py record` (this change edits `defaults/`).
11. **R11. The change types are defined** (added in build, at the originator's request). The
    process doc (`defaults/SDLC.md` and its mirror) gets "Seeds, and the changes they become": the
    seed kinds, and the types a change can be (`feature`, `fix`, `refactor`, `perf`, `docs`,
    `test`, `chore`), each with the kind it usually grows from, apart from tier and `impact:`. The
    inbox template's note names the types and points there; ship's commit-style rule uses those
    words when the host's style names a type, and the host decides whether it does. Recording a
    change's type is seed `2026-10-25-24`, not this change. Test:
    `test_defaults.py::test_the_process_doc_names_the_seed_kinds_and_the_change_types`.

## Design

No reading code changes: kind is still decided by `is_bug`/`is_nit`/`is_building`, and anything
else is an idea. The change is words (the template note, docs, skills, under one definition), two
output names (status rule `seed` → `idea`, retro's `ideas.seeds` → `ideas.open`, read only by this
plugin's skills and tests), one migration step (`migrate-inbox` retags `[seed]` headings, in the
same fence-aware pass over headings that gives bare dates an id), and the writers (skills that
append entries write `[idea]`).

"Milestone's first grouped seed" and "next in series" keep *seed*: `Groups:` and `After:` can name
an entry of any kind.

Ordering risk: the main checkout has an uncommitted seed (`2026-10-25-23`) in `work/inbox.md`.
This change rewrites every heading there, so that edit is committed to `main` before ship; ship's
base step then rebases onto it, and the retag is rerun over the new entry.

## Contracts touched

- **Never match an entry by title alone; references are ids or quoted titles.** Untouched: the retag
  changes the tag only, never an id or a title.
- **What history holds is read for good.** `[seed]` stays readable forever, so history's registers
  and the whole-heading `idea:` lines older intents hold (`_seed_title()` strips any tag) read as
  before.
- **Shims in `.sdlc/deprecations.toml`.** Only the retag step is one (R5); the `[seed]` reader is a
  path kept for good.
- **Defaults/`.sdlc/` mirror and record.** `defaults/SDLC.md` and `.sdlc/SDLC.md` change together,
  then `record`.
- **Always Tier 2: what `sdlc.py` writes in a host.** It is Tier 2.
- **Skills' invariants** (`allowed-tools`, one WAIT, script calls): no new commands run, so no rule
  changes.

No policy change.

## Alternatives rejected

- **Stop reading `[seed]` after a deprecation.** Turns every host's inbox and history's registers
  into a shim, for nothing: reading it costs nothing.
- **Rename `idea:` to `seed:`.** Every intent in history has `idea:`, so `closed_changes()` would
  read both forever; and under the new vocabulary `idea:` is already exact.
- **Keep `[seed]` as the tag, another umbrella word ("entry", "request").** The originator chose
  seed as the umbrella.
- **Typed or free-form labels beyond the three kinds.** A later change; an unknown tag still reads
  as an idea.
- **Retagging in setup, unasked.** `migrate-inbox` is the explicit step that rewrites the inbox,
  and readiness already points setup at it.

## Verification

- `./check.sh`: ruff, pytest (the new R1, R2, R5 and R6 tests), `claude plugin validate --strict`.
- `uv run --quiet --script scripts/sdlc.py migrate-inbox` in the worktree reports the retagged ids;
  a second run reports "nothing to migrate".
- `sdlc.py status`'s last next-up lines are labelled `idea`; `sdlc.py retro` shows `ideas.open`.
- `sdlc.py drift` is empty after `sdlc.py record`.
