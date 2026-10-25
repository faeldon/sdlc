---
id: 017
slug: ship-seed-and-staged
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 017 — Ship stages a path already staged, and finds the seed whatever form idea: takes · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py ship` never passes a fully staged path (porcelain worktree column a space) to
   `git add`, and still lists it as staged. Test: a `git rm`'d tracked file and an edited one exit
   0, both in `git diff --cached`.
2. **R2.** A path staged and changed again (`MM`) still goes to `git add`, so the later edit is
   staged. Test.
3. **R3.** `_seed_title()` reads an `idea:` value holding the heading with or without its leading
   `## `. Test (in the parametrized seed test): `idea: "[2026-10-02] [seed] Reopen drafts"` against
   `## [2026-10-02] [building] Reopen drafts → work/001-reopen-drafts/` deletes that entry and
   nothing else.
4. **R4 (nit 014-1).** `_seed_title()` cuts only a trailing ` → work/…` pointer, so a title holding
   an arrow ("Map intent → spec") is kept whole. Test: such a seed is found and deleted.
5. **R5.** A line in `work/ideas.md` without `## ` never counts as a seed heading; `IDEA_RE`,
   `idea_entries()` and status's orphan check are unchanged. Test: a body line starting
   `[2026-10-02] [seed] Reopen drafts` is not deleted.
6. **R6.** `skills/intent/SKILL.md` Step 5 says to set `idea:` to the seed's title alone (no date or
   tag), to change only the heading's tag to `[building]`, and to put the pointer as the entry's
   first body line, `Building in work/NNN-slug/.`, never in the heading.
7. **R7.** `defaults/SDLC.md`'s frontmatter comment `idea: # optional backlink to a work/ideas.md
   heading` reads `… the title of a work/ideas.md seed`, the same edit in `.sdlc/SDLC.md`, and
   `.sdlc/setup.json` is re-recorded (`drift` clean).
8. **R8.** Every form that worked before still deletes the seed: bare title, the whole `## `
   heading, a heading or `idea:` carrying ` → work/…`. The existing tests pass unchanged.

## Design

`_status_entries(tree)` returns `(xy, path)` pairs from the porcelain parse `_dirty_paths()` does
today; `_dirty_paths()` returns their paths, so its other callers are unchanged. `_stage_change()`
hands `git add --` only the paths whose `xy[1] != " "` and reports every dirty path not left out as
staged, since the fully staged ones already are. With nothing to add it runs no `git add`.

`_seed_title(text)` matches `IDEA_RE` on the text, or on `## ` + the text when that fails, takes
the title group (or the text when neither matches), and cuts at the first ` → work/`. `_seed_lines()`
keeps its `IDEA_RE.match(line)` gate, so R5 holds.

## Contracts touched

- **Stage by name, never `-A`.** Paths are still named after `--`; skipping only passes fewer.
- **`--leave` and its already-staged refusal.** Unchanged; they run before staging.
- **`_drop_seed()` byte for byte; two matches refuse.** Unchanged.
- **What `sdlc.py` writes in a host (Tier 2).** Ship stages a change holding a staged deletion where
  it refused, and deletes the seed in more cases. No key or template heading, so `RETIRED_KEYS` and
  `TEMPLATE_READS` are untouched.
- **Defaults mirror into `.sdlc/`.** R7 makes the same edit in both, then `record`.
- **Nothing about a project.** Test data stays `Reopen drafts`.

## Alternatives rejected

- **Make `## ` optional in `IDEA_RE`.** Status, retro and `idea_entries()` would count any line
  starting with a date as a seed heading.
- **`git add -A -- <paths>`.** It fails on a `D ` path's pathspec too, and `-A` reads like the sweep
  the contract forbids.
- **Keep the pointer in the heading.** It makes a title with an arrow ambiguous, and status's orphan
  check matches titles that then carry a pointer.
- **A shim for the old heading form.** Hosts' existing headings are data, read for good; nothing is
  retired.

## Verification

- `uv run --group dev pytest tests/test_sdlc.py tests/test_skills.py tests/test_defaults.py -q`, then
  `./check.sh`; `sdlc.py drift` clean.
