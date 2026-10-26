---
name: idea
description: File an idea in .sdlc/work/inbox.md, or edit or retire one — takes the idea in the person's own words, checks the register for one that already covers it, drafts the entry with an id from next-entry (and an After line when it follows another seed), and after one approval commits the inbox alone on the base branch as "File <id>", "Update <id>" or "Retire <id>". Use from any checkout, a change's worktree included, when someone has an idea for later. Not for something already broken (/sdlc:bug files it), not for building the idea (/sdlc:intent <id> opens the change), and never for editing code.
argument-hint: "[the idea, or an entry's id to edit or retire]"
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

Read the register, the file `config`'s `work.register` names. If an entry already covers the idea,
say which and ask whether to sharpen that one instead: one idea, one entry.

## Step 1 — Take the idea in the person's words

Ask only about what the human hasn't said:

- **What it is**, and **why it's worth doing**: the problem it answers, or what it would let
  someone do.
- **What it waits on**: another seed it follows, by id. That becomes an `After: <id>` line.

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
Raised <today's date>.
```

For an edit, the entry as it becomes; for a retirement, the entry and its reason.

## Step 4 — WAIT for explicit approval

Ask literally, with the entry's id and what happens to it:

> `Append this idea to .sdlc/work/inbox.md as <id> and commit it as "File <id>"? (yes / edit it / no)`

For an edit: `Change <id> in .sdlc/work/inbox.md as shown and commit it as "Update <id>"?`; for a
retirement: `Remove <id> from .sdlc/work/inbox.md as <reason> and commit it as "Retire <id>"?`

**Write nothing until the human says yes.** Approval is for this entry only.

## Step 5 — Write and record it

**The register is the file `config`'s `work.register` names:** `.sdlc/work/inbox.md` in this
checkout. Write entries there, never into a second file beside it, which would hide every entry the
first one holds.

`Edit` the register as approved: append a new entry after the last one, change an edited one in
place, or delete a retired one from its heading to the line before the next `## `. If it doesn't
exist, `Write` it at that path first from `templates["inbox.md"]` in `config`, as it is, then
append. Then:

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
- Pushing. Only `/sdlc:publish` pushes.
