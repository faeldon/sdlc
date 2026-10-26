---
name: retro
description: Run a retrospective, the outermost loop — look across every change and release since the last one, from counts the script gathers, and make five passes (cost, architecture, process, product, direction). The product pass, when the repo has a product doc, scores its outcomes against the evidence the host's commands print. Each finding becomes a .sdlc/work/inbox.md seed, an intent title, or is dropped with a reason. After one approval, rewrite the direction doc (goals, milestones, the next major release) and the product doc's outcome lines, and commit them with the seeds as "Retrospective YYYY-MM-DD". Use from the main checkout when /sdlc:status says a retrospective is due (after 2 releases, or a major one), or when the direction is unclear. Not for scans or drift (/sdlc:health), not for cutting a release (/sdlc:release), and never for editing code, skills or the process doc.
argument-hint: "[an area to focus on]"
allowed-tools:
  - Read
  - Write
  - Edit
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py retro *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py retro-commit *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry *)'
disable-model-invocation: true
---

# Retro — look across the loops and set direction

The process has three loops. The **change loop** (intent → spec → plan → build → ship → close)
runs once per change. The **release loop** (release, then publish) runs over a batch of closed
changes. This is the third: it runs over the releases and history since the last retrospective and
asks the slower questions: is the process spending effort where a script would do, is the
architecture still the right shape, are the loops working, is the work moving what its users need,
and where should the next stretch of work go.

**It never edits code, skills or the process doc.** What it finds goes back in as seeds in
`.sdlc/work/inbox.md` and intent titles for `/sdlc:intent`, and comes out the other end as changes.
Besides seeds it writes the direction doc, which says where the repo is headed, and, when there is
one, the outcome lines of the product doc (`docs.product`), never its prose.

**This skill is the expensive look, so it keeps to a budget.** Everything that can be counted
comes from `sdlc.py retro`, as one JSON blob. Don't run `git log` or read closed changes' artifacts:
their titles, problems, tiers, impacts, sizes and dates are in that output. The files to read are
the ones Step 1 names, and no others.

