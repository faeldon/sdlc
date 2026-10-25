---
name: status
description: Report the current state of this repo's change pipeline (work/ — what's open, at what stage, what's stalled) and recommend the single next action with the command to run. Use when the human asks what's in the SDLC backlog, where a change stands, what to work on next, or what's blocking something. Read-only — it never writes, and hands off to /sdlc:intent, /sdlc:spec, plan mode or /sdlc:ship. Not for the repo's drift scans; that is /sdlc:health.
argument-hint: "[change id, e.g. 003 — omit for the whole pipeline]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check *)'
  - 'Bash(echo *)'
disable-model-invocation: true
---

# Status — where the pipeline stands, and what's next

Stage-agnostic read of `work/`, per the repo's change process. Answers two questions and stops: **what is
open**, and **what should happen next**.

**This skill is a budget, not just a report.** It exists because answering this from scratch costs
thousands of tokens — re-reading the process doc for the stage model, the review for what
shipping involves, and several `intent.md` files to see what each change is waiting on. Everything
needed to answer the common case is in Step 1's output plus the tables below.

**Do not read the process doc, the review, `work/inbox.md`, or any `intent.md`/`spec.md`/`plan.md`**
— not "for context", not "to be thorough". Step 1 is the whole input. The one exception is Step 4.

**Read-only.** Never write an artifact, never edit frontmatter, never advance a `stage:`, never
scaffold a folder, and never start implementing whatever it recommends. It reports and hands off.

