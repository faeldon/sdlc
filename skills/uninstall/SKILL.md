---
name: uninstall
description: Take the sdlc plugin's setup back out of a repo — lists everything /sdlc:setup wrote (the committed files in .sdlc/, the plugin's allow rules in .claude/settings.json, the .claude/worktrees/ line in .gitignore when setup recorded adding it) and the lines in AGENTS.md or CLAUDE.md that name the plugin, then removes setup's files after one approval and commits nothing. Refuses while any change is open, standing in a worktree, or shipped and not closed, and while anything it would remove has uncommitted edits, so everything it removes is in history. Use when a repo stops using the plugin. Not for resetting one doc or template to the plugin's default (that's /sdlc:setup reset), not for dropping one change (/sdlc:drop), and never for touching work/, the tracker's issues, tags or history.
allowed-tools:
  - Read
  - 'Bash(cd *)'
  - 'Bash(git rev-parse *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py uninstall *)'
disable-model-invocation: true
---

# Uninstall — take setup back out of a repo

Setup writes into a repo in several places, and removing them by memory leaves rules in the
shared settings, a `.sdlc/` nobody reads, or worse, removes them while a change is still open in
a worktree and its number still claimed. This skill removes only what setup wrote, and only once
nothing is live, so the repo's history keeps every file it removes.

**What stays**: `work/` (the repo's record of its changes, and `work/inbox.md`), `AGENTS.md` and
`CLAUDE.md` (other agents read them; the lines naming the plugin are listed for the human to
edit), the issue forms in `.github/ISSUE_TEMPLATE/` (people file with them), the tracker's
issues and their labels, every tag, and every `Close` and `Drop` commit. A later setup counts
on from that history, so no number is handed out twice.

## Step 0 — The plan (mechanical, no confirmation needed)

```bash
cd "$(git rev-parse --show-toplevel)" && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py uninstall --check
```

`config` names `archive.target`: where the repo's issues are, which are left as they are.
`uninstall --check` prints the plan as JSON and exits 1 when it refuses:

- **`refused`**: each reason it won't run yet. An open change is shipped and closed, or dropped;
  a change shipped but not closed is closed; a stale worktree is the human's to remove; an
  uncommitted edit under `.sdlc/`, in `.claude/settings.json` or in `.gitignore` is committed or
  discarded first. With any refusal, show them all, say what clears each, and stop: there is
  nothing to approve yet.
- **`remove`**: the files under `.sdlc/` that git holds. A file there that git doesn't hold (an
  ignored local file) is in `left`, with why.
- **`edit`**: the plugin's rules to come out of `.claude/settings.json`, every other key and rule
  kept, and the `.claude/worktrees/` line in `.gitignore` when the record says setup added it.
- **`left`**: what stays, and why.
- **`mentions`**: each line in the policy doc (`docs.policy`) or a context doc (`docs.context`)
  that names `/sdlc:`, `.sdlc/` or `work/`, by path and line number.

## Step 1 — Show it

List every path in `remove`, every edit in `edit` with the rules or line it takes out, then
`left` and `mentions`. Say that `.claude/settings.json` is shared: the rules go for everyone who
works in the repo. For each mention, say what it does now that the plugin is gone, so the human
can edit it after: an `@`-import or a line telling an agent to run a skill is the one that
misleads.

## Step 2 — WAIT for explicit approval

Ask literally, listing every path:

> `Remove these files and edits: <paths>? (yes / no)`

**Remove nothing until the human says yes.** Approval is for this list only: run `--check` again
first if anything in the repo changed since Step 0.

## Step 3 — Remove

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py uninstall
```

It checks the refusals again and does nothing if one now holds. It commits nothing.

## Step 4 — Report and stop

Say what was removed and what was left, and the mentions still to edit. End with the commit for
the human to run, naming exactly the paths it touched, and then how to remove the plugin itself:

```
git add -A <the paths> && git commit -m "Remove the sdlc plugin's setup"
claude plugin uninstall sdlc@sdlc
```

## Out of scope

- Committing, pushing, or touching the tracker. The human commits; issues stay as they are.
- `work/`, `AGENTS.md`, `CLAUDE.md`, tags and history. Mentions are listed, never edited.
- Closing or dropping open changes. Those are `/sdlc:close` and `/sdlc:drop`, run first.
- Uninstalling the plugin from Claude Code. The human runs `claude plugin uninstall`.
