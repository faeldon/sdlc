---
name: bug
description: File a bug in work/inbox.md, or retire or retag one — interviews for what broke and how to reproduce it, takes an id and a severity from the process doc's words, offers the change that last touched the code as its `Introduced by:`, and after one approval commits the inbox alone as "File <id>", "Retire <id>" or "Update <id>". Use from the main checkout when something already shipped is broken, or a bug turns out to be a feature request or a duplicate. Not for something nobody has built yet (an idea, which /sdlc:retro or a person writes), not for fixing the bug (/sdlc:intent <id> opens the change that does), and never for editing code.
argument-hint: "[what broke, or an entry's id to retire or retag]"
allowed-tools:
  - Read
  - Write
  - Edit
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py bugs *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py bug-commit *)'
disable-model-invocation: true
---

# Bug — file what's already broken

A bug is something that shipped and is broken, with a way to see it. It goes in `work/inbox.md`
beside the seeds, tagged `[bug]` and given a severity, so `/sdlc:status` puts it first and
`/sdlc:retro` can count it. This skill files one, retires one that turned out not to need a fix,
or retags an entry that was filed as the wrong kind. It never fixes anything: the fix is a change,
opened with `/sdlc:intent <id>`, which links it with `fixes:`.

**It writes one file, the inbox, and commits it alone.** Everything else is the script's.

## Step 0 — See what's there (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py bugs
```

Run this from the **main checkout**, on `git.base` from `config`: the commit in Step 5 refuses
anywhere else. If `config`'s `work.dir` is inside `.claude/worktrees/`, stop and say so. `bugs`
lists the open bugs and `severities`, the process doc's words for how bad one is (`docs.process`,
its section on bugs), most severe first. If the bug is already listed, say which and stop: one bug,
one entry.

## Step 1 — Ask what broke

Ask only about what the human hasn't said:

- **What happens**, and what should happen instead.
- **How to see it**: the command, the input, the steps. A bug nobody can reproduce yet is still
  filed, saying so.
- **Where**: the paths it lives in, as far as anyone knows.
- **How bad**: one of `severities`, with the process doc's meaning for each beside it. Never pick
  for the human.

Write it so it names no host. A report from another repo says what the plugin did, never which
repo it was in, or what that repo builds.

**Where it came in.** With the paths known, ask the script which change last touched them:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py bugs --introduced <path> <path>
```

Offer what it names as the bug's `Introduced by:`, and write the line only when the human
confirms one. `/sdlc:retro` counts escapes per introducing change against its tier, so a guess
written down would count as a finding. A path it names no change for was last touched outside a
change, and gets no line.

## Step 2 — Retiring or retagging instead

When the argument is an entry's id, or the human wants one gone or moved:

- **Retire** a bug that needs no fix: the reason is one of `duplicate`, `not-a-bug`, `wontfix`
  or `cant-reproduce`, said with a line on why. A bug fixed by a change is never retired here:
  `/sdlc:ship` removes it with the fix.
- **Retag** an entry filed as the wrong kind: a `[bug]` that is really a request becomes a
  `[idea]`, and an `[idea]` (or an older `[seed]`) that describes something broken becomes a
  `[bug]` with its
  `Severity:` line. Its id stays the same, so whatever names it still does.

## Step 3 — Draft and show it

For a new bug, take its id:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry
```

Show the entry exactly as it will be appended:

```
## [<id>] [bug] <title: what's broken, in a few words>

<What happens, and what should happen instead. How to see it.>

Severity: <one of severities>
Paths: <path>, <path>
Introduced by: <NNN-slug, only as confirmed>
```

For a retirement, the entry and its reason; for a retag, the heading and lines as they become.

## Step 4 — WAIT for explicit approval

Ask literally, with the entry's id and what happens to it:

> `Append this bug to work/inbox.md as <id> and commit it as "File <id>"? (yes / edit it / no)`

For a retirement: `Remove <id> from work/inbox.md as <reason> and commit it as "Retire <id>"?`;
for a retag: `Retag <id> as [<tag>] and commit it as "Update <id>"?`

**Write nothing until the human says yes.** Approval is for this entry only.

## Step 5 — Write and record it

**The register is the file `config`'s `work.register` names:** `work/inbox.md`, or
`work/ideas.md` in a repo `/sdlc:setup` hasn't moved over yet. Write entries there, never into a
second file beside it, which would hide every entry the first one holds.

`Edit` the register as approved: append a new entry after the last one, delete a retired one from
its heading to the line before the next `## `, or change a retagged one's heading and lines in
place. If it doesn't exist, `Write` it at that path first from `templates["inbox.md"]` in
`config`, as it is, then append. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py bug-commit --reason <id>=<reason>
```

`--reason` only for a retirement. The script commits the inbox alone, and refuses before writing
anything if anything else in the main checkout is uncommitted, or an entry is gone without a
reason: say what it printed and stop. It never pushes.

## Step 6 — Report and stop

Give the commit, the entry's id and severity, and the next action: `/sdlc:intent <id>` when the
human wants it fixed now, or nothing, and `/sdlc:status` puts it forward by severity.

## Out of scope

- Fixing the bug, or opening the change that does: that's `/sdlc:intent <id>`.
- Seeds and nits: retro and ship write those.
- Pushing. Only `/sdlc:publish` pushes.
