---
name: intent
description: Open a new change to this repo by capturing why it's worth making — interviews the human, drafts work/NNN-slug/intent.md (Stage 1 of the repo's process doc), gates on confirmation, then stops. Use when the human wants to start, propose or formalize a change to the code, config or tooling in this repo, or to promote a work/ideas.md seed into committed work.
argument-hint: "[what the change is about, or the path to a brief file]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - EnterWorktree
  - 'Bash(cd *)'
  - 'Bash(git rev-parse *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py new *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py lookup *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits *)'
disable-model-invocation: true
---

# Intent — open a change to this repo

Stage 1 of the repo's change process. Produces one artifact, `work/NNN-slug/intent.md`, which
records **why** a change is worth making in the human's own words — problem, outcome, what it
touches, what constrains it, what's still unknown.

**This skill stops at Stage 1.** It does not design, does not plan, and does not write any code. An
intent with open questions is a finished intent; resolving them is Stage 2's job. The single most
common way to get this wrong is to helpfully start building once the intent is clear — don't.

## Step 0 — Orient (mechanical, no confirmation needed)

```bash
cd "$(git rev-parse --show-toplevel)" && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config
```

`config` names the repo's process doc (`docs.process`) and its policy doc (`docs.policy`). Read the
process doc if it isn't already in context — specifically its tier table, since Step 2 depends on
it. If `config` reports it doesn't exist, use the tiers in Step 2 as they stand and say so. Skim
`work/ideas.md`, if there is one, for a seed that matches what the human is describing. Note
`docs.project.fields` too: the issue fields the repo's project doc turns on, which Step 1 asks
about. Empty is the usual answer, and then there is nothing to ask. Note whether
`docs.product` exists, and its `outcomes`: with a product doc, Step 1 asks what the change serves.
Note `git.base` too: the branch every change starts from, `main` unless the repo's is another.
Where this skill says `main`, it means that branch. When it is null, stop here and say why: `new`
refuses without one, and `/sdlc:setup` sets it.

**`work/` is committed**: each change's folder lives on its own branch, in its own worktree, and
open changes in other worktrees are listed by `status`. If `config` says `work.ignored: true`, stop
here and say why: `new` refuses while `work/` is in `.gitignore`, and better now than after the
human has approved a draft.

If an open change already covers this, say so and ask whether to extend that intent instead of
opening a second one. Two intents for one change is the failure this step prevents.

## Step 1 — Interview

Ask about whatever the human hasn't already told you. Keep it to the gaps — they've usually just
explained the problem, so don't make them repeat it.

**A brief can arrive as a file.** If the argument is a path to a readable file, `Read` it as the
human's own answers: pre-fill whichever sections below it covers, quote it rather than rephrase it,
and interview only about what it leaves open. A `tier:` line in a brief is a proposal for Step 2,
not a decision, and the gate in Step 4 is unchanged — a brief answers questions, it doesn't approve
anything.

The sections are the intent template's (`templates["intent.md"]` in `config`). When its `source` is
`host`, read it: the repo's own prompts say what it wants in each section.

- **Problem** — what's wrong today, concretely. Which file, which component, which result nobody
  trusted. If this came from an incident or a surprise, get the specifics: what, when, how much.
- **Outcome** — what's true when it's done, stated so it could be checked: a test that passes, a
  command whose output changes, a figure that matches.
- **Affected** — which part of the repo, and **what reads it**. Something with users is a different
  change from something with none; ask who or what is downstream, because that is what decides the
  tier as often as the size of the diff does. Ask too whether it waits on another open change
  (`status` lists them): each one goes on the frontmatter's `depends_on:` line by id,
  `depends_on: [003]`, and a tracker that links issues shows it as blocked by that one.
- **Constraints** — what must not break. The policy doc's invariants are the first place to look.
- **Open questions** — what they don't know yet. Record these; do not resolve them here.

