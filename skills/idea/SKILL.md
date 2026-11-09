---
name: idea
description: File an idea in .sdlc/work/inbox.md, or edit or retire one — takes the idea in the person's own words, checks the register for one that already covers it, drafts the entry with an id from next-entry (and an After line when it follows another seed), and after one approval commits the inbox alone on the base branch as "File <id>", "Update <id>" or "Retire <id>". Use from any checkout, a change's worktree included, when someone has an idea for later; `--themes`, from the main checkout, proposes a Theme line for every idea and bug lacking one, when status says many do. Not for something already broken (/sdlc:bug files it), not for building the idea (/sdlc:intent <id> opens the change), and never for editing code.
argument-hint: "[the idea, an entry's id to edit or retire, or --themes]"
allowed-tools:
  - Read
  - Write
  - Edit
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py inbox-commit *)'
disable-model-invocation: true
---

# Idea — file what's worth doing later

An idea is something nobody has built yet: a change worth making, said before anyone opens it. It
goes in `.sdlc/work/inbox.md` as a seed, tagged `[idea]`, so `/sdlc:status` can put it forward and
`/sdlc:intent <id>` can open the change that builds it. This skill files one, edits one, or retires
one nobody will build. It never builds anything.

**It writes one file, the inbox, and commits it alone.** Everything else is the script's.

## Step 0 — See what's there (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config
```

Run it from any checkout: ideas come up in the middle of other work. The commit in Step 5 always
lands on `git.base` from `config`, in the main checkout. When `config`'s `work.dir` is inside
`.claude/worktrees/`, the session is in a change's worktree: note it, since Step 5 then names the
entry it files.

**What the argument is**, read in this order: `--themes`, alone, is the themes pass (Step 2); an
entry's id alone (`2026-10-01-2`) is that entry to edit or retire; anything else, a word like
`themes` included, is a new idea in the person's words. No idea starts with `--`.

Read the register, the file `config`'s `work.register` names. If an entry already covers the idea,
say which and ask whether to sharpen that one instead: one idea, one entry.

## Step 1 — Take the idea in the person's words

Ask only about what the human hasn't said:

- **What it is**, and **why it's worth doing**: the problem it answers, or what it would let
  someone do.
- **What it waits on**: another seed it follows, by id. That becomes an `After: <id>` line.

Don't ask for these two; propose the first and take the second only when it's said:

- **Its theme**: a word the register's other entries already use in their `Theme:` lines
  (`tests`, `docs`…), the one closest to the idea, or a new one when none fits. Status groups
  entries by it, so a theme is work that can be taken on together. The person may change it or
  drop it.
- **Its priority**, only when the person says it's urgent (`Priority: high`) or can wait
  (`Priority: low`). Status puts high before everything else and low after it; with no line it
  ranks where its kind does.

Keep their words. Draft it in neutral terms, so it names no host: an idea from another repo says
what the plugin should do, never which repo it came from, or what that repo builds. An idea that
describes something already broken is a bug: say so and stop, `/sdlc:bug` files it.

## Step 2 — Editing or retiring instead

When the argument is an entry's id, or the human wants one changed or gone:

- **Edit** an idea's title or prose in place. Its id stays the same, so whatever names it still
  does.
- **Retire** an idea nobody will build: the reason is one of `duplicate`, `superseded` or
  `declined`, said with a line on why. An idea an open change builds (its `idea:` line, or the
  `[building]` tag) is never retired here: its change removes it at ship, or `/sdlc:drop` says why
  not. A `[bug]` is `/sdlc:bug`'s to retire, and a
  `[nit]` is ship's.

**Themes for what has none**, when the argument is `--themes` (status says `N ideas and bugs have
no theme`). Only from the main checkout: when `work.dir` is inside `.claude/worktrees/`, say that
a worktree's copy of each entry may be older than the main checkout's, which filing from here
would put back, and stop. Otherwise, from the register you read in Step 0, take every `[idea]` and
`[bug]` with no `Theme:` line, leaving out those tagged `[building]`. Propose a theme for each:
a word the register's `Theme:` lines already hold, nits' included, the one closest to the entry;
a new one only where none fits, one word or a short kebab-case phrase, and the same new word for
the entries that share it. This touches a `[bug]` only to add its `Theme:`, the one edit of a bug
that isn't `/sdlc:bug`'s. Skip Step 1.

## Step 3 — Draft and show it

For a new idea, take its id:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry
```

Show the entry exactly as it will be appended:

```
## [<id>] [idea] <title: what it would do, in a few words>

<What it is and why it's worth doing, in the person's words.>
After: <id, only when it follows another seed>
Theme: <theme, unless the person dropped it>
Priority: <high or low, only when the person said so>
Raised <today's date>.
```

For an edit, the entry as it becomes; for a retirement, the entry and its reason. For `--themes`,
one table, a row per entry, which the person may change, drop or merge any row of:

```
id             kind  title                                          theme
2026-10-24-1   idea  UX and UI reviewers for the factory, and how…  factory
2026-10-25-4   idea  A changelog that keeps its own layout          release
```

## Step 4 — WAIT for explicit approval

Ask literally, with the entry's id and what happens to it:

> `Append this idea to .sdlc/work/inbox.md as <id> and commit it as "File <id>"? (yes / edit it / no)`

For an edit: `Change <id> in .sdlc/work/inbox.md as shown and commit it as "Update <id>"?`; for a
retirement: `Remove <id> from .sdlc/work/inbox.md as <reason> and commit it as "Retire <id>"?`;
for `--themes`: `Add these <n> Theme: lines to .sdlc/work/inbox.md and commit them as "Update
<ids>"? (yes / edit a row / no)`.

**Write nothing until the human says yes.** Approval is for this entry only, or for `--themes`, the
rows shown.

## Step 5 — Write and record it

**The register is the file `config`'s `work.register` names:** `.sdlc/work/inbox.md` in this
checkout. Write entries there, never into a second file beside it, which would hide every entry the
first one holds.

`Edit` the register as approved: append a new entry after the last one, change an edited one in
place, or delete a retired one from its heading to the line before the next `## `. If it doesn't
exist, `Write` it at that path first from `templates["inbox.md"]` in `config`, as it is, then
append. For `--themes`, add `Theme: <theme>` to each approved entry after its last `Key: value`
line, or after its prose when it has none, and change nothing else. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py inbox-commit <id> --reason <id>=<reason>
```

The `<id>` only from a change's worktree, and `--reason` only for a retirement. From the main
checkout the script commits the inbox alone, and refuses before writing anything if anything else
there is uncommitted, or an entry is gone without a reason. From a worktree it files the entry it
names into the main checkout's register and commits it there, refusing if the main checkout has
anything uncommitted or isn't on `git.base`, then puts the entry back as it was in the worktree,
which gets it from `git.base` when it next comes up to date. On a refusal, say what it printed and
stop. It never pushes.

## Step 6 — Report and stop

Give the commit, the entry's id, and the next action: `/sdlc:intent <id>` when the human wants it
built now, or nothing, and `/sdlc:status` puts it forward.

## Out of scope

- Building the idea, or opening the change that does: that's `/sdlc:intent <id>`.
- Bugs: `/sdlc:bug` files them. Nits: ship writes those.
- Pushing. Only `/sdlc:publish`, and close and release when `git.push` names them, push.
