---
id: 054
slug: close-runs-cleanup
tier: 2
impact: minor
stage: shipped
created: 2026-11-13
updated: 2026-11-13
shipped: 2026-11-13
idea:
depends_on:
serves: [O3]
---

# 054 — Close runs the repo's cleanup when its gate approves it

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

When a change's worktree leaves things outside git, `/sdlc:close` lists them with
`commands.close_list`. Then, after the close has landed, it ends its report by handing the person
`commands.close_cleanup` (`! make drop {id}` in `docs/REFERENCE.md`'s example) to type
themselves. `skills/close/SKILL.md` forbids it from ever running that command.

That causes two problems:

- **It adds a stop.** The person has already seen the listing and said yes at close's one WAIT.
  Typing the cleanup by hand is then a second stop for something they already looked at, which
  works against O3.
- **It gets skipped.** The command comes last in a long report, after the push, measure and
  `reaches` lines. People skip it, so what worktrees leave behind (caches, scratch databases,
  containers) piles up across closes.

Close was made this way on purpose. A cleanup deletes things, and the seed `[2026-10-25-7]`
repeats it ("`close_cleanup` stays the person's to run"). That reasoning still holds for a cleanup
nobody approved. It does not hold for one the person approves at the gate, with the command shown
in front of them.

## Outcome

- A host can say in `.sdlc/config.toml` that close runs its cleanup itself. With that set, close's
  WAIT question names the exact command, `{id}` filled in. A `yes` runs it as one of close's own
  steps, reported in `done` like the others. Nothing else runs it.
- Once turned on, it runs on every approved close, whether or not `close_list` found anything and
  whether or not the repo sets a `close_list`.
- When the setting is off or missing, close behaves exactly as it does today: it hands the person
  the command and never runs it. Existing hosts see no difference.
- A cleanup that fails doesn't fail the close. The change has already landed, just as with
  `push_failed`. The report says the cleanup failed, gives the reason, and hands the person the
  command to run again.
- Tests pin each part: the question names the command only when the setting is on, nothing runs
  without the approved close, and a failed cleanup is reported without undoing what landed.
- **Moves O3:** a close in a host that sets `close_cleanup` takes one stop, its WAIT, instead of
  the WAIT plus a hand-typed command afterwards.

## Affected

- **Area:** closing: `cmd_close()` and its steps, the close skill's Step 1 and WAIT question, and
  the config schema.
- **Files & components:** `scripts/sdlc.py` (config default and the step in `cmd_close()`),
  `skills/close/SKILL.md` (Step 1, Step 2's question, Step 4, and Out of scope),
  `docs/REFERENCE.md` (the `[commands]` keys), `tests/test_sdlc.py`, and `tests/test_skills.py`
  (including the `close_cleanup` assertion and `READS_CONFIG`). Possibly
  `RETIRED_KEYS`/`TEMPLATE_READS` if the key's meaning moves, and `/sdlc:setup` if it should ask.
- **Downstream:** every host that sets `close_cleanup`. Some write it with a leading `!` because it
  was meant to be typed into a session. Sessions and hosts running the plugin from a clone also
  pick up the new close step and skill text.
- **Contracts:** close's WAIT step (always Tier 2). Nothing runs unasked. Only named steps push or
  delete: today the only thing close deletes is the change's own folder, worktree and branch.
  Logic that a permission rule must cover goes in the script, not in a skill's bash. The Windows
  rules apply: `_sh()` for a host's command, with `encoding="utf-8"` and `errors="replace"`.

## Constraints

- Off by default. A host that doesn't opt in keeps today's behaviour and today's meaning of
  `close_cleanup`.
- It runs only behind close's own `yes`, for that change, with the command shown word for word in
  the question. Turning it on in config doesn't count as approval.
- It runs only after the change has landed and its folder has left `main`, never before the
  merge, so a cleanup can't destroy work that hasn't reached `main` yet.
- A failed cleanup never turns a landed close into a failed one, and a rerun of close doesn't run
  a cleanup that already succeeded a second time.
- It must be possible to read the setting from the base branch's config, so a change can't turn
  on its own cleanup.

## Open questions

- ~~What shape should the setting take? A boolean beside `close_cleanup`, a list in the style of
  `git.push` naming the steps that run, or a new key so `close_cleanup` keeps its "never run by a
  skill" meaning?~~ Resolved: a new boolean, `commands.close_cleanup_runs`, off by default;
  `close_cleanup` stays the command, whoever runs it.
- ~~Should the script run it (a `cleanup` step in `cmd_close()`, so permission rules cover the
  script alone) or the skill's bash (which needs an `allowed-tools` rule for a command that
  writes)? Per AGENTS.md, probably the script.~~ Resolved: the script, as close's last step.
- ~~Where does it go among close's steps: before or after `remove worktree`? Some cleanups need the
  worktree gone first (containers or mounts bound to it), and others need it still there.~~
  Resolved: last, after `delete branch` and `push`, when nothing of the change is at stake.
- ~~What should happen to a `close_cleanup` written with a leading `!`: strip it, refuse it, or have
  `check` report it?~~ Resolved: stripped before running, since `sh` would read it as negation.
- ~~Does it also run when closing a dropped change?~~ Resolved: yes.
- ~~Should `/sdlc:setup` ask about it when a host sets `close_cleanup`, and does `measure` need to
  count the stop this saves?~~ Resolved: neither; setup asks about neither close command today.
