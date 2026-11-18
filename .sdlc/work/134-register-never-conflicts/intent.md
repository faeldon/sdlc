---
id: 134
slug: register-never-conflicts
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-16
depends_on:
serves: [O5]
---

# 134 — The register never conflicts when a change lands

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In the person's words: "Landings conflict on the register every time: today all four landing
conflicts (124, 128, 129, 130) involved .sdlc/work/inbox.md, and three were nothing else, each
costing a builder resolution, a gate and every reviewer at the run's depth." 133 then made five
out of five.

The cause: `factory.py land --by person` appends each carried seed and filed bug to
`.sdlc/work/inbox.md` in the change's own worktree (`_dispose()`), riding the change's commit;
`/sdlc:ship` appends its nits, bugs and carried seeds there by hand too, and `sdlc.py ship` deletes
the seed the change took. Meanwhile every other landing, and every `/sdlc:idea` through
`inbox-commit`, appends to the same file's end on `main`. Two appends at one file's end always
conflict on rebase. AGENTS.md already says an entry never rides a change's branch, where a drop
would lose it (that's why `inbox-commit` exists); the landing and ship are the exception, and it
is the exception that bites.

## Outcome

- A landing or ship no longer conflicts on `.sdlc/work/inbox.md` when other entries were filed on
  `main` meanwhile, and nothing a change files or retires is lost or written twice.
- A test lands two changes that each carry a seed, one after the other with an `/sdlc:idea` filed
  between them, and finds no register conflict on rebase, every entry exactly once, and each
  change's taken seed gone.
- **Moves O5:** a batch landing spends its builder, gate and review runs on code conflicts only,
  not on the register.

## Affected

- **Area:** the register, landing and ship.
- **Files & components:** `plugins/factory/scripts/factory.py` (`_dispose()`, `land`, `land
  --close`); `scripts/sdlc.py` (`cmd_ship`'s seed deletion, `inbox-commit`), possibly
  `.gitattributes`; `skills/ship/` (its register writes); the land skill; REFERENCE.md and
  AGENTS.md (*The register*); tests.
- **Downstream:** every host's landings and ships; the register `/sdlc:status` shows and retro
  ranks; the ids commit messages cite (`Carried forward:`, `Retired nits:`).
- **Contracts:** `inbox-commit` is the only code that commits the register on its own, always on
  the base branch in the main checkout; the record is committed before anything is told; nothing
  lost (O2), and a rerun finishes one cut short; a dropped change must not lose an entry; ids come
  from one `next-entry` call.

## Constraints

- No entry lost or duplicated, including when a landing stops part way or is rerun.
- A change's commit message still names the ids it carried, filed or retired, and they resolve in
  the register once it lands.

## Open questions

- ~~Which way: (a) the landing and ship file their entries through `inbox-commit` on `main` after the
  change's commit lands, and retire the taken seed the same way; (b) a union merge on the register
  (`.gitattributes` `merge=union`) with a check that both sides' entries survive; or (c) both?~~
  Resolved: (a), held in the change's `entries.md` and filed inside the `Close` commit (spec R1–R4).
- ~~With (a), what happens to entries when a landing commits but stops before close, as 124, 125 and
  129 did today: filed at commit time, or only once the change is on `main`?~~ Resolved: only once
  it is on `main`, by close (spec R4, R12).
- ~~With (b), does union merging survive a deleted entry (the seed a change takes) cleanly, and does
  it reach hosts, who would need the `.gitattributes` line too?~~ Resolved: no to both, so it is
  not used (spec, *Alternatives rejected*).
- ~~Does ship by hand change the same way as the landing, so the two paths agree?~~ Resolved: yes
  (spec R1–R4, R13).
