---
id: 058
slug: setup-stops-when-complete
tier: 2
impact: patch
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-11-04-7
depends_on:
serves: none
---

# 058 — Setup stops on a set-up repo before reading its first-setup steps

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Every `/sdlc:setup` run reads the whole of `skills/setup/SKILL.md`, 314 lines, about 5,500 tokens,
including the common rerun on a repo that is already set up: after `claude plugin update`, or to
check. Step 0 already says what such a run does: if every `readiness` item is `ok` and `drift` has
nothing in `breaking`, `refresh` or `report`, say so and stop. But by then the model has loaded
Steps 1–3 (learning the repo, the profile round, drafting every doc and settings file), the `reset`
text and Steps 5–6, none of which apply. Nor does the rule quite hold: the plugin's own repo is
set up (`drift`'s three lists are empty), yet `readiness` reports `commands.build` and
`commands.scan` as `missing` because they are unset, by choice, so today's "every item `ok`" never
stops it at all.

The call is also the skill's to make, by comparing two JSON outputs against a prose rule, where
since 056 whether a branch applies is the script's. And `readiness` already has a `ready` field
that means less (the `required` items are fine), which a reader can take for "nothing to do".

The retrospective of 2026-11-04 raised this as M9's next seed, after 2026-11-04-6, which 056
landed.

## Outcome

- `sdlc.py readiness` gains a `complete` field, true only when every item is `ok` (or `n/a`) and
  `drift` has nothing in `breaking`, `refresh` or `report`, pinned by tests for each thing that
  makes it false.
- The first-setup steps (the profile round, the drafts) live in a file beside
  `skills/setup/SKILL.md`, read only when the script says it applies.
- A rerun on a set-up repo with no argument reads `SKILL.md` alone, reports `complete`, lists the
  defaults a repo usually sets, and stops; the skills' cases show it with a grader that fails if
  setup's run reads that side file on a complete fixture.
- `prose_metrics` reports setup's `SKILL.md` well under 314 lines, and a budget test holds it.
- `product`, `project` and `reset` still reach the steps they need, on a complete repo too, and a
  first setup reads the side file and otherwise runs as now.

## Affected

- **Area:** the setup skill and `readiness` in the script.
- **Files & components:** `scripts/sdlc.py` (`cmd_readiness()`, possibly a shared reading of
  `drift`'s lists with `cmd_drift()`, a table of setup's side files like `SHIP_BRANCHES`);
  `skills/setup/SKILL.md` and its new side file(s); `tests/test_skills.py` (side files, budget),
  the `readiness` tests, `tests/test_retro.py` (prose metrics); `evals/setup/` (a grader);
  `AGENTS.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md` where they describe `readiness`.
- **Downstream:** every host's `/sdlc:setup` run, the first skill a new repo runs and the one each
  plugin update sends people to. `readiness`'s JSON, read only by the setup skill; `ready` keeps
  its meaning. Sessions running the plugin from a clone pick up the skill at `/reload-plugins`.
- **Contracts:** the skills invariant (side files are part of their skill, named by `SKILL.md`, no
  gate in them, their commands covered by `allowed-tools`); setup's one WAIT stays in `SKILL.md`;
  nothing writes before it; `readiness` stays read-only (`READ_ONLY`); the Windows rules for any
  new script code.

## Constraints

- A repo that isn't complete never stops early: any `missing` or `warn` item, or anything in
  `drift`'s three lists, sends setup on to the side file. A wrong `true` skips a host's setup
  silently, so `complete` errs towards false.
- `ready` keeps its meaning; `complete` is a new field beside it, not a rename.
- Setup's WAIT and what it approves don't change; Step 4 and the rules binding every run stay in
  `SKILL.md`.
- No new command in the skill: `readiness` carries what it needs, as ship's one `preflight` call
  does.
- `readiness` and `drift` stay read-only and never refuse.

## Open questions

- ~~Does `readiness` compute drift itself, or does a new `setup` lookup combine the two, as
  `preflight` does for ship?~~ Resolved: `readiness` already runs `drift()` for its `drift` item;
  `complete` reads the same result, no new lookup.
- ~~Does a `report` holding only a `guide-changed` note (something to read, not to write) make
  `complete` false, as today's prose rule says, or is it said on a complete repo?~~ Resolved: false,
  as today; `complete` errs towards false.
- ~~`product`, `project` and `reset` need parts of Steps 1–3 on a complete repo: one side file shared
  with a first setup, or one each?~~ Resolved: one, `drafts.md`, read whenever setup isn't stopping.
- ~~What moves besides Steps 1–3 (the `reset` text, Step 5's proof), and what stays because every
  run needs it (the defaults a repo usually sets)?~~ Resolved: `drift`'s explanation, the `reset`
  text and Steps 1–3 move; the WAIT and Steps 5–6 stay; the defaults left unset come from
  `readiness`'s new `unset`.
- ~~Is the side-file decision a table in the script like `SHIP_BRANCHES` (a `branches` part on
  `readiness`), or is one `complete` flag enough for one file?~~ Resolved: the flag; the argument
  is the skill's.
- ~~What budget does setup's `SKILL.md` get?~~ Resolved: 150 lines.
