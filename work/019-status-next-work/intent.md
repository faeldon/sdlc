---
id: 019
slug: status-next-work
tier: 2
impact: minor
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea:
depends_on:
serves: [O4]
---

# 019 — Status recommends what to work on next, not only how to advance what's open

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

"What should I work on next?" is a request I make often, and `/sdlc:status` only answers it for open
changes. With nothing open it says "run `/sdlc:intent`", and the real question (is there a
multi-phase series in `work/ideas.md` I'm partway through, a direction milestone with seeds left, a
bug a host reported, a release or retrospective due?) takes a conversation. On 2026-10-25, with 0
open changes, the honest answer meant weighing 11 unreleased changes, milestones M1–M3 in
`.sdlc/DIRECTION.md` whose remaining groups are seeds, a three-phase intake series (local channel →
bugs register → GitHub triage) with phase one seeded, and four host-raised seeds against release,
publish, close and sync. The skill can't weigh any of it: it is told not to read `work/ideas.md` or
the direction doc, rightly, since its job is to save the tokens that reading costs. So the
information exists and nothing collects it.

## Outcome

- With nothing open, `/sdlc:status` recommends one next item and a short ranked runner-up list, each
  naming its source (a milestone, a seed series, a host-raised bug, release due, retro due, a nit),
  why it ranks there, and the command that starts it, without the skill reading more files than it
  does today.
- With changes open, they still come first, under the existing precedence; the list follows them.
- A test pins the collection: given an ideas register, a direction doc and a nits register, the
  script lists their candidates in a fixed order.
- **Moves O4:** the seeds and milestones a retrospective writes into the direction doc become the
  next changes because status puts them forward, not because someone remembers them; the next
  retrospective sees milestone groups closing between retrospectives instead of being carried.

## Affected

- **Area:** the status skill and the `sdlc.py` reads behind it.
- **Files & components:** `skills/status/SKILL.md` (its precedence, maybe its `allowed-tools`);
  `scripts/sdlc.py` (`cmd_status` or a new read-only subcommand, on `idea_entries()`, `doc_items()`,
  `nit_entries()` and the release and retro-due checks it already has); `tests/test_sdlc.py`,
  `tests/test_skills.py`; `docs/REFERENCE.md` if hosts get a new output or convention.
- **Downstream:** every host that runs `/sdlc:status`. A host with no direction doc, no ideas
  register or no nits must get a list from whatever it has, never an error.
- **Contracts:** status stays read-only and its skill stays a budget (mechanism in the script,
  judgment in the skill); values read as text, never through YAML; a new subcommand needs an
  `allowed-tools` rule written exactly as run, and stays out of anything that runs a host command;
  the nothing-local rule for test data.

## Constraints

- Open changes still outrank anything new: finish what's started before opening more.
- No ranking hidden in code a person can't see or change: the script collects and orders by plain
  rules, the skill names one and says why.
- Nothing invented: an empty register gives an empty list, and then the answer is `/sdlc:intent`,
  as today.

## Open questions

- ~~How does the script know seeds form a series and which phase is next?~~ Resolved: a seed may
  carry `After: "<title>"`, the shape of a milestone's `Groups:` line, and waits while a seed it
  names is still open; a milestone's `Groups:` order is a sequence too (spec R4, R5).
- ~~What counts as a bug before a bugs register exists?~~ Resolved: a `[bug]` tag in
  `work/ideas.md`, ranked first; the register stays its own seed, and this change doesn't wait on
  it (spec R5).
- ~~What is the precedence among the new sources?~~ Resolved: bugs → each milestone's next ready
  seed → next in a series → `S` nits by theme → other seeds, after the skill's existing precedence,
  release due and retro due (spec R5, R10).
- ~~A new `status` section, or a separate subcommand?~~ Resolved: a `■ Next up` section, so no new
  `allowed-tools` rule (spec R1).
- ~~How many items, and what of an old seed?~~ Resolved: at most 5 plus `(+N more)`, each with its
  age; flagging old seeds is deferred until retro's numbers show seeds going stale.
