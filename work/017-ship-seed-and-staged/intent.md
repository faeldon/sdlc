---
id: 017
slug: ship-seed-and-staged
tier: 2
impact: patch
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea:
depends_on:
serves: [O3]
---

# 017 — Ship stages a path already staged, and finds the seed whatever form idea: takes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Since 014, `sdlc.py ship` deletes the change's seed from `work/ideas.md` and stages the change
itself. On 2026-10-25 a host's ship did neither, and the person staged and deleted by hand. Two
causes:

- **Staging stops at a deletion already staged.** `_stage_change()` hands every path `git status`
  lists to `git add --`. A path removed with `git rm` (status `D `) is in neither the index nor the
  tree, and git refuses it: `fatal: pathspec 'f' did not match any files` (reproduced in a scratch
  repo). The host's change had deleted `.gitattributes` that way.
- **The seed isn't found when `idea:` lacks the heading's `## `.** The intent skill says to set
  `idea:` "to that entry's heading"; two of the host's changes copied it without the Markdown
  marker (`idea: "[2026-10-24] [seed] <title>"`). `IDEA_RE` is anchored on `^##`, so
  `_seed_title()` falls back to the whole string, date and tag included, which never equals a
  heading's title, and `_seed_lines()` returns `[]` (reproduced with the host's exact strings). The
  ` → work/…` pointer intent adds to the heading isn't the cause, but it cuts a title holding an
  arrow short (nit 014-1).

## Outcome

- Ship skips a path already fully staged and stages the rest. Test: a `git rm`'d file and an
  edited one ship in one commit, no refusal.
- `_seed_title()` reads an `idea:` value with or without the leading `## `; the scan of
  `work/ideas.md` still requires `##`. Test: the host's pair, `[2026-10-24] [seed] Title` against
  `## [2026-10-24] [building] Title → work/101-x/`, finds the heading.
- The intent skill names the form `idea:` takes and puts the `[building]` pointer in the entry's
  body, not its heading; ship still finds a seed already retagged with a ` → ` pointer.
- Nit 014-1 is retired, or recorded as no longer reachable by a new seed.
- **Moves O3:** a host ships a change that came from a seed, or that deletes a file, without
  staging or editing `work/ideas.md` by hand.

## Affected

- **Area:** shipping
- **Files & components:** `scripts/sdlc.py` (`_stage_change()`, `_dirty_paths()`, `IDEA_RE` or
  `_seed_title()`, `_seed_lines()`), `skills/intent/SKILL.md` (Step 5's seed paragraph),
  `skills/ship/SKILL.md` if its seed wording changes, the ship tests in `tests/test_sdlc.py`
- **Downstream:** every host's `/sdlc:ship`; hosts' open changes whose `idea:` lacks `## `; hosts'
  `work/ideas.md` headings already retagged with a pointer; `retro` and any other reader of
  `IDEA_RE`
- **Contracts:** staging still names paths after `--`, never `-A`, and leaves `--leave` paths out;
  `_drop_seed()` keeps every other entry byte for byte; two matching seeds still refuse

## Constraints

- Nothing outside the change gets staged; a path is skipped only because it is already staged.
- An ordinary line in `work/ideas.md` starting with a date never counts as a heading.
- Seeds and `idea:` lines in every form written so far keep working (`## …`, bare title, the
  host's form).

## Open questions

- ~~Widen `IDEA_RE` itself, which `retro` and others share, or give `idea:` values a reader of
  their own?~~ Resolved: neither; `_seed_title()` retries the value with `## ` before it, and the
  heading scan keeps `IDEA_RE` strict.
- ~~A half-staged path (`MM`) must still go to `git add`, so only a blank worktree column is
  skipped?~~ Resolved: yes; only `xy[1] == " "` is skipped, and `D ` is the one git refuses.
- ~~Does intent write `idea:` as the bare title from now on, or the heading without `## `?~~
  Resolved: the bare title, as this repo already does.
- ~~Do headings retagged by older intents need the ` → ` strip for good, or only until hosts'
  current seeds are gone, which would make it a shim?~~ Resolved: for good, narrowed to ` → work/`
  (nit 014-1); old headings are data, not a deprecated path, so no shim.
