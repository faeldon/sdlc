---
name: intent
description: Open a new change to this repo by capturing why it's worth making — interviews the human, drafts .sdlc/work/NNN-slug/intent.md (Stage 1 of the repo's process doc), waits for approval, then stops. Use when the human wants to start, propose or formalize a change to the code, config or tooling in this repo, or to promote a .sdlc/work/inbox.md seed into committed work, or several groups of seeds into several changes at once (a batch, its groups separated by `;`).
argument-hint: "[what the change is about, the path to a brief file, or a batch: <id> … as <slug> tier <n>; …]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - EnterWorktree
  - EnterPlanMode
  - 'Bash(cd *)'
  - 'Bash(git rev-parse *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py new *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py lookup *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py groups *)'
disable-model-invocation: true
---

# Intent — open a change to this repo

Stage 1 of the repo's change process. Produces one artifact, `.sdlc/work/NNN-slug/intent.md`, which
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
process if it isn't already in context — specifically its tier table and its always-Tier-2 rules,
since Step 2 depends on them: the plugin's guide first (`docs.process.guide`, when `config` gives
one), then the repo's doc, whose blocks stand in for the guide's of the same heading or lead and
add to the rest. If neither exists, use the tiers in Step 2 as they stand and say so. Skim
the register, the file `config`'s `work.register` names, if there is one, for a seed that matches what the human is describing; an
argument that is an entry's id (`2026-10-01-2`, as `/sdlc:status` prints it) names that entry, and
several ids name several, a theme's seeds taken as one change (`status --all` prints the command
for each theme): draft one Problem covering them all. Note
`docs.project.fields` too: the issue fields the repo's project doc turns on, which Step 1 asks
about. Empty is the usual answer, and then there is nothing to ask. Note whether
`docs.product` exists, and its `outcomes`: with a product doc, Step 1 asks what the change serves.
Note `factory.enabled` too: whether `sdlc-factory` is enabled for this repo, read from Claude
Code's settings files, which decides the form of Step 4's question. It is all this skill knows of
the factory. Note `git.base` too: the branch every change starts from, `main` unless the repo's
is another. Where this skill says `main`, it means that branch. When it is null, stop here and say why: `new`
refuses without one, and `/sdlc:setup` sets it.

When `status` printed `■ Setup`, say that line once, as printed, before Step 1, and go on: the
nudge never stops this skill.

**`.sdlc/work/` is committed**: each change's folder lives on its own branch, in its own worktree, and
open changes in other worktrees are listed by `status`. If `config` says `work.ignored: true`, stop
here and say why: `new` refuses while `.sdlc/work/` is in `.gitignore`, and better now than after the
human has approved a draft.

If an open change already covers this, say so and ask whether to extend that intent instead of
opening a second one. Two intents for one change is the failure this step prevents.

**An argument holding `;` is a batch:** several changes, each a group of register ids, opened in
one run behind one question. Read `batch.md`, beside this file, now, and at each step below follow
its section of the same number as well. Without a `;`, there is no batch, and nothing in
`batch.md` applies.

## Step 1 — Interview

For a batch, `batch.md`'s Step 1 replaces this interview.

Ask about whatever the human hasn't already told you. Keep it to the gaps — they've usually just
explained the problem, so don't make them repeat it.

**A brief can arrive as a file.** If the argument is a path to a readable file, `Read` it as the
human's own answers: pre-fill whichever sections below it covers, quote it rather than rephrase it,
and interview only about what it leaves open. A `tier:` line in a brief is a proposal for Step 2,
not a decision, and the approval in Step 4 is unchanged — a brief answers questions, it doesn't approve
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
  `depends_on: [003]`, and a tracker that links issues shows it as blocked by that one. When the
  problem traces to an earlier change, its code or its design, ask which: each one goes on a
  `reworks:` line by id, `reworks: [041]`, the rework `/sdlc:retro` counts. A change that only
  builds on another reworks nothing; ask only when the human's account points back at one.
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
outcomes say what the work is for. Propose the `serves:` line yourself, `serves: [O1]` or
`serves: none` (a refactor, process work), from `docs.product.outcomes`' ids alone: from a brief or
seed first, then what the human said, then the doc's outcomes read against the Problem. When none
of those points at an outcome, propose one anyway, `none` included, marked `inferred`. For each
outcome proposed, draft what should change for users if this works, in Outcome as
`- **Moves O1:** <what should change>`: the retrospective checks it against the evidence. Ask no
question about either. The retrospective counts these as the human's decision, so Step 3 shows
where each came from, Step 4's question names them, and `edit a section` is how the human changes
them; nothing is written before the yes.

