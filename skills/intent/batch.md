# A batch: several changes from one run

An argument holding `;` opens several changes at once: the batch a person, or the model writing
the command for them, has already grouped. Each `## Step N` here adds to that step of `SKILL.md`
for a batch; the rest of each step holds as it is. One question approves them all, and the
session stays in the checkout it started in: it can enter only one worktree.

## Step 0

Split the argument on `;` into groups, in order. Each group is one or more register ids, then
optionally `as <slug>`, `tier <1|2>`, `after <slug>` (another group of this batch, created first)
and `— <words>` last, the person's own words for that change alone. Keep each group's words aside:
they are that change's answers, and never go on a command line. Propose a slug for each group
without `as` and a tier, by Step 2's rules, for each without `tier`; both show in the question,
where the person can change them. Then read the batch against the register and the open changes:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py groups "<group>" "<group>"
```

One quoted argument a group, its `as` and `tier` filled in and its words removed. It writes
nothing. Each group comes back with its ids' kind (`idea`, `bug` or `nit`), title and `Issue:`
numbers, `created` (an open change already holding its slug: an earlier run of this batch made it,
so `new` is skipped for it), `drafted` (false while that change's intent is still the scaffold
`new` wrote: the earlier run stopped before writing it), and `order`, the order to create them in. **With `refusals`, show each and
stop:** an id the register doesn't hold or an open change already takes, a group with no id, a
tier that isn't 1 or 2, a slug two groups share, an `after` naming no group, a cycle. A change no
register entry describes isn't a batch's: it goes through a run of its own, with its interview.

## Step 1

No interview: each group's entries and words are its answers, as a brief's are. Draft each
Problem from its entries' own prose and its words, quoted rather than rephrased. A question only
the person can answer goes in that intent's Open questions. Propose each group's `serves:` and `origin:` lines
as a single run does, from its entries first.

## Step 2

A nit in a group is taken in: a Tier 1 puts its id on a `Nits taken in:` line in its Approach, a
Tier 2 leaves it for its spec to weigh. List no other nits; the batch took what it names.

## Step 3

Draft every intent in full, as a single run drafts one, and show them in `order`, a section a
change: its slug and tier, its `serves:`, `origin:`, `idea:`, `fixes:` (each bug), `closes:` (each entry's
`Issue:` numbers) and `depends_on:` lines, then its body. A `depends_on:` line shows the group it
waits on by slug, `depends_on: [landing-fixes]`, until Step 5 has its number. Leave out a group
`created` holds with `drafted` true, and say it was made by an earlier run; one with `drafted`
false is drafted and shown like the rest, its number already given.

## Step 4

`leave one out` and `edit one` take the person's answer: run `groups` again without that group, or
with it changed, show its refusals if any (a group whose `after` named the one left out is
refused), redraft only what changed, and ask again.

## Step 5

For each group in `order`, one at a time, skipping one `created` holds with `drafted` true, and
for one with `drafted` false skipping only 2, `new`, at the paths of the change `created` names:

1. When it has an `after`, run `groups` again with the whole batch: its `depends_on` is now the
   number `new` gave the change it waits on. Write that number, and never one from `next` or from
   memory. A null `depends_on` means the change it waits on wasn't made: stop.
2. Create it with `new`, as a single run does, and run `worktree_setup` for it.
3. Write its intent and its frontmatter lines at the paths `new` printed, in its own worktree,
   as a single run answered `yes, for the factory` writes them. The register is never edited.
4. `sync` it.

Never `EnterWorktree`. **A refusal from `new` stops the run there:** the changes made so far are
complete, each with its worktree, issue and intent. The same command run again shows them as
`created` and makes only the rest, writing the intent of any `new` made before the stop.

## Step 6

Report each change in `order`: the number `new` gave it (and that it differs from any shown, when
it does), its issue, its worktree, and its next command: `/sdlc:spec NNN` for a Tier 2 or plan mode
for a Tier 1, each from a new session in its worktree (`cd "<worktree path>" && claude`), or, when
`factory.enabled`, `/sdlc-factory:build NNN` from the main checkout. For one with `depends_on:`,
say it waits on that change landing. After a stop, name the changes made and those not reached,
and that the same command finishes it.
