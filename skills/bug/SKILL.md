---
name: bug
description: File a bug in .sdlc/work/inbox.md, or retire or retag one — interviews for what broke and how to reproduce it, takes an id and a severity from the process doc's words, offers the change that last touched the code as its `Introduced by:`, and after one approval commits the inbox alone on the base branch as "File <id>", "Retire <id>" or "Update <id>". Use from any checkout, a change's worktree included, when something already shipped is broken, when a /sdlc-factory:review report proposes bugs to file (given its path), or a bug turns out to be a feature request or a duplicate; in a host, a bug in the plugin itself is filed instead as a public issue on the plugin's repo, after the same one approval. Not for something nobody has built yet (an idea, which /sdlc:idea files), not for fixing the bug (/sdlc:intent <id> opens the change that does), and never for editing code.
argument-hint: "[what broke, an entry's id to retire or retag, or a review report's path]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py bugs *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py inbox-commit *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py upstream *)'
disable-model-invocation: true
---

# Bug — file what's already broken

A bug is something that shipped and is broken, with a way to see it. It goes in `.sdlc/work/inbox.md`
beside the seeds, tagged `[bug]` and given a severity, so `/sdlc:status` puts it first and
`/sdlc:retro` can count it. This skill files one, retires one that turned out not to need a fix,
or retags an entry that was filed as the wrong kind. It never fixes anything: the fix is a change,
opened with `/sdlc:intent <id>`, which links it with `fixes:`.

**It writes one file, the inbox, and commits it alone.** Everything else is the script's. A bug
in the plugin, met in a host, is the one exception: it goes to the plugin's own repo as a public
issue, from an input file in the git common dir, and nothing in the host is committed.

## Step 0 — See what's there (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py bugs && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py upstream
```

Run it from any checkout: a bug turns up at any stage of a change. The commit in Step 5 always lands
on `git.base` from `config`, in the main checkout. When `config`'s `work.dir` is inside
`.claude/worktrees/`, the session is in a change's worktree: note it, since Step 5 then names the
entry it files. `bugs`
lists the open bugs and `severities`, the process doc's words for how bad one is (`docs.process`,
its section on bugs, else the plugin's guide, `docs.process.guide`), most severe first. If the bug is already listed, say which and stop: one bug,
one entry. `upstream` says whether a bug in the plugin can be filed on the plugin's repo from here:
`own_repo`, `available` and `why`, the `repo` (from the plugin's manifest, never typed), the `gh`
`login`, the `input` file, and `new_issue_url`.

## Step 1 — Ask what broke

**Whose bug it is.** When `upstream`'s `own_repo` is true, never ask: this is the plugin's own
repo, and every bug is filed here. In a host, ask first whether the bug is in the host's own work,
or in the plugin (an `/sdlc:` or `/sdlc-factory:` skill, `sdlc.py` or `factory.py`, the plugin's
docs). You may propose the plugin when the bug as told is a failing `sdlc.py` or `factory.py`
call, one of those skills, or the plugin's docs, but never decide alone: the person says which.
A bug in the host's own work goes on as below, unchanged.

**A bug in the plugin** is told in its own fields, and only these leave the host: a title; what
happens, and what should happen instead; how to see it; and, from the session, the failing
plugin command, its exit, and what it printed. Ask for the first three; take the last three from
the session as they were, and ask only when the session doesn't hold them. No severity, paths,
theme or `Introduced by:`: the plugin's repo triages it. Then go to Step 3.

Ask only about what the human hasn't said:

- **What happens**, and what should happen instead.
- **How to see it**: the command, the input, the steps. A bug nobody can reproduce yet is still
  filed, saying so.
- **Where**: the paths it lives in, as far as anyone knows.
- **How bad**: one of `severities`, with the process doc's meaning for each beside it. Never pick
  for the human.

Don't ask for these two; propose the first and take the second only when it's said:

- **Its theme**: a word the register's entries already use in their `Theme:` lines (`Read` the
  file `config`'s `work.register` names), the one closest to the bug, or a new one when none
  fits. Status groups entries by it. The person may change it or drop it. A bug filed without
  one may get it later from `/sdlc:idea --themes`, the one edit of a bug that isn't this skill's.
- **Its priority**, only when the person says it's more urgent than its severity
  (`Priority: high`) or can wait (`Priority: low`). Status puts high before everything else, low
  after it; with no line, a bug ranks by its severity.

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

**From a report.** When the argument is a path to a report `/sdlc-factory:review` wrote (under
`.sdlc/reports/`), `Read` it instead of interviewing: each `## [?] [bug] <title>` block is a
proposed bug, with what's wrong, a proposed `Severity:` and its `Paths:`. List them, and ask which
to file: the person picks, and may change a title, a severity or the text, and gives one to a
block that has no `Severity:` line, from `severities` like any bug's; one already listed by
`bugs` is a duplicate, said and left out. Then, for each picked bug, ask `bugs --introduced` about
its paths and offer its `Introduced by:` as above. Everything from here on covers all of the
picked bugs at once: one draft, one WAIT, one commit.

## Step 2 — Retiring or retagging instead

When the argument is an entry's id, or the human wants one gone or moved:

- **Retire** a bug that needs no fix: the reason is one of `duplicate`, `not-a-bug`, `wontfix`
  or `cant-reproduce`, said with a line on why. A bug fixed by a change is never retired here:
  `/sdlc:ship` removes it with the fix. An entry with an `Issue:` line was filed from those
  issues, which stay open and labelled: say so in Step 6, and that each is closed by hand on the
  tracker, with the same reason.
