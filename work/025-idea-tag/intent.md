---
id: 025
slug: idea-tag
tier: 2
impact: minor
stage: shipped
created: 2026-10-25
updated: 2026-10-26
shipped: 2026-10-26
idea:
depends_on:
serves: none
---

# 025 — Tag ideas [idea], and call every inbox entry a seed

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

"Seed" means two things today. It is the tag on one kind of `work/inbox.md` entry
(`## [2026-10-25-23] [seed] …`), beside `[bug]` and `[nit]`, and it is also used loosely for
anything in the register that could become a change: retro "proposes one paydown seed per theme"
from nits, and status puts "seeds" forward. In the originator's words: "An idea, a feature, a bug,
a nit is a seed. A seed for a change." So a reader can't tell whether "the seeds" means every entry
or only the ones tagged `[seed]`, and the tag names the role (what a change grows from) rather
than the kind (an idea). The word is in about 25 files: `scripts/sdlc.py` (status's `seed` rule,
ship's "removed seed" message, retro's counts), every skill that writes the register (`bug`,
`ship`, `retro`, `intent`), `templates/inbox.md`, `defaults/SDLC.md`, `docs/REFERENCE.md` and the
tests.

## Outcome

- **`templates/inbox.md` says what a seed is.** Its `>` note opens with the concept: every entry in
  the inbox is a seed, something a change may grow from, and each seed has a kind, given by its
  tag: `[idea]` for a proposed change, `[bug]` for something already broken, `[nit]` for a finding
  ship approved unfixed. Then each kind's body lines (`After:`, `Severity:`, `Theme:`…), how an
  entry is named, and what `/sdlc:status` and `/sdlc:intent` do with them, as now. It says that a
  `[seed]` tag from before this change reads as `[idea]`. Someone reading only that note can tell
  "seed" (any entry) from "idea" (one kind). It keeps the shape `tests/test_defaults.py` requires
  (one title, one `>` note, `##` sections).
- New entries for a proposed change are tagged `[idea]`. The skills that write the register
  (`ship` carrying notes, `retro` proposing paydowns, `bug` retagging a non-bug) write `[idea]`.
- "Seed" means any inbox entry, whatever its kind, everywhere it appears: skills, defaults,
  REFERENCE, status and retro output, and the script's comments and messages, matching the
  template's note. Where the text means only the idea kind, it says "idea".
- A `[seed]` entry is still read as an idea, for good. That is not a shim: history and hosts hold
  them. This repo's inbox is retagged `[seed]` → `[idea]`, and `migrate-inbox` offers hosts the
  same retag.
- The process doc and the inbox template say what a seed becomes: a change of a type (`feature`,
  `fix`, `refactor`, `docs`, `chore`…), which its kind suggests, so hosts can adopt the names. In
  the originator's words: "Those can turn into different outcomes. It could be a feature, a fix, a
  chore, and so on." Whether a commit carries the type is the host's call; recording it is a seed
  of its own.
- `./check.sh` passes, with a test that a `[seed]` and an `[idea]` entry read the same, and one
  that the inbox template's note names all three kinds and defines "seed" as any entry.

## Affected

- **Area:** the inbox register's vocabulary: the script, the skills that read and write it, and
  the docs that describe it.
- **Files & components:** `scripts/sdlc.py` (entry kinds, status's `NEXT_RULES`, `migrate-inbox`,
  user-facing strings), the skills `bug`, `intent`, `ship`, `retro`, `status`,
  `templates/inbox.md`, `defaults/SDLC.md` and its mirror `.sdlc/SDLC.md`, `docs/REFERENCE.md`,
  `README.md`, `AGENTS.md`, `.sdlc/DIRECTION.md`, and the tests that assert on `[seed]` or "seed"
  output.
- **Downstream:** every host's `work/inbox.md` (the tag the skills write into it, and
  `migrate-inbox`), anyone reading status or retro output, and new hosts whose inbox is written
  from the template.
- **Contracts:** AGENTS.md's "never match an entry by title alone", the defaults/`.sdlc/` mirror
  and its `record`, and the process doc's rule that what `sdlc.py` writes in a host is Tier 2.

## Constraints

- Every `[seed]` entry in a host's inbox and in history keeps reading as an idea: status's
  ordering, `After:` waits, `idea:` links and retro's counts are unchanged for it.
- Never match an entry by its tag or title alone; ids stay as they are.
- `defaults/SDLC.md` and `.sdlc/SDLC.md` move together, and `sdlc.py record` is rerun so drift is
  clean.
- Setup's drift must not report a host's `[seed]` entries as breaking.

## Open questions

- ~~Does the frontmatter `idea:` key keep its name? It links an idea entry, but under the new
  vocabulary it is "the seed this change grew from"; bugs use `fixes:`.~~ Resolved: it stays; it
  names the idea a change grew from (spec R8).
- ~~Status's rule names and output (`seed`, "next in series", "every other ready seed"): renamed to
  `idea`, or kept, since the umbrella word now covers them?~~ Resolved: the last rule becomes
  `idea`; milestone and series keep *seed*, since they can name any kind (spec R3).
- ~~Does `migrate-inbox` retag unasked, or only when told, and is the retag recorded in setup's
  record or drift?~~ Resolved: it retags when run, readiness nudges, setup's record isn't involved,
  and the step goes with `migrate-inbox` in 1.4.0 (spec R5).
- ~~Do other `[…]` tags get named kinds too, now that unknown tags read as ideas? The originator:
  "right now we don't have a tag feature, maybe in the future we will". Free-form labels, apart
  from the kind, are a later change.~~ Resolved: deferred; an unknown tag still reads as an idea.
- ~~Is `[building]` still a tag on the entry, or a state any seed's kind can be in?~~ Resolved: it
  stays a tag, on ideas only (spec R8).
