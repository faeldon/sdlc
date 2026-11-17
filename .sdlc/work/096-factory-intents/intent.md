---
id: 096
slug: factory-intents
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
serves: [O3, O6]
---

# 096 — Intent opens several changes from one run

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In the originator's words: "I will allow creating intents by the model in a factory skill so that
batch intent creation can be possible and fast. I still have to approve the intents." Discussed
further, the batch belongs in `/sdlc:intent` itself, not a factory skill: nothing about opening
several changes at once needs the factory, and a second skill would restate intent's rules.

`/sdlc:intent` opens one change per run. The batch planned on 2026-11-17 shows the cost: ten
changes, grouped from 29 register entries, need ten hand-typed runs, each with its own interview
(empty for a seed the register already describes) and its own WAIT. Each run moves the session into
the new worktree unless the answer is `yes, for the factory`, so the person has to get back to the
main checkout before the next. And `depends_on:` between changes in the batch (wave 2 waits on
`landing-fixes`) only has a number once the earlier change is created, so the typing order matters
and is easy to get wrong. The model drafted the grouping, slugs, tiers and dependencies of all ten
in one reply, and could only hand back ten commands to type.

## Outcome

- `/sdlc:intent` takes several changes in one call: groups separated by `;`, each one or more
  register ids, with an optional `as <slug>`, `tier N` (a proposal, as a brief's `tier:` line is),
  `after <slug>` (another group of the same call) and `— <words>` (the person's own words for that
  change alone). A nit id in a group is taken into its Approach, a bug id goes on its `fixes:`
  line. Ids alone, with no `as` or `tier`, ask the skill to propose the grouping. The batch planned
  on 2026-11-17 is one command:

  ```
  /sdlc:intent
    2026-11-17-31 2026-11-17-32 2026-11-17-33 2026-11-17-34 as landing-fixes tier 1;
    2026-11-17-30 2026-11-17-23 2026-11-17-47 2026-11-17-22 as board-fixes tier 1 — also print the bound port for board --port 0;
    2026-11-17-24 2026-11-17-25 2026-11-17-26 as board-page-fixes tier 1;
    2026-11-17-41 as seeds-marked-by-changes tier 2;
    2026-11-17-40 2026-11-17-43 as factory-start-fresh tier 2;
    2026-11-17-29 2026-11-17-27 as sdlc-docstrings tier 1;
    2026-11-17-35 2026-11-17-36 2026-11-17-39 as landing-does-what-ship-does tier 2 after landing-fixes;
    2026-11-17-37 2026-11-17-38 as landing-follows-main tier 2 after landing-fixes;
    2026-11-17-42 2026-11-17-44 2026-11-17-48 as factory-run-records tier 2;
    2026-11-17-45 2026-11-17-46 as factory-reviewer-coverage tier 2
  ```

  The model can write that command for the person, who pastes it.
- It drafts every intent in full, as a single run writes one (Problem, Outcome, Affected,
  Constraints, Open questions, a Tier 1's Approach; `idea:`, `fixes:`, `closes:`, `serves:`,
  `depends_on:`), and shows them all before it writes anything.
- Nothing is created before the person approves, and the approval names each change, its tier and
  what it serves. A change left out or edited is not created.
- On a yes, each change is created as a single run creates one: `sdlc.py new --worktree` (and its
  GitHub issue under `ids_from: github`), its intent written, its seeds tagged in its worktree,
  `sync`. In dependency order, so each `depends_on:` names the number this run allocated. The
  session stays in the checkout it started in, as with `yes, for the factory`.
- Its report lists each change's number, worktree and issue, and the next command for those with
  nothing to wait on (`/sdlc-factory:build NNN` when they were handed to the factory).
- A single-change run asks and reads what it does today.
- **Moves O3:** opening a batch of N changes stops the person once (or once per dialog of a few),
  not N times; close's stop counts show it.
- **Moves O6:** the model drafts the intents and the person still approves every one before
  anything exists.

## Affected

- **Area:** `skills/intent/` and `scripts/sdlc.py`; sdlc-factory only reads what a batch creates.
- **Files & components:** `skills/intent/SKILL.md`, which names a new side file, `batch.md`, read
  only when the call holds several groups (as ship reads `conflict.md` or `factory.md` only when
  `preflight`'s `branches` names them); an `sdlc.py` command that parses the groups, checks every
  id against the register, orders them by `after`, refuses a cycle, an unknown id or an `after`
  that names no group, and fills each `depends_on:` once `new` has allocated the number it names;
  `tests/test_skills.py` (the WAIT's new form, still one WAIT in a dialog); `docs/REFERENCE.md` and
  README.md where they describe opening a change; `plugins/factory/README.md` and the
  intent-to-factory hand-off (093) where they say a change is handed over one at a time.
- **Downstream:** every host gets a new way to open changes, with or without sdlc-factory; each
  change opened gets a GitHub issue under `ids_from: github`, which everyone with access to the repo
  sees; `/sdlc-factory:build`, `/sdlc:status` and the board read the created folders as they read a
  single run's. The skills' cases (`evals/`) that cover intent.
- **Contracts:** a skill's WAIT (what it approves: always Tier 2 by `.sdlc/SDLC.md`); numbering
  (`ids_mode()`, never a number twice, never a local fallback under `ids_from: github`); mechanism
  vs. judgment; narrow `allowed-tools`; nothing public names the agent.

## Constraints

- Approval is per run, never standing: every intent created was shown and covered by the yes.
- The skill stays `disable-model-invocation: true`: the person types the command, the model may
  only write it for them.
- Drafting is the skill's judgment; parsing the groups, ordering them, allocating numbers, creating
  worktrees and the issue sync are the script's mechanism. Logic a permission rule must cover goes
  in `sdlc.py`, not the skill's bash.
- No `depends_on:` number is written before `new` has allocated it.
- A run that stops partway (GitHub unreachable at the fourth change) leaves the first three created
  and complete, says so, and a rerun never creates them twice.
- A single-change run's question and reading stay as they are; the batch's text lives in
  `batch.md`, so it costs a single run nothing (O5).
- Each intent's Problem is drafted from its entries' own prose: the seeds keep the person's words.
- Nothing the run opens (issues, intents) names the agent.

## Open questions

- ~~One yes for the whole batch, or `AskUserQuestion`'s up to four questions a dialog (one per
  change: yes / edit it / leave it out)?~~ Resolved: one question for the batch, as land asks
  (yes / leave one out / edit one / no); spec R9.
- ~~Is the `;` / `as` / `tier` / `after` / `—` syntax the right one, or should a batch come as a
  brief file (one section a change), which intent already reads?~~ Resolved: the inline syntax,
  which the model writes for the person to paste; a brief file stays the single run's; spec R2.
- ~~Does a batch take the `yes, by hand` / `yes, for the factory` choice once for all, or per
  change? By hand, which worktree does the session end in?~~ Resolved: neither; a batch always
  stays in its checkout, and the report gives each change's next command; spec R10, R12.
- ~~A limit on how many changes one run opens, like `land.batch`?~~ Resolved: no cap; the
  question lists every change and `leave one out` trims it.
- ~~Should a batch accept free-text changes with no register id, or only ids (with `— <words>` to
  add to them)?~~ Resolved: every group names at least one id; a change with no seed goes through
  a single run's interview; spec R4.
