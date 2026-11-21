---
id: 207
slug: change-origin
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T00:51Z
updated: 2026-11-21
shipped: 2026-11-21
idea:
depends_on:
serves: [O4]
---

# 207 — A change records where its finding came from

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Many of this plugin's changes are its owner's own findings from using it in a host repo. 206 is
one: its six-step update came from updating one host to 1.11.0. Nothing records that.

- An intent names where a change came from only when that place is a record in this repo: `idea:`
  (a seed), `fixes:` (a `[bug]` entry), `closes:` (a GitHub issue someone filed), `reworks:` (an
  earlier change). A finding the owner made in a host is none of those, so 206 reads the same as a
  change thought of while working on this repo.
- `.sdlc/DIRECTION.md` says under G7 "No pilot project has run it yet, so there is still no
  evidence from a second repo", while changes found in that second repo land every week. The
  retrospective can't tell them apart.
- `PRODUCT.md`'s first bet says "issues from hosts are what would break this", but `retro` counts
  only issues filed on GitHub. A host problem the owner finds and fixes directly never reaches it.
- Seeds carry no origin either. Most host findings land first as a seed through `/sdlc:idea` or
  `/sdlc:bug`, and by the time a change takes one, where it came from is prose, if anywhere.

## Outcome

- An intent's frontmatter can say `origin: host` (found using the plugin in another repo) or
  `origin: self` (found working on this one). `/sdlc:intent` proposes it from the person's account
  or the seed, as it proposes `serves:`, and Step 4's question names it, so the yes covers it.
- `/sdlc:idea` and `/sdlc:bug` write an `Origin: host` line on an entry when the account says so,
  and an intent taking that seed proposes the same origin from `idea:`.
- `/sdlc:close` records it on the `Close` commit as an `Sdlc-Origin: host` trailer, extending the
  metrics contract, never redefining it.
- `/sdlc:retro` counts each window's changes by origin beside the issues filed, and its report
  reads the host-found ones as second-repo evidence for G7 and the first bet.
- **Moves O4:** the retrospective's direction cites how many changes came from a host, not only
  process counts, so "no evidence from a second repo" stops being said while such evidence lands.
- A test closes a change with `origin: host` and finds the trailer; one reads a window holding
  both kinds and checks the counts.

## Affected

- **Area:** intent, idea and bug skills; the change template; close's trailers; `retro`; docs.
- **Files & components:** `templates/intent.md` (the frontmatter key); `skills/intent/SKILL.md`,
  `skills/idea/SKILL.md`, `skills/bug/SKILL.md`; `scripts/closing.py` beside `Sdlc-Fixes:`;
  `scripts/metrics.py`'s trailer docstring; `scripts/retro.py`'s counts and report; `vet` if it
  checks values; REFERENCE.md *Metrics* and *Retrospectives*; `docs/FEATURES.md`; tests.
- **Downstream:** every host's intents and `Close` commits. A host that never uses the line must
  read as it does today; older changes have no origin at all.
- **Contracts:** `templates/` is `[review] irreversible`; the `Sdlc-*` trailer format is extended,
  never redefined; frontmatter is read as text (`frontmatter_list()`); *Nothing about a project or
  a workspace* (the line says `host`, never which host); the retro's `unmeasured`, never `unused`
  (a change with no line is unknown, not `self`).

## Constraints

- The line never names a host: not in the intent, the seed, the trailer or the report.
- A missing `origin:` reads as unknown, never guessed or backfilled into history.
- No new question for the person: intent, idea and bug propose it, and `edit a section` changes it.
- Older changes and hosts that never set it keep working; `vet --strict` doesn't refuse a missing
  line.

## Open questions

- ~~Values: are `host` and `self` enough? Is a filed GitHub issue (`closes:`) its own origin
  (`issue`) or a host one? What of findings from a retrospective or a review?~~ Resolved: two
  values; a filed issue is already on `closes:`, and retrospective, review and nit findings are
  `self` (spec R1)
- ~~Is the line offered to every host, or only meaningful in this repo, since a host's own changes
  always come from its own work?~~ Resolved: offered on every intent in every host, `self`
  proposed when nothing points elsewhere, approved with the spec (R10)
- ~~Does the retro count seeds by origin too, or only landed changes?~~ Resolved: landed changes
  only; a seed's `Origin:` reaches the count through the intent that takes it (spec R8, R10)
- ~~A per-host breakdown would need an opaque label in a gitignored file. Out of scope?~~
  Resolved: out of scope; the line names a class, never a host
- Does 206, already open, get `origin: host` by hand before it ships?