## Step 1 — Collect the facts (one call, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status && \
echo "── check ──" && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check --strict; echo "check exit: $?"
```

Run it from wherever the session is: `status` lists the open changes in every worktree, each
from its own branch, and the main checkout's.

That is the entire input. `sdlc.py status` already gives id, tier, stage, age in days, which
artifacts exist, the title, and the counts of undone items and unresolved open questions — don't
go looking for any of it elsewhere.

**`■ Next up` is what comes after the open changes**, so you never need `work/inbox.md`, the nits
register or the direction doc to answer "what's next". The script collects candidates from them
and orders them by a fixed rule: `bug` entries first, then each open milestone's next grouped seed
(`M1 (…)`), then the next seed in a series (`next in series after "…"`), then cost-`S` nits by
theme (`nits`), then every other seed (`seed`). Each line ends with the command that starts it,
`/sdlc:intent <id>` with the entry's id.
A seed already being built, or waiting on an earlier seed in its series, is left out. The lines
below the list say which milestone has nothing left in its groups, and which `After:` lines can
never be met (`⚠`).

**The `~` markers in the artifact column are load-bearing.** `sdlc.py new --tier 2` scaffolds
`spec.md` and `plan.md` from the plugin's templates, so a change whose spec and plan are still
empty forms would otherwise be indistinguishable from a written one. `status` marks each unwritten
artifact — `intent plan~ spec~`. Treat a `~` artifact as absent. `check --strict` stays quiet about
these at `stage: plan` deliberately (a tool whose own `new` produced something that instantly failed
its own check would teach you to ignore the check), so `status` is the only place they surface —
don't re-derive them by grepping for template placeholders, which invites a second threshold that
disagrees with the tool's.

The open-questions count keys on this repo's convention for closing one: strike the bullet and say
how it went (`- ~~Question?~~ Resolved: ...`), as the intent template prompts. A question closed in
prose without the strikethrough still counts, so read the number as a ceiling.

If `check` reports `work/ is gitignored`, the repo isn't set up for the plugin: recommend
`/sdlc:setup`, which says what else is missing, and stop. `/sdlc:intent` would be refused.

If `work/` doesn't exist or `status` reports nothing open, say so plainly, skip Step 2, and pick
from Step 3's precedence: release, retro, then `Next up`, and `/sdlc:intent` only when none of
those apply.

## Step 2 — Map each open change to its next action

Read the stage and tier off the status line; look up the action here. No other source is needed.

| Stage | Tier 1 next action | Tier 2 next action |
|---|---|---|
| `plan` | Build it — plan mode, then implement | `/sdlc:spec NNN` — resolve the open questions first (even if a stub `spec.md` already exists) |
| `design` | *(shouldn't occur — Tier 1 skips design)* | Plan mode against `spec.md`, save as `plan.md`, set `stage: build` |
| `build` | Implement, then `/sdlc:ship NNN` | Implement, then `/sdlc:ship NNN` |
| `test` | `/sdlc:ship NNN` | `/sdlc:ship NNN` |
| `ship` | `/sdlc:ship NNN` | `/sdlc:ship NNN` |
| `shipped` / `dropped` | Nothing — it's closed | Nothing — it's closed |

**Required artifacts by tier** — a change missing one of these is stalled, whatever its stage says:

| Tier | Needs | If something's missing |
|---|---|---|
| 0 | nothing — no folder at all | — |
| 1 | `intent.md` (its **Approach** section stands in for spec and plan) | Fill in the Approach section |
| 2 | `intent.md` + `spec.md` + `plan.md` | `/sdlc:spec NNN` for the spec; plan mode for the plan |

`sdlc.py check --strict` is the authority on mismatches. If it exits non-zero, its problems outrank
everything in this table — lead the report with them.

**Flags worth calling out**, in this order:

- **`check --strict` problems** — a declared stage with no artifact to back it, or an orphan
  `[building]` idea. Always first.
- **Age.** The signal worth watching: an intent sitting at `stage: plan`
  for weeks is an unmade decision, not a queued task. Flag anything ≥ 14 days old, and say that's
  what it means rather than nagging about it.
- **Unresolved open questions on a Tier 2 at `stage: plan`** — that is exactly what `/sdlc:spec` is
  for, so it strengthens the recommendation. On a Tier 1 they're informational; Tier 1 ships with
  them open.
- **Stub artifacts** — a Tier 2 whose `spec.md` or `plan.md` carries a `~`. Say "scaffolded, not
  written", never "has a spec".

## Step 3 — Report

Compact. The status output has already been printed to the human; do not re-list every change line
by line. Give them what the tool didn't:

1. **One line of shape** — how many open, where they're bunched (e.g. "4 open, all at `stage: plan`
   — nothing has been built yet").
2. **Problems**, if `check --strict` failed. Otherwise skip the heading entirely.
3. **Recommended next** — one item, an open change (`NNN-slug`) or a `Next up` line, with a
   sentence on *why it's the one* (unblocks others, smallest, oldest, already half-built, the
   milestone it moves) and the exact command to run.
4. **Runners-up** — at most two, one line each.

Pick the recommendation on this order of precedence, stopping at the first that applies:

1. Anything `check --strict` flags as broken — fix the pipeline before extending it.
2. A change already at `stage: build` or later — finish what's started before opening more.
3. A change in `Ready to close` — `/sdlc:close NNN` lands it.
4. A change others are declared to depend on: nothing that reads a thing can be built, or pointed
   at it, until the thing exists.
5. The lowest tier among the rest of the open changes — a Tier 1 is roughly fifteen lines of
   intent and an afternoon.
6. `Unreleased` lists changes — `/sdlc:release`, from the main checkout.
7. `Retro due` — `/sdlc:retro`, which also settles a milestone with nothing left in its groups.
8. The first `Next up` line — its own command. Runners-up come from the lines after it.

With none of these, recommend `/sdlc:intent`. Don't invent work to fill the report.

## Step 4 — Only if asked: one change in depth

If the human names a change ("what's 004 about?", "why is 002 stuck?"), read **only** that folder's
`intent.md`, and its `spec.md` only if the question is about design. Summarize Problem, Outcome, and
what it's waiting on. Still no writing, and still no process doc.

## Not this skill's job

- **The repo's drift scans** — whatever its configured scan command checks. That's
  `/sdlc:health`, which runs it. A different pipeline entirely; say so and point
  there rather than running it.
- **Doing the work.** Recommending `/sdlc:spec 002` is the deliverable. Running it is the human's
  call.