**Where it came from**, always. Propose the `origin:` line yourself: `origin: host` when the
finding came from using what this repo makes in another repo, `origin: self` when it came from
working on this one, a retrospective, a review finding or a nit included. Take it from the seed's
or bug's `Origin:` line first (an `Origin: host` on any entry the change takes makes it `host`),
then from what the human said; when nothing points at another repo, propose `self`, marked
`inferred`. The line names a class, never which repo. Ask no question about it: Step 3 shows where
it came from, Step 4's question names it, and `edit a section` is how the human changes it.

Push back once if the problem statement is a solution in disguise ("add a cache" is a solution;
"the report page takes forty seconds to load" is a problem). Then take their answer. If the process
doc names push-backs of its own for Stage 1, make those too.

## Step 2 — Assign a tier

Propose one from the process doc's tier table and say why in a sentence (for each group of a
batch without a `tier`). Where it has none, these
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

Offer the ones of cost `S`, and any whose theme is the change's own, to take in. Each one taken
goes on a `Nits taken in: <id>, <id>` line in the **Approach**; an id written anywhere else is
never taken in, so name a nit elsewhere only to say it isn't. `/sdlc:ship` retires each one taken
once the diff fixes it. Nothing listed is the usual answer, and then there is nothing to say.
Never take one in unasked.

## Step 3 — Draft and show it

For a batch, every change's, as `batch.md`'s Step 3 shows them.

Write the full `intent.md` body — every section filled, no placeholder text left from the template —
and show it in the conversation. For Tier 1, include the **Approach** section; for Tier 2, delete it.
Show the issue fields chosen in Step 1 above it, as the frontmatter lines they become:
`milestone: "Q4 2026"`, `project: [Roadmap]`, `assignees: [ana, bo]`, and the proposed `serves:`
line with where it came from and each outcome's `name` in a comment after it:
`serves: [O1]  # proposed from 2026-10-01-2: O1 (Unaided setup)`, `# proposed from your account:
…` or `# inferred: …`. The comment is for the reader of the draft; the line written in Step 5 is
`serves: [O1]` alone. Show the proposed `origin:` line the same way,
`origin: host  # proposed from 2026-11-20-3`, `# proposed from your account` or `# inferred`;
the line written is `origin: host` alone.
Show the `reworks:` line too when Step 1 named an earlier change, and the `idea:` line when the
change takes several seeds, `idea: [2026-10-24-4, 2026-11-12-2]`. When the seed or bug the change takes on has an `Issue:` line, show a `closes:` line with every
number on it, bare: `Issue: #12, #15` becomes `closes: [12, 15]`. Those are the issues people
filed for it, which the change closes when it lands.

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

> `Create this as <tier> change NNN-<slug> (NNN if still free when created), serving <O1 (Unaided setup)>, <origin clause>, in a new worktree and branch NNN-<slug> off <git.base>? (yes / change the tier / edit a section)`

The `serving` clause names every outcome Step 1 proposed, each with its `name`, or reads
`serving no outcome` for `none`, so the yes visibly covers them; it keeps its place in each form
below, and is left out without a product doc. The origin clause follows it, `found in a host` for
`origin: host` or `found here` for `self`, so the yes covers the origin too; it keeps its place in
each form below, the factory's and the batch's included.

With `ids_from: github`, say what else a yes does, since it is visible to everyone with access to
the repo: `…NNN-<slug> (NNN if still free when created), serving …, opening its GitHub issue
with this title and this intent, in a new worktree…`. The issue shows the intent once Step 5 syncs it, and is
updated again at spec and ship; `/sdlc:close` archives it. With issue fields chosen, name them
too: `…with this title and this intent, in milestone Q4 2026, assigned to ana and bo, in a new
worktree…`.

