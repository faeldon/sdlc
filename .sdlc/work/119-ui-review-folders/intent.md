---
id: 119
slug: ui-review-folders
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on: [111]
fixes: [2026-11-17-85]
serves: [O6]
---

# 119 — The ui and ux reviewers each get their own shots folder

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-85:** the factory's ui and ux reviewers can't run at once. Before each one runs,
`factory.py agent` takes the screenshots under `.sdlc/reports/shots/<change>/round-<n>/`, the same
folder for both roles. `_fixture_copy()` copies `[ui] fixture` into its `fixture/` there, and
this repo's `[ui] serve`, `tests/fixtures/board/serve.sh`, builds a scratch repo inside it
(`build.sh <fixture> <fixture>/drafts`). So when both start together, as the build skill says to
start a round's reviewers, the second one finds the first's repo and is refused before it judges
anything: "build.sh: …/fixture/drafts already exists; it builds only a new repo". Seen on
110-board-says-it-plainly round 1, 2026-11-17. The supervisor reran ux alone after ui finished,
and ran every later ui and ux pair one after the other, by hand. Introduced by
106-factory-reviewer-coverage.

## Outcome

- The ui and ux reviewers of one round can start in the same message and both run: neither's
  shots, fixture copy or server touches the other's.
- A test in `tests/test_factory.py` takes a round's shots for both roles at once, with a serve
  command that refuses an existing folder, as `build.sh` does. It fails while they share one.
- **Moves O6:** a round's reviewers run as the skill describes, with no supervisor step between
  them.

## Affected

- **Area:** sdlc-factory's UI review.
- **Files & components:** `plugins/factory/scripts/factory.py` (the shots and fixture paths:
  `_fixture_copy()`, the shots function, `cmd_shots()`), and possibly
  `tests/fixtures/board/serve.sh` and `build.sh`. Also `tests/test_factory.py`, and the factory
  README where it names the shots folder.
- **Downstream:** every factory run with `[ui]` set. The ui and ux reviewers read their shots by
  path.
- **Contracts:** shots stay under `.sdlc/reports/shots/`, which ignores itself, so none reaches
  a commit. A shot that fails still refuses its review, so no reviewer judges a page it couldn't
  see.
- **Waits on:** 111, which reworks the same server code (`_up()`, the port retry).

## Constraints

- A host's `[ui] serve` command doesn't change: the fix is in the folder the factory hands it.
- The two roles' shots stay findable by each reviewer, as today.

## Approach

Give each role its own shots folder for the round, `round-<n>/<role>/`, so each gets its own
fixture copy and server. That's the smallest change, and it also keeps one role's shots from
overwriting the other's. Update wherever the ui and ux prompts name their shots folder. Pin it
with the test above, the serve command being a stub that refuses an existing `drafts` folder.

## Open questions

- Should the two roles share one set of screenshots, taken once, rather than each taking its
  own? That halves the server starts, but needs a lock or an order between them.
