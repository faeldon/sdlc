---
name: update
description: Take a newer sdlc release in this repo — checks the latest release now, finds every sdlc and sdlc-factory install that applies here (user scope, and this repo's project and local scope), prints this host's exact steps (the marketplace update, one `claude plugin update` per stale install with its --scope, the restart, /sdlc:setup, the commit), and behind one approval runs the claude plugin commands from the main checkout. Use when the session start or /sdlc:status says a release is out, or to see whether one is. Not inside the plugin's own clone (read in place, never told to update), not to refresh a repo's docs after the restart (that's /sdlc:setup), and never to commit, push, or update another repo's install.
allowed-tools:
  - AskUserQuestion
  - 'Bash(cd *)'
  - 'Bash(claude plugin marketplace update sdlc)'
  - 'Bash(claude plugin update sdlc@sdlc --scope *)'
  - 'Bash(claude plugin update sdlc-factory@sdlc --scope *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py update *)'
disable-model-invocation: true
---

# Update — take a newer release, the same way in every host

Taking a release takes more than one command: the marketplace's copy first, then each install at
the scope it was made at, then a restart (the running session keeps the copy it started with),
then `/sdlc:setup` for what the release changed under the repo's docs, then a commit of what setup
wrote. This skill gets the list right for this host and runs the part Claude Code can run.

## Step 0 — The steps (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py update
```

`update` checks the latest release now (and caches the answer for the day's session-start line)
and prints JSON: `running` (this session's copy), `latest`, `in_place`, every install found in
`installs`, the ones in other repos in `elsewhere`, `restart_first`, `cwd` (the main checkout) and
`steps`, in the order they run. Whether an install applies here, which are stale and in what order
they update is the script's call: never add, drop or reorder a step.

- **`in_place` true:** the plugin is read from a clone, whose version is whatever its checkout
  holds. Say so and stop: `git pull` in the clone is the update.
- **`steps` empty:** say what `running` and `latest` are (and `reason`, when `latest` is null) and
  stop. When `restart_first` is true, an update already ran: restart Claude Code, then run
  `/sdlc:setup`.
- **`config`'s `factory.enabled` true with no `sdlc-factory` row in `installs`:** say the factory
  is enabled here but no install of it was found, so it gets no step. Never hide it.

## Step 1 — Show them

Print the steps, numbered, as the script gave them, each `claude plugin …` command with the folder
it runs from (`cwd`). Then list `elsewhere`, if any: those installs belong to other repos, and are
updated by running `/sdlc:update` there.

## Step 2 — WAIT for explicit approval

Ask literally, `<commands>` the `claude plugin …` steps joined with `; `:

> `Run these claude plugin commands: <commands>? (yes / no)`

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, and stop.

**Run nothing until the human says yes.** A no leaves them the printed steps to run themselves.
Approval is for these commands only.

## Step 3 — Run them

Run each `claude plugin …` step as its own Bash call, in order, from `cwd`, since `--scope project`
acts on the folder it runs in:

```bash
cd "<cwd>" && claude plugin marketplace update sdlc
cd "<cwd>" && claude plugin update sdlc@sdlc --scope <scope>
cd "<cwd>" && claude plugin update sdlc-factory@sdlc --scope <scope>
```

Each one the steps name, and only those. **Stop at the first that fails**: report its output, and
the steps not run.

## Step 4 — Report and stop

Report each command and what it printed. Then the steps left, which only the person can take:
`restart Claude Code` (this session still runs `running`), then `/sdlc:setup` in the new session,
then commit what setup names. Setup refuses to refresh until the restart. Nothing was committed or
pushed.

## Out of scope

- Committing, pushing, or editing any file. Setup drafts the refresh and names its commit.
- Another repo's project or local install: listed in `elsewhere`, updated from there.
- Restarting Claude Code, which only the person can do.