When `factory.enabled` is false, the question is the one above. For **Tier 1**, end it with plan
mode, so the person doesn't have to ask for it after the yes:
`…off <git.base>, then start plan mode? (yes / yes, without plan mode / change the tier / edit a
section)`. Starting plan mode approves nothing; the plan is approved when plan mode ends. A Tier 2
question stays as it is, ending `(yes / change the tier / edit a section)`: `/sdlc:spec` comes
first.

When `factory.enabled` is true, the question offers both ways to build the change, by hand first,
and `yes, without plan mode` isn't among them. For **Tier 1**: `…off <git.base>, then plan it here
or hand it to the factory? (yes, by hand / yes, for the factory / change the tier / edit a
section)`. For **Tier 2**: `…off <git.base>, then write its spec here or hand it to the factory?
(yes, by hand / yes, for the factory / change the tier / edit a section)`. Each yes approves the
same things: the change, its worktree and its issue. `yes, for the factory` starts no factory run;
`/sdlc-factory:build` asks its own question.

For a batch, ask instead, every change in `order` named with its tier and what it serves:

> `Create these <n> changes in this order, each in a new worktree and branch off <git.base>, <slug> (Tier <t>, serving <O1 (name)>, <origin clause>), …? (yes / leave one out / edit one / no)`

With `ids_from: github`, `, each opening its GitHub issue with its title and intent` follows
`<git.base>`. The yes approves every change it names and nothing else; `leave one out` and `edit
one` are `batch.md`'s Step 4.

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in them
an option in that order, labelled as written, `header` the skill's name, and the frontmatter lines
shown, then `## Problem` and `## Outcome` as they will be written as the `preview` of each yes
option. A preview past 40 lines keeps its approving part and ends "… <k> more lines in <path>", or
"… <k> more lines, shown above" when no file holds them yet. Only a chosen `yes` (or `yes, …`), or a
yes typed in Other, approves; dismissed, empty, timed out or refused is a no. If the tool is
unavailable or refused, ask the same text, answers in parentheses, right after what the preview
holds, and stop.

**Do not write anything until the human says go.** Approval is per-invocation, never standing — the
same gate `/sdlc:spec` and `/sdlc:ship` use, for the same reason.

## Step 5 — Create it

For a batch, `batch.md`'s Step 5 runs this step once a change, in `order`.

Every change gets its own worktree and branch, both named `NNN-slug` and branched from `git.base`, so
a new session can never land inside another change's branch, and its folder `.sdlc/work/NNN-slug/`
inside that worktree, committed with the change. Run this from wherever the session is — the tool
finds the main checkout itself and takes the number from the change's new GitHub issue, or under a
lock from the counter, which it then writes as `.sdlc/last-id` in the new worktree:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py new <slug> --tier <N> --title "<title>" --worktree
```

It prints the folder's path, the worktree's and the main checkout's, and the issue's URL when it
opened one. If it refuses because GitHub can't be reached, stop and say so: it never falls back to
a local number, which could later collide with an issue's. If `config` named a
`commands.worktree_setup`, run it from the **main checkout** next, in a subshell, `(<command>)`,
with `{worktree}` replaced by the worktree's path and `{main}` by the main checkout's — a
worktree lacks every gitignored thing the repo's tools need, and that command is the repo's own
account of what those are. The subshell keeps a `cd` in it from moving this session into the
worktree before `EnterWorktree` does, which would leave close nothing to exit. With none
configured, skip it and say so.

Then move **this session** into the worktree, so the human never has to start another. Unless the
answer was `yes, for the factory`: then the session stays in the checkout it started in, where
the factory's supervisor runs, and every step below writes to the paths `new` printed, as it
always does, never to a path `config` named from here. Otherwise, `EnterWorktree` with `path` set to the worktree path `new` printed. If
the tool isn't available or refuses, carry on from here and say so in Step 6, which then names
the fallback.

Then `Edit` the scaffolded `intent.md` at the folder path `new` printed, inside the worktree, to
replace the template body with the approved draft. Keep the frontmatter the tool stamped, and add
the approved issue fields' lines, the `serves:` line, the `origin:` line and any `reworks:` line
under `depends_on:`, exactly as shown in Step 3.

If the change came from a `.sdlc/work/inbox.md` seed: set `idea:` in the frontmatter to that entry's
id, written bare (`idea: 2026-10-01-2` for `## [2026-10-01-2] [idea] Keep drafts`), or, from
several, to every id as a list (`idea: [2026-10-24-4, 2026-11-12-2]`): `sdlc.py ship` deletes each
entry by it. That line is all that marks a seed taken: `status`, `bugs`, `nits` and `groups` read
it from the open change. Leave the register itself alone, the entry's tag and prose included: an
edit to it on the change's branch would conflict with every inbox commit on the base branch.

