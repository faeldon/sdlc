---
id: 227
slug: docs-reviewer
tier: 2
impact: minor
stage: shipped
created: 2026-11-22
opened: 2026-11-22T01:18Z
updated: 2026-11-22
shipped: 2026-11-22
idea:
depends_on:
serves: [O6]
---

# 227 — A docs reviewer checks that a diff leaves no doc saying something false

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Whether the docs still tell the truth after a change is one pass of five in the factory's code
reviewer (`plugins/factory/agents/reviewer-code.md:59`, *Context*), beside correctness, contract,
readability and cost, and it reads only `[docs] context` (here AGENTS.md, README.md,
docs/REFERENCE.md, docs/CONTRIBUTING.md). The code reviewer is already the widest prompt the factory
runs, and docs lose to code inside it. Three runs on 2026-11-21/22 show it:

- 222-parked-changes: its approver wrote that "round 2's code reviewer did not review the docs the
  rework touched", and handed the README and REFERENCE prose to the person as a look (D6); the same
  prose was the requirement (R18) that ended its first run as untestable.
- 220-base-ci-red and 222's acceptance checks are hand-written greps over CONTRIBUTING, REFERENCE
  and AGENTS.md: people writing checks to prove the docs were updated.
- `docs/RETRO-SCORECARD.md`'s 36 `Status:` lines went stale across waves 0–6 unnoticed; it isn't
  on the `context` list, and nothing else reads it (226 cleans it up).

Docs beyond the context list (`docs/`, the factory's README, a future documentation site) have no
reviewer at all.

## Outcome

- A `docs` reviewer joins a factory round whose diff could make a doc false, at either depth, and
  returns `- CHANGE: [docs] <file>:<line>: what it says, what is now true, and the edit` for each,
  at the Context pass's bar: only what is now false, or what a future reader needs and can't find;
  wording it could merely improve is a nit at most.
- The docs it reads come from config, so a docs site's source folder is one line in the base
  branch's `.sdlc/config.toml`, and a host with none set gets today's `[docs] context` list.
- The code reviewer no longer has a Context pass, so the two never raise the same line.
- `/sdlc:ship`, for a change built by hand, gets the same pass from a core agent beside
  `sdlc:security`, `sdlc:ui` and `sdlc:ux`.
- A host that has set its own factory `reviewers` list still has its docs checked after upgrading.
- **Moves O6:** a factory change no longer hands its docs to the person as a look, or as an
  acceptance-check grep, because a reviewer already read them.

## Affected

- **Area:** the factory's review loop, ship's review passes, and config.
- **Files & components:** `plugins/factory/agents/reviewer-code.md` (its Context pass goes), a new
  `plugins/factory/agents/reviewer-docs.md`, a new core `agents/docs.md`; `factory.py`'s reviewer
  roster, `verdicts`' `missing` and the join rule (as the ui and ux reviewers join); `sdlc.py`'s
  `config` (the docs list), `context` and `preflight`'s `passes`; `docs/REFERENCE.md`,
  `plugins/factory/README.md`, `docs/FEATURES.md` (a new review pass), the skills' cases if a
  WAIT's preview names the reviewers.
- **Downstream:** every host that runs the factory or `/sdlc:ship`: one more agent run in the
  rounds it joins, and a reviewer list whose meaning shifts.
- **Contracts:** *A change to what something a host already has means* (a host's `reviewers` and
  `[light] reviewers`, and `[docs] context`); the core agents have `Read`, `Grep` and `Glob` and
  nothing that writes; mechanism vs judgment: the script lists the docs and the stale path
  references (`sdlc.py context` already does), the agent judges.

## Constraints

- No agent that judges gets Write; the docs reviewer edits nothing.
- A host that sets nothing new keeps every doc it is checked on today.
- Its cost stays small: sonnet, and only in rounds whose diff can make a doc false.

## Open questions

- ~~Which diffs call it in: anything outside `tests/`, a path a doc names, or a list the host sets
  (as `[ui] paths`)?~~ Resolved: spec R4, clauses (a)–(e): a reviewed doc changed or naming a
  changed path, a `CLAUDE.md`/`AGENTS.md` above one, an earlier round that ran it, or any path
  outside `tests/` and the change folder.
- ~~One key or two: does the reviewer read `[docs] context` plus a new key for user-facing docs, or
  one list for both?~~ Resolved: two, `[docs] context` plus a new `[docs] reviewed` (spec R5).
- ~~Does it join on its own (like ui and ux), or go into the default `reviewers` lists, and what
  happens for a host whose list names `code` alone?~~ Resolved: on its own, whatever the lists
  say (spec R3, R11).
- Does it also check that a doc doesn't say what the code or another doc already says, or only
  that nothing is false?
- ~~At ship, does it run on every diff, or only beside the fresh reviewer on a sensitive one?~~
  Resolved: wherever R4's (a), (b), (c) or (e) holds, at any depth (spec R9).