**Issue fields**, only when `docs.project.fields` names some. Read the project doc
(`docs.project`): its prose says how this repo chooses each one. Then list what each can be:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py lookup
```

Ask for each field with the `values` it printed as the only options; a milestone takes one, a
project or assignees any number. Never offer or accept a value it didn't print: a milestone or a
login from memory is a guess, and the issue would carry it. When a field's `error` is set, say so,
with the error, and leave that field out.

**What it serves**, only when `docs.product` exists. Read the product doc: its users, problem and
outcomes say what the work is for. Ask which of `docs.product.outcomes` this change serves, with
those ids as the only options, each shown with its `name` beside it, `O1 (Unaided setup)`, so
nobody has to open the doc to know what O1 is, plus `none` for a change that serves no outcome on
purpose (a refactor, process work). Never pick for the human: the retrospective counts these, and
a guess would count as their decision. The answer is a `serves:` line, `serves: [O1]` or
`serves: none`.
For each outcome served, ask what should change for users if this works, and write it in Outcome
as `- **Moves O1:** <what should change>`: the retrospective checks it against the evidence.

Push back once if the problem statement is a solution in disguise ("add a cache" is a solution;
"the report page takes forty seconds to load" is a problem). Then take their answer. If the process
doc names push-backs of its own for Stage 1, make those too.

## Step 2 — Assign a tier

Propose one from the process doc's tier table and say why in a sentence. Where it has none, these
are the defaults:

- **Tier 0** — a typo, a comment, a one-line fix nothing else depends on. No folder at all. Say so
  and stop.
- **Tier 1** — a small, contained change: a field added, a test added, a doc section, a flag.
  `intent.md` only, with an **Approach** section.
- **Tier 2** — anything that changes what something already relied on means, anything an invariant
  in the policy doc comes near, or anything with a live consumer. Gets `spec.md` and `plan.md` too.

When the process doc says some kind of change is **always** a given tier, whatever the size of its
diff, that rule wins over the size of the diff.

When it's otherwise borderline, pick the lower tier. An under-specified Tier 1 that turns out to
need a spec can be promoted by editing `tier:` and running `/sdlc:spec`; an over-ceremonied Tier 2
just doesn't get written.

**Open nits, for a Tier 1 change.** A Tier 2 change's spec weighs these instead. List the nits
earlier ships left open on the paths this change will touch:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits --touching <path> <path>
```

Offer the ones of cost `S`, and any whose theme is the change's own, to take in. Each one taken is
named by id in the **Approach** section; `/sdlc:ship` retires it once the diff fixes it. Nothing
listed is the usual answer, and then there is nothing to say. Never take one in unasked.

## Step 3 — Draft and show it

Write the full `intent.md` body — every section filled, no placeholder text left from the template —
and show it in the conversation. For Tier 1, include the **Approach** section; for Tier 2, delete it.
Show the issue fields chosen in Step 1 above it, as the frontmatter lines they become:
`milestone: "Q4 2026"`, `project: [Roadmap]`, `assignees: [ana, bo]`, and the `serves:` line
with each outcome's `name` in a comment after it: `serves: [O1]  # O1 (Unaided setup)`. The
comment is for the reader of the draft; the line written in Step 5 is `serves: [O1]` alone.

Write in the repo's register: concrete, naming real files, real components and real incidents, and
explaining *why* and not only *what*. Prefer "the export job reads every order twice when a refund
exists, so October's total was 1.8× actual" over "export bug".

## Step 4 — WAIT for explicit approval