## Step 0 — The counts (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py retro
```

Run this from the **main checkout**, on `main`: the record in Step 6 refuses anywhere else. If
`config`'s `work.dir` is inside `.claude/worktrees/`, stop and say so before Step 1.

What `retro` gives:

- `since`: the last retrospective (null: the whole history is in range).
- `changes`: each change closed since then, with id, title, tier, impact, the first paragraph
  of its problem, days open, files and lines (over every commit on its branch; null, with a
  problem, when its start can't be found), `release` (the first release tag holding it, null
  while none does: its users haven't had it yet), `serves` (the outcomes its intent named, `none`,
  or null for no line) and `moves` (its `**Moves O1:**` lines: what should change if it works).
- `rework`: later changes that touched an earlier one's code within days, leaving out
  `rework_common`: the files more than a third of the window's changes touched (once there are
  six), each with how many, since sharing one of them says nothing.
- `open`, `ideas` (open ideas' count, oldest), `tiers`, `impacts`, and `releases` since `since`.
- `nits`: the nits ship left open, `[nit]` entries in `.sdlc/work/inbox.md`, by theme, each theme's
  `count` and its oldest's date and `age_days`.
- `bugs`: the `[bug]` entries and their history in the window. `reported`, `fixed` (from each
  `Close` commit's `Sdlc-Fixes:`) and `retired` (from each `Retire` commit's `Sdlc-Retired:`,
  by reason), `triaged` (the issues triage closed without a change, from each `Sdlc-Triaged:`, by
  verdict), `days_to_fix` (median and max), `open` (oldest first), and `escapes`: each change a
  bug was `Introduced by`, with its tier, and `unattributed`, the bugs no one tied to a change.
- `unmeasured`: signals history doesn't record.
- `prose`: each skill's size, estimated tokens and commands, plus the host docs the skills read.
- `direction`: the current direction doc's goals and milestones by id (`items`, each `open`,
  `done`, `dropped` or `revised`), its format `problems`, the `next_ids` to give new ones, and
  `milestones`: for each open milestone, what every seed and change on its `Groups:` line became
  (a change `closed`, `open` or `unknown`; a seed `shipped` by a change, still `open`, or
  `vanished` with no change behind it). Empty items with no doc, or a doc without ids, means a
  first retrospective.
- `metrics`: what `/sdlc:close` measured on each change in range and wrote on its `Close` commit,
  as medians per tier and way of running (`manual` or `factory`):
  - the four clocks: elapsed (calendar time, never effort), agent, response, and away, with
    blocked apart;
  - stops against the gates `required` and the host's `target`;
  - tokens per stage and per sub-agent role;
  - ship's findings;
  - `in_change`: rework within each change, not the follow-up `rework` above. The first-time
    rate per stage (`first_time`) and for whole changes (`all_first`), the median of each rework
    count, and what spikes cost, kept apart from rework.

  `uncaptured` counts changes close couldn't measure. They're not guessed at.
  Read stops as upper bounds: a harness message that arrives as a plain user entry looks typed,
  so it can count as an `extra` stop.
- `product`: null with no product doc. Otherwise its outcomes by id (`items`, `problems`,
  `next_ids`), and `outcomes`: for each open one, the changes closed since `since` that serve it
  (with `release` and `moves`) and the open changes that do. `unlinked` are closed changes with no
  `serves:` line, `none` the ones that serve no outcome on purpose, `unserved` the open outcomes
  nothing serves, and `stale` the open changes naming an outcome already struck. `evidence` is a
  row per `retro.evidence` command: its `output` (capped, `truncated` when cut), `exit` and
  `error`. What it means is the host's: the script passes it through unread.

`problems` names any change whose intent couldn't be read: report it, don't guess around it.

## Step 1 — Read what sets the lens

`config` says where each is. Read them once:

- **The process doc** (`docs.process`): its stages, tiers and "Signals worth watching". This is
  what "working" means here.
- **The policy doc** (`docs.policy`): the invariants. An architecture finding that needs one moved
  says so.
- **The direction doc** (`docs.direction`), if it exists: what the last retrospective set. The
  first thing this one says is how the repo did against it.
- **The product doc** (`docs.product`), if it exists: who the users are, the problem, the outcomes
  and how each is measured, and the bets. This is what "the right work" means here.
- **The context docs** (`docs.context`): what a session is told about the repo.
- **`.sdlc/work/inbox.md`**: the seeds, so a finding that is already a seed is dropped as a duplicate.
- **Three skills at most**: the three largest by `est_tokens` in `prose.skills` (or by `tokens` sum
  when measured), plus any the argument names. They sit next to this one, in the plugin's
  `skills/` folder.

## Step 2 — Five passes

Each finding is one line: what it is, the evidence from Step 0 or 1, and its disposition (Step 3).

1. **Cost.** Steps a skill does in prose that are deterministic: they read the same inputs and
   reach the same answer every run. Each finding names the skill, the step, what the step decides
   mechanically, the `sdlc.py` command that could do it instead, and its tokens (estimated from
   `prose`, or measured from `tokens`). Also docs every run reads in full when it only needs one
   section.
2. **Architecture.** Structural problems the counts or the docs point at: one file or function
   doing several jobs, a boundary missing (something wired in where it should be behind an
   interface), the same logic in two places. Name the files and say what shape would fix it.
   A code file in `rework_common` is one most changes had to touch: say whether that is a
   boundary missing.
3. **Process.** The process doc's signals, computed: change age, `rework` (naming what
   `rework_common` left out), the tier mix (tier drift: is everything becoming Tier 2?),
   impacts per release. Say what each one says. Also
   each `unmeasured` signal, and whether it's worth a seed to measure it. From `metrics`:
   - where a change's time goes (agent against the human's response, away and blocked);
   - how far stops are above `required` and `target`;
   - which stage or role the tokens pile up in;
   - from `in_change`, which stage most often misses first time and which rework count drives it
     (a spec edited after design is a Stage 2 problem; failed gate runs a build one), and whether
     spikes are buying fewer misses later.

   Say how many changes the numbers rest on, and that `uncaptured` ones aren't in them.

   Then the debt in `nits`: each theme's count and oldest age against the threshold the process
   doc's section on nits sets. A theme past it is a finding whose disposition is one seed to pay
   that theme down in a single change, never a seed per nit. The `[nit]` entries themselves are
   ship's to edit, never this skill's.

   Then `bugs`: what got through. Weigh each escape against the introducing change's tier: a
   Tier 1 that let a high-severity bug through says the tier rule let something risky skip its
   spec; a Tier 2 says its review passes missed a class of failure, which is a finding for the
   review doc, proposed as an intent title. Say how many are `unattributed`, since an escape no
   one tied to a change counts toward neither. A bug open long, or `days_to_fix` growing, is a
   finding whose disposition is the intent that fixes it. Bugs themselves are `/sdlc:bug`'s to
   file and retire, never this skill's.
4. **Product**, only when `product` isn't null. Whether the work is going where the users are,
   judged from `product.evidence` against each outcome's measure in the product doc. Score every
   open outcome in `product.items` the way the direction pass scores its items (done, dropped,
   revised, carried), citing the evidence row that decides it, or saying none bears on it: an
   outcome with no evidence is carried, never done. For each change in `product.outcomes`, say
   whether what its `moves` said should change did, and note a `release` of null: its users
   haven't had it, so no evidence can show it yet. Then name the `unserved` outcomes, the `stale`
   changes, anything the evidence shows users need that no outcome or seed covers, and the bets
   the evidence breaks. A share of `none` and `unlinked` that keeps growing is a finding too.
   Name every outcome by its id and its `name` from `product.items`, as `O1 (Unaided setup)`:
   an id alone means nothing to someone without the doc open. With no product doc, skip this pass
   and say so in Step 7.
5. **Direction.** First, close the loop: score every `open` item in `direction.items`, for *Since
   the last retrospective*, as one of:
   - **done**: struck `~~…~~ Done: <evidence>`, citing the change or release (a milestone whose
     `milestones` rows are all `closed` or `shipped` is the usual case);
   - **dropped**: struck `~~…~~ Dropped: <reason>`;
   - **revised**: struck `~~…~~ Revised → <new id>: <reason>`, with the new item written beside it;
   - **carried**: left open, saying what's left. Partial progress is carried, never "partly done".

   A `vanished` seed is worth saying out loud: it left `inbox.md` with no change behind it. Then,
   given the above and the product pass first of all, propose up to three open goals and the milestones that reach them, new ones
   numbered from `next_ids`. Each milestone says what is true when it's done and has one `Groups:`
   line naming its changes and seeds, each seed by its id. Then say what the next **major** release would contain (the
   process doc's `impact:` table: users have to change what they do), or that none is planned.

## Step 3 — Give each finding a disposition

Every finding ends in exactly one of these, or it doesn't go in the report:

- **Seed**: a `.sdlc/work/inbox.md` entry, `## [<id>] [idea] Title`, with a short paragraph: the
  problem, the evidence, and "Raised by the retrospective of YYYY-MM-DD." A finding that comes in
  phases is one seed per phase, each later one with an `After: <earlier seed's id>` line, so
  `/sdlc:status` puts forward only the phase that's next.