- **Retag** an entry filed as the wrong kind: a `[bug]` that is really a request becomes a
  `[idea]`, and an `[idea]` (or an older `[seed]`) that describes something broken becomes a
  `[bug]` with its `Severity:` line. Its id stays the same, so whatever names it still does.

## Step 3 — Draft and show it

For a new bug in the host's own work (or any bug, in the plugin's own repo), take its id:

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
Theme: <theme, unless the person dropped it>
Priority: <high or low, only when the person said so>
Origin: <host, only when the person's account says it was found in another repo>
```

The `Origin: host` line says the bug was found using the plugin in another repo, never which
one; an intent fixing it proposes it as its `origin:`. A bug found here gets no line.

**A bug in the plugin.** `Write` the file `upstream`'s `input` names, these headings and nothing
else, each followed by its text as told:

```
## Title
## What happens
## What should happen
## How to see it
## Command
## Exit
## Output
```

Then render the issue from it:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py upstream --render
```

It prints `title`, `body`, `key`, `left_out` and `already`. The script, not you, decides what the
body holds: every path, name and value that would identify the host is cut, and a field that
still would is left out, saying so. Show the title and the body exactly as printed, in the message
and in the dialog's `preview`, and say what `left_out` names. When `already` names an issue, it was
filed before: give its URL and stop. When `upstream`'s `available` is false, say its `why`, show
the body and `new_issue_url` to paste it there by hand, and stop: nothing is filed, and the bug is
done.

For a retirement, the entry and its reason; for a retag, the heading and lines as they become.
From a report, take every id in one call, `next-entry --count <n>` with `<n>` the bugs picked, and
show each entry as above with its own id, `[?]` replaced.

## Step 4 — WAIT for explicit approval

Ask literally, with the entry's id and what happens to it:

> `Append this bug to .sdlc/work/inbox.md as <id> and commit it as "File <id>"? (yes / edit it / no)`

For a retirement: `Remove <id> from .sdlc/work/inbox.md as <reason> and commit it as "Retire <id>"? (yes / no)`;
for a retag: `Retag <id> as [<tag>] and commit it as "Update <id>"? (yes / no)`; from a report:
`Append these <n> bugs to .sdlc/work/inbox.md as <ids> and commit them as "File <ids>"? (yes / edit them / no)`;
for a bug in the plugin, with `upstream`'s `repo` and `login`:
`File this bug publicly on <owner/name> as <login>? Anyone can read it. (yes / edit it / no)`,
its dialog's `preview` the body as rendered. On `edit it`, rewrite the input file, render it again,
show it, and ask again.

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in them
an option in that order, labelled as written, `header` the skill's name, and the entry exactly as it
will be appended (for a retirement, the entry and its reason; for a retag, the heading and lines as
they become; from a report, every entry; for a bug in the plugin, the body as rendered) as the
`preview` of each yes option. A preview past 40 lines keeps its approving part and ends "… <k> more
lines in <path>", or "… <k> more lines, shown above" when no file holds them yet. Only a chosen
`yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or refused is a
no. If the tool is unavailable or refused, ask the same text, answers in parentheses, right after
what the preview holds, and stop.

**Write nothing until the human says yes.** Approval is for this entry only.

## Step 5 — Write and record it

**A bug in the plugin** is filed, only after a chosen yes, under the key the body was shown with:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py upstream --send --key <key>
```

It files under the person's own `gh` login, and records the key before and after, so a rerun never
files twice. It refuses a key the input no longer renders to: render it again, show it, and ask
again. With `filed` null, it filed nothing: say its `why`, and show the body and `new_issue_url` to
paste it there by hand. Nothing in the host is written or committed; skip to Step 6.

**The register is the file `config`'s `work.register` names:** `.sdlc/work/inbox.md`. Write
entries there, never into a second file beside it, which would hide every entry the first one
holds.

`Edit` the register as approved: append a new entry after the last one, delete a retired one from
its heading to the line before the next `## `, or change a retagged one's heading and lines in
place. If it doesn't exist, `Write` it at that path first from `templates["inbox.md"]` in
`config`, as it is, then append. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py inbox-commit <id> --reason <id>=<reason>
```

The `<id>` only from a change's worktree (every id, from a report), and `--reason` only for a
retirement. The report stays where it was: it is ignored, and the person may delete it. From the main
checkout the script commits the inbox alone, and refuses before writing anything if anything else
there is uncommitted, or an entry is gone without a reason. From a worktree it files the entry it
names into the main checkout's register and commits it there, refusing if the main checkout has
anything uncommitted or isn't on `git.base`, then puts the entry back as it was in the worktree,
which gets it from `git.base` when it next comes up to date. On a refusal, say what it printed and
stop. It never pushes.

## Step 6 — Report and stop

For a bug in the plugin: the issue's URL, and that it is followed there; nothing is filed in the
register.

Give the commit, the entry's id and severity, and the next action: `/sdlc:intent <id>` when the
human wants it fixed now, or nothing, and `/sdlc:status` puts it forward by severity.

## Out of scope

- Fixing the bug, or opening the change that does: that's `/sdlc:intent <id>`.
- Ideas: `/sdlc:idea` files them. Nits: ship writes those.
- Pushing. Only `/sdlc:publish`, and close and release when `git.push` names them, push.
