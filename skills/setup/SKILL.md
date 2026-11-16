---
name: setup
description: Set a repo up for the sdlc plugin, or check that it still is, and after a plugin update refresh what the update changed under it — first asks whether it's a lightweight repo or a product, run by one person or a team, tracked on GitHub or locally, then gitignores the change worktrees, writes .sdlc/config.toml with the commands the repo's own task files suggest and the numbering the answers pick, scaffolds the process doc and the review passes from the plugin's defaults, generates an AGENTS.md (imported by a one-line CLAUDE.md) when the repo has neither, or proposes additions to the one there is, and allowlists the plugin's read-only commands; for a product it interviews for the product doc (users, outcomes, the evidence commands the retrospective reads), and for a team on GitHub it drafts the project doc (issue fields). Drafts everything, writes after one approval, and commits nothing. Use before a repo's first /sdlc:intent, when /sdlc:status says the repo isn't set up, after `claude plugin update`, with `product` or `project` to add that doc to a repo already set up, or with `reset` to put a doc or template override back to the plugin's default. Not for opening a change (/sdlc:intent), the repo's own drift scans (/sdlc:health), or taking the plugin back out (/sdlc:uninstall).
argument-hint: "[product | project — add that doc | reset <doc | template | all>]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - 'Bash(cd *)'
  - 'Bash(git rev-parse *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py readiness *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py drift *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py record *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py reset *)'
disable-model-invocation: true
---

# Setup — make a repo ready for the change pipeline

Runs once per repo, and again whenever someone wants to know whether it is still set up, which is
always worth doing after the plugin updates. On a repo that already is, it reports that and offers
only what's missing, and what the update changed under the docs it copied. **It writes nothing until the
human has seen every file and every edit and said yes**, and it never commits: the pipeline can't
ship its own setup, because it needs the setup first.

## Step 0 — See what's there (mechanical, no confirmation needed)

```bash
cd "$(git rev-parse --show-toplevel)" && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py readiness && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py drift
```

`readiness` lists each item with `ok`, `missing`, `warn` or `n/a`, and says `complete` when
there is nothing to draft: every item answered and nothing in `drift`'s `breaking`, `refresh`
or `report`. `commands.build` and `commands.scan` left unset, listed in `unset`, and a repo
tracked locally (`archive.target` `none`) are answers, not gaps. It also gives the commands the
repo's own task files suggest (`candidates`), the permission rules it proposes, and the
plugin's default docs to draft from (`defaults`). `config` gives every path and setting as
resolved now; `drift` what the plugin changed under the docs setup copied.

**With `complete` true and no argument, say the repo is set up, list `unset` as the commands a
repo usually sets, and stop.** Nothing to write is a finished setup, and nothing below
applies.

**Otherwise** (not `complete`, or the argument `product`, `project` or `reset`), `Read`
`${CLAUDE_PLUGIN_ROOT}/skills/setup/drafts.md` now. `drafts.md` holds what `drift`'s lists mean,
what each argument drafts, and Steps 1 to 3, which learn the repo, ask about the gaps and draft
every file. Work through them, then come back for Step 4.

## Step 4 — WAIT for explicit approval

Ask literally, listing every path:

> `Write these files and edits: <paths>? (yes / change one / leave one out)`

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, and stop.

**Write nothing until the human says yes.** "Change one" means redraft that one and ask again;
"leave one out" means drop it from the list and ask again. Approval is for this list only.

## Step 5 — Write and prove it

Write each file, `Edit` each existing one exactly as approved: a `refresh` doc is written as its
approved `proposed` text. A template override being reset is deleted by the script, which takes
only a file name in `.sdlc/templates/` and refuses one with uncommitted edits:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py reset <name>
```

Then record what setup offered, so the next `drift` compares against it. `--created` names each
file this run created (none on a refresh), and `--gitignore-line` is given when this run added the
`.claude/worktrees/` line to `.gitignore`: `/sdlc:uninstall` removes only what the record says
setup wrote. Then prove it:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py record --created <paths created> && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py readiness && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check
```

Every item written should now be `ok`, `drift` included unless the human left a `refresh` out. One that isn't is a draft that didn't do what it said: say
which, rather than reporting success. If a gate command was set, run it once and say whether it
passed; a gate that fails on a clean tree isn't one yet.

## Step 6 — Report and stop

Start with the three profile answers and what each decided: which optional docs were drafted or
left out, and how changes are numbered and archived. Then the attribution answer, when Step 2
asked it, and what it wrote. Then report each item and what became of
it, what was left at its default and why, and anything the
human still has to do (a `<` line left in a doc, `gh auth login`). After a product doc, name
each open change `check` reported for a missing `serves:` line: its intent is in its own worktree,
so the human adds the line there (an outcome, or `none`). End with the commit, for the human to
run, naming exactly the paths written, `.sdlc/setup.json` among them:

```
git add <the paths> && git commit -m "Set the repo up for the sdlc plugin"
```

After a refresh or a reset, report what was taken, what was left in `report` and why, and the same
commit with `-m "Refresh the sdlc setup for <plugin version>"`.

Then the next step: `/sdlc:intent` for the first change.

## Out of scope

- Committing, pushing, or opening an issue. The human commits; `/sdlc:intent` opens the first issue.
- Rewriting an existing `CLAUDE.md`, `AGENTS.md`, review or process doc. Additions are proposed as diffs.
- Writing templates in `.sdlc/templates/`. The plugin's are generic and work; a repo adds its own
  later, and `reset` only removes one.
- Removing the setup. That's `/sdlc:uninstall`.
- Allowing anything that writes. `new`, `ship`, `close` and `archive` keep asking.
- Recording the profile. The answers steer the drafts; no config key keeps them.
