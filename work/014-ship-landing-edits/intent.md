---
id: 014
slug: ship-landing-edits
tier: 2
impact: minor
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea: Ship does its own landing edits
depends_on:
serves: [O3]
---

# 014 — Ship does its own landing edits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:ship` Step 6 leaves two mechanical edits to the model, after the human approves the commit:

- **delete the seed entry** the change's `idea:` line names from `work/ideas.md`, heading to the
  line before the next `## `;
- **build the `git add` list** by hand: the change's code, its folder `work/NNN-slug/`,
  `work/ideas.md` and `work/nits.md` when Step 6 edited them, any context doc it edited, and
  `.sdlc/last-id` when `new` wrote one. `git add -A` is banned, rightly, so every path is reasoned
  out one at a time.

Neither needs judgment, and both go wrong quietly. In 001, 003 and 005 each took a hand-written
script or a 9–22-path `git add`; in 013 the worktree guard refused a compound command and the
steps were split and rerun by hand. A path left out lands without its change; a path wrongly
included bundles unrelated work, the thing Step 0 exists to prevent. Each hand-built command can
also be another permission prompt, which counts against O3's stop target.

## Outcome

- `sdlc.py ship <NNN>` (still run after the WAIT) also deletes the seed entry `idea:` names from
  the checkout's `work/ideas.md`, saying so when there is none rather than failing, and prints the
  exact paths to stage, as a list the skill passes to one `git add`.
- Ship's Step 6 runs that and stages what it printed; it no longer edits `work/ideas.md` or builds
  the list by hand.
- Tests: a change from a seed (entry gone, neighbours untouched, `ideas.md` in the paths), from no
  seed, a missing or already-deleted entry, and a change with `.sdlc/last-id`;
  `test_adoption.py` still runs `new` → `close` in a bare repo.
- **Moves O3:** a Tier 1 ship stops its person only at its WAIT, with no extra permission prompts
  for staging or the `ideas.md` edit; close's `Sdlc-Totals` `permission=` reads 0 at ship.

## Affected

- **Area:** ship (script and skill)
- **Files & components:** `scripts/sdlc.py` (`cmd_ship`, a helper listing a change's paths, likely
  reusing `changed_paths()`), `skills/ship/SKILL.md` Step 6 and its `allowed-tools`,
  `tests/test_sdlc.py`, `docs/REFERENCE.md` where it describes what `ship` writes
- **Downstream:** every host's ship. `sdlc.py ship` would newly write a host's `work/ideas.md`,
  which is why this is Tier 2.
- **Contracts:** seed entries found by heading and edited as text, never round-tripped (as
  `stamp_shipped` edits lines in place); `allowed-tools` rules exactly as the commands run; "only
  publish pushes" untouched; ids matched with `names_change()`.

## Constraints

- Every write still follows ship's one WAIT: `sdlc.py ship` already runs only after it, and this
  doesn't move it earlier.
- The script never stages what Step 0 flagged as unrelated and never uses `git add -A`: the list
  is the change's own paths, and `git status --short` is still read before the commit.
- A rerun is safe: a second `ship` after a refused commit finds the seed already gone and carries
  on.
- Paths with spaces or unusual characters reach `git add` intact.

## Open questions

- ~~How does the script tell the change's own paths from unrelated work in the same tree?~~
  Resolved: every path `git status` lists in the change's worktree (`_dirty_paths()`), since the
  worktree is the change; what Step 0 flags and the human commits separately is passed as
  `--leave <path>`.
- ~~Does `sdlc.py ship` stage the paths itself or only print them?~~ Resolved: it stages, with
  `git add -- <paths>`, as `cmd_drop` already does; ship loses its `git add` rule. It never
  commits.
- ~~Do the nits and notes edits come along?~~ Deferred: their text is judgment; only the seed
  deletion and the staging are mechanical.
- ~~How is a seed entry matched to `idea:`?~~ Resolved: exact title, ignoring a trailing ` → …`
  pointer and accepting a full heading in `idea:`; two matches refuse before any write, none is a
  note.
