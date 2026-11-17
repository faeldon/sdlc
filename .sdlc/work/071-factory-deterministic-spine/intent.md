---
id: 071
slug: factory-deterministic-spine
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
serves: [O6]
---

# 071 — Say the factory runs on the manual process as its deterministic spine

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A host deciding whether to trust the factory can't see from the docs what stays mechanical when
agents take over. `README.md`'s factory bullet says it "hands a change's spec, build and review to
agents working in rounds, behind the same approvals". `plugins/factory/README.md` opens with "Where
`sdlc` has a person drive every stage of a change, this hands … to agents". Both present the
factory as a second way to run a change. Neither says that the factory runs on the manual process
itself: the same deterministic core of `sdlc.py`'s stages, `check`, the base branch's
`[review] sensitive` depth, ship's one commit and close's landing.

The factory doesn't work around that core. It puts agents into the judgment slots of the manual
process: drafting the spec, building, reviewing. The mechanism and the gates around those slots
stay the same code a person runs by hand. That's the reason its autonomy can be trusted, and the
docs never say it. No doc names "manual mode" either. The only nearby term is "manual medians", in
`.sdlc/PRODUCT.md` and `.sdlc/DIRECTION.md`.

## Outcome

- `plugins/factory/README.md` says, near the top and in "Where it sits", that the factory runs on
  the manual process as its deterministic spine. It lists which parts stay mechanical and the
  person's: stages and artifacts checked by `sdlc.py`, review depth from the base branch's config,
  ship's WAIT and its one commit, close. It also names which slots the agents fill.
- `README.md`'s factory bullet says the same in a sentence and uses the same name for the manual
  process, "manual mode".
- A reader can tell from either doc that a change the factory built passes through exactly the
  checks and gates of one built by hand.
- **Moves O6:** a host can say what the factory leaves deterministic before it runs one, so its
  first factory change starts from known gates instead of an unknown agent loop.

## Affected

- **Area:** docs only.
- **Files & components:** `plugins/factory/README.md` (intro, "Where it sits"), `README.md` (the
  factory bullet in the optional features, and the line naming the two plugins if needed).
- **Downstream:** readers of the docs: hosts weighing the factory, and contributors. Nothing parses
  these files.
- **Contracts:** none. `test_nothing_local.py` applies, so the docs use neutral wording.

## Constraints

- What's described must be true of the code today: what `factory.py`, the factory skills and
  `sdlc.py` actually do. No claimed guarantee the code doesn't make.
- 070-factory-supervisor rewrites the same factory paragraphs. This change stays independent of
  it, and whichever change lands second rebases over the other's wording. 070 landed first, and
  this change is rebased over it: the spine sits beside its supervisor wording.
- Say each thing once: the factory README carries the detail, and `README.md` points to it.

## Open questions

- ~~Is "manual mode" the name to use everywhere, or should the docs say "the manual process" /
  "`sdlc` by hand"? Should `AGENTS.md` and `.sdlc/PRODUCT.md`'s "manual" follow later?~~
  Resolved: "manual mode", defined once in the factory README's opening and used in `README.md`'s
  bullet. `AGENTS.md` and `.sdlc/PRODUCT.md` stay out of scope; their "manual" already reads the
  same way.
- ~~Does the existing ASCII diagram in "Where it sits" show the spine, for example with the `sdlc`
  steps as a line the agent slots hang from, or does prose carry it?~~ Resolved: prose carries it,
  a list under the section's lead; the diagram is unchanged.

## Approach

Rewrite the factory README's opening paragraph and the lead of "Where it sits" around the spine:
manual mode is the deterministic core, and the factory fills its judgment slots with agents. Add a
short list of what stays mechanical and gated, each item naming the code or skill that enforces it,
and check each item against `factory.py` and `sdlc.py` before writing it. Change `README.md`'s
factory bullet to say the same in a sentence and link to the README. Run `./check.sh`.