- **Intent**: a proposed title for `/sdlc:intent`, for one that needs a decision now. Don't open it:
  that skill has its own gate.
- **Dropped**: with its reason, which goes under the direction doc's *Dropped findings*.

A finding that duplicates an open change (in `open`) or an existing seed is dropped, naming which.

## Step 4 — Draft and show it

Draft the whole direction doc from `templates["direction.md"]` in `config`, every section filled
and no `<` prompt line left, and every new seed exactly as it will be appended, with its id. Take
the ids for all of them in one call, `<N>` being how many:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry --count <N>
```

Every id the current doc has open is still there, open or struck with its status; one already
struck may be left out. With a product doc, draft its outcome lines the same way: each open one carried or
struck with its status, new ones numbered from `product.next_ids` with a short bold name
(`- O5. **<name>.** …`), and every other line of it
left exactly as it is. A change to its users, problem, measures or bets is the human's: propose it
as an intent title. Show each doc's changes, followed by the intent titles, and list the status
changes first: they are the decisions this approval makes.

## Step 5 — WAIT for explicit approval

Ask literally:

> `Write <docs.direction> with these <K> status changes (done, dropped, revised), append these <N> seeds to .sdlc/work/inbox.md, then commit both as "Retrospective <today>"? (yes / revise / no)`

When the product doc's outcome lines change too, name it: `Write <docs.direction> and the
outcomes in <docs.product> with these <K> status changes…, then commit all three as…`.

**Write nothing until the human says yes.** Approval is for this draft only: after a revision, show
it again and ask again.

## Step 6 — Write and record it

`Write` the direction doc at the `docs.direction` path, `Edit` the product doc's outcome lines as
approved, and `Edit` the register to append the seeds after its last entry. If it doesn't
exist, `Write` it at that path first from `templates["inbox.md"]` in `config`, as it is, then
append. **The register is the file `config`'s `work.register` names:** `.sdlc/work/inbox.md`.
Write entries there, never into a second file beside it, which would hide every entry the first
one holds. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py retro-commit
```

It commits exactly those files as `Retrospective <today>`, and refuses (writing nothing) when
anything else in the tree is changed, when it isn't the main checkout on `main`, when today
already has one, or when a new doc drops a goal, milestone or outcome the committed one left open,
or breaks the id format. A refusal naming an id means the draft lost it: put it back, carried or
struck with its status, show the change and ask again. That commit is the next retrospective's
boundary.

## Step 7 — Report and stop

Give the commit, the direction doc's path, the status changes, the seeds added, and the proposed
intent titles with `run /sdlc:intent to open it`. With no product doc, end with: `No product doc,
so no product pass: run /sdlc:setup product to add one.` Then stop.

## Out of scope

- Editing code, skills, the process doc or the policy doc: that's a change, through `/sdlc:intent`.
- Editing the product doc's users, problem, measures or bets: only its outcome lines.
- Quoting evidence output into the direction doc, the product doc or `.sdlc/work/inbox.md`: findings
  are written in this skill's own words, and a line of evidence goes in only when the human
  approves that line at the WAIT. Evidence can hold what a host's users did.
- Opening intents, cutting releases, pushing anything.