If the change fixes a `[bug]` entry, the one its argument named or any the human says it fixes:
add `fixes: [<id>, <id>]` under `depends_on:`, each bug's id, and draft the Problem from the
entry's own description and repro. Leave the entry as it is, tag and all: `status` leaves out a
bug an open change fixes, `sdlc.py ship` deletes it with the fix, and `/sdlc:close` records it on
the `Close` commit as an `Sdlc-Fixes:` trailer, which is how `/sdlc:retro` counts it fixed.

If a seed or bug it takes has an `Issue:` line, add the `closes:` line Step 3 showed under
`depends_on:`, every number of each, so the issues they were filed from close with the change. `/sdlc:ship`
asks about each one before it does, and the `sync` below makes each a sub-issue of the change's
issue and comments on it that the change took it on, so its filer follows the change from now.

Then mirror the written intent to the change's issue, which until now says only that it was
opened. With no tracker, or a change that gets its issue at close, it says there is nothing to
sync, which is fine:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync <NNN>
```

If it fails, say so in Step 6 with what it printed: the change is created either way, and
`sdlc.py sync <NNN>` can be rerun.

## Step 6 — Report and stop

For a batch, `batch.md`'s Step 6 is the report.

Print the id `new` allocated, the issue URL if it opened one, the worktree path, the folder path and
the next action, then stop.
If the id differs from the one Step 4 showed, say so first: another session took that number in
the meantime, and the change is NNN, not the number approved.

Answered by hand (`yes`, `yes, by hand` or `yes, without plan mode`), the session is now in the
worktree, so the next action happens here. Only if `EnterWorktree` didn't move it, the next action
starts with a new session there: `cd "<worktree path>" && claude`.

- **Tier 1**, answered `yes` or `yes, by hand` → call `EnterPlanMode` last, once the session is in
  the worktree: plan mode reads the code, and the plan the person approves when it ends is saved
  as `plan.md` if it's more than a couple of files. If the tool isn't available or refuses, say
  the next step instead, as below.
- **Tier 1**, answered `yes, without plan mode` (offered only without the factory) → "start it in
  plan mode when you're ready; save the approved plan as `plan.md` if it's more than a couple of
  files."
- **Tier 2**, answered `yes` or `yes, by hand` → "run `/sdlc:spec` next."
- **Either tier**, answered `yes, for the factory` → the session stays where it is, and the change
  stays at `stage: plan`, where the factory starts it: "run `/sdlc-factory:build NNN` from the main
  checkout, or hand it to the supervisor already running there. Its builder plans a Tier 1; its
  spec-writer drafts a Tier 2's spec, which its own question approves."

Do **not** continue into Stage 2 or 3 in this same turn beyond entering plan mode, which writes
nothing and approves nothing. Do not start editing code. This skill's job ends here.

## Out of scope

- Writing `spec.md` or `plan.md` — that's `/sdlc:spec` and plan mode.
- Running anything against the system the repo builds, or touching its code. This skill creates one
  folder in `.sdlc/work/`, one worktree and its branch, and nothing else.
- Committing. `/sdlc:ship` does that, at Stage 5, with the change's folder in the same commit.
- Deciding the change is a good idea. The human is the product owner; this skill records their
  judgment, it doesn't second-guess it beyond the one push-back in Step 1.