Read the number from the tool immediately before asking, never from memory or from what
`/sdlc:status` showed earlier. Other sessions open changes too, and a number shown here is only
the one that would be allocated if nobody else creates one first. When `config` says
`archive.ids_from: github`, the number is the GitHub issue `new` opens, and `next` is GitHub's
likely next number: anyone's new issue or pull request can take it first.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next
```

Ask literally, with that number as NNN:

> `Create this as <tier> change NNN-<slug> (NNN if still free when created), in a new worktree and branch NNN-<slug> off <git.base>? (yes / change the tier / edit a section)`

With `ids_from: github`, say what else a yes does, since it is visible to everyone with access to
the repo: `…NNN-<slug> (NNN if still free when created), opening its GitHub issue with this title
and this intent, in a new worktree…`. The issue shows the intent once Step 5 syncs it, and is
updated again at spec and ship; `/sdlc:close` archives it. With issue fields chosen, name them
too: `…with this title and this intent, in milestone Q4 2026, assigned to ana and bo, in a new
worktree…`.

**Do not write anything until the human says go.** Approval is per-invocation, never standing — the
same gate `/sdlc:spec` and `/sdlc:ship` use, for the same reason.

## Step 5 — Create it

Every change gets its own worktree and branch, both named `NNN-slug` and branched from `git.base`, so
a new session can never land inside another change's branch, and its folder `work/NNN-slug/`
inside that worktree, committed with the change. Run this from wherever the session is — the tool
finds the main checkout itself and takes the number from the change's new GitHub issue, or under a
lock from the counter, which it then writes as `.sdlc/last-id` in the new worktree:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py new <slug> --tier <N> --title "<title>" --worktree
```

It prints the folder's path and the worktree's, and the issue's URL when it opened one. If it
refuses because GitHub can't be reached, stop and say so: it never falls back to a local number,
which could later collide with an issue's. If `config` named a `commands.worktree_setup`, run it from the
**main checkout** next, in a subshell, `(<command>)`, with `{worktree}` replaced by that path — a
worktree lacks every gitignored thing the repo's tools need, and that command is the repo's own
account of what those are. The subshell keeps a `cd` in it from moving this session into the
worktree before `EnterWorktree` does, which would leave close nothing to exit. With none
configured, skip it and say so.

Then move **this session** into the worktree, so the human never has to start another:
`EnterWorktree` with `path` set to the worktree path `new` printed. If the tool isn't available
or refuses, carry on from here and say so in Step 6, which then names the fallback.

Then `Edit` the scaffolded `intent.md` at the folder path `new` printed, inside the worktree, to
replace the template body with the approved draft. Keep the frontmatter the tool stamped, and add
the approved issue fields' lines and the `serves:` line under `depends_on:`, exactly as shown in
Step 3.

If the change came from a `work/ideas.md` seed: set `idea:` in the frontmatter to that entry's
title alone, without its `## `, date or tag (`idea: Keep drafts` for `## [2026-10-01] [seed] Keep
drafts`): `sdlc.py ship` deletes the entry by it. Then `Edit` the entry in the worktree's
`work/ideas.md`: its heading's tag becomes `[building]`, the rest of the heading unchanged, and
`Building in work/NNN-slug/.` becomes its first body line, so the tag lands with the change. Never
put the pointer in the heading. Leave the seed's prose alone.

Then mirror the written intent to the change's issue, which until now says only that it was
opened. With no tracker, or a change that gets its issue at close, it says there is nothing to
sync, which is fine:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync <NNN>
```

If it fails, say so in Step 6 with what it printed: the change is created either way, and
`sdlc.py sync <NNN>` can be rerun.

## Step 6 — Report and stop

Print the id `new` allocated, the issue URL if it opened one, the worktree path, the folder path and
the next action, then stop.
If the id differs from the one Step 4 showed, say so first: another session took that number in
the meantime, and the change is NNN, not the number approved.

The session is now in the worktree, so the next action happens here. Only if `EnterWorktree` didn't
move it, the next action starts with a new session there: `cd "<worktree path>" && claude`.

- **Tier 1** → "start it in plan mode when you're ready; save the approved plan as `plan.md` if it's
  more than a couple of files."
- **Tier 2** → "run `/sdlc:spec` next."

Do **not** continue into Stage 2 or 3 in this same turn. Do not start editing code. This skill's
job ends here.

## Out of scope

- Writing `spec.md` or `plan.md` — that's `/sdlc:spec` and plan mode.
- Running anything against the system the repo builds, or touching its code. This skill creates one
  folder in `work/`, one worktree and its branch, and nothing else.
- Committing. `/sdlc:ship` does that, at Stage 5, with the change's folder in the same commit.
- Deciding the change is a good idea. The human is the product owner; this skill records their
  judgment, it doesn't second-guess it beyond the one push-back in Step 1.
