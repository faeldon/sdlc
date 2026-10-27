---
name: setup
description: Set a repo up for the sdlc plugin, or check that it still is, and after a plugin update refresh what the update changed under it — first asks whether it's a lightweight repo or a product, run by one person or a team, tracked on GitHub or locally, then gitignores the change worktrees, writes .sdlc/config.toml with the commands the repo's own task files suggest and the numbering the answers pick, scaffolds the process doc and the review passes from the plugin's defaults, generates an AGENTS.md (imported by a one-line CLAUDE.md) when the repo has neither, or proposes additions to the one there is, and allowlists the plugin's read-only commands; for a product it interviews for the product doc (users, outcomes, the evidence commands the retrospective reads), and for a team on GitHub it drafts the project doc (issue fields). Drafts everything, writes after one approval, and commits nothing. Use before a repo's first /sdlc:intent, when /sdlc:status says the repo isn't set up, after `claude plugin update`, with `product` or `project` to add that doc to a repo already set up, or with `reset` to put a doc or template override back to the plugin's default. Not for opening a change (/sdlc:intent), the repo's own drift scans (/sdlc:health), or taking the plugin back out (/sdlc:uninstall).
argument-hint: "[product | project — add that doc | reset <doc | template | all>]"
allowed-tools:
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

`readiness` lists each item with `ok`, `missing`, `warn` or `n/a`, the commands the repo's own task
files suggest (`candidates`), the permission rules it proposes, and the plugin's default docs to
draft from (`defaults`). `config` gives every path and setting as resolved now.

`drift` compares what setup copied with this plugin's defaults, block by block (each section, each
`- **lead**` bullet), against the record `.sdlc/setup.json` keeps of what setup last offered. It
sorts what it finds three ways, and Step 3 keeps them apart in that order:

- **`breaking`**: what the plugin would now misread: a config key a release retired, a template
  override in `.sdlc/templates/` that lacks a heading or key the script reads, a project or product
  doc it can't parse. Each comes with its `fix`.
- **`refresh`**: per host doc, the blocks the plugin changed that the host never touched
  (`added`, `refreshed`, `removed`), and `proposed`, the whole doc with them taken and every
  other block exactly as the host wrote it.
- **`report`**: what only a person can decide: a block both sides changed (`conflict`), a block
  that differs where there's no record to say who changed it (`differs`, `base: none`), a config
  key the plugin doesn't read (`unknown`) or one new since the record (`new`), a plugin template
  that changed under an override (`changed`). For the process and review docs, which hold only
  this repo's answers (`layout: answers`), only two: the plugin's guide changed since the record
  (`guide-changed`, a note to read, never a refresh), and a block whose heading the guide has
  nowhere (`unknown`), which no reader can place.

Blocks the host wrote (`own`), edited (`edited`) or took out (`host-removed`) are listed under
`docs` and never proposed back.

If every item is `ok` and `drift` has nothing in `breaking`, `refresh` or `report`, say so, list
anything still at its default that a repo usually sets, and stop. Nothing to write is a finished
setup. **Unless the argument is `product` or `project`**:
then that doc is the one item to draft, even though `readiness` reports it `ok` while it's off, and
Steps 1 to 6 run for it alone, without the profile round. A doc that already exists is never
rewritten: propose additions as a diff. **Or `reset`**, below.

**`reset <doc | template | all>`** puts the plugin's default back where the host changed it: a doc
by its `docs` key (`process`, `review`, `health`, `product`, `project`), a template override by its
file name (`intent.md`), or `all` of both. For a doc, the draft is its default again with every
`<` prompt filled the way a first setup fills it (Steps 1 to 3), and above it the blocks the reset
loses: each one `drift` lists as `own` or `edited`, shown as a diff, so nobody loses an edit
without seeing it. The process and review docs hold nothing but this repo's answers to the
plugin's guide, so `drift` lists none of their blocks: every block but the title and note is what
the reset loses, shown as the whole doc against the template. A repo set up before 1.5.0 holds a
whole copy of the guide there, which the skills read twice; its reset is how it gets back to
answers, carrying over only what it changed. For an override, there's nothing to draft: the reset deletes it and the
plugin's template is used again, so show the override against `templates[...]` in `config` and
what it loses. A reset is a write like any other, behind Step 4.

## Step 1 — Learn the repo

Read it the way `/init` does: the README, the task files `candidates` came from, the test layout,
the main entry points, and enough of the code to see its architecture. Read the existing
`CLAUDE.md` or `AGENTS.md` (`docs.policy`, and anything in `docs.context`) in full if there is
one. This is what
the drafts in Step 3 are made from; a draft written without it is a template with the blanks
guessed.

## Step 2 — Ask only about the gaps

**First, what kind of repo this is.** On a first setup (`readiness`'s `config` item is `missing`:
there is no `.sdlc/config.toml` yet), open with three questions in one round, each with a
proposed answer. A repo already set up skips them, even with other items `missing`. They decide which optional
docs Step 3 drafts and what goes in them. Nothing records them: no config key holds the answers,
so a later setup reads what was written, not what was said.

- **Kind:** *lightweight* (a throwaway, a spike, a personal tool) or a *product* (it has users
  who aren't the person running it). Propose it from Step 1's reading of the README and what the
  code serves.
- **Who runs it:** *one person* or a *team*. Propose a team only when Step 1 found a `CODEOWNERS`
  file (`Glob`) or a README that names maintainers; otherwise propose one person.
- **Where changes are tracked:** *GitHub* or *local*. Propose local for a lightweight repo. For a
  product, propose GitHub when `readiness`'s `archive` is `github` and its `gh auth` is `ok`;
  otherwise local.

Then one short round, only for what Step 1 couldn't settle:

- **The gate** (`commands.check`): which candidate it is, or the command if none fits. It's the
  gate `/sdlc:ship` runs on this diff, pass or fail: fast, offline, no side effects.
- **A slower check** (`commands.build` and `commands.build_when`): a slower gate, run when a
  changed path matches: anything needing real services or data, and the paths that should trigger
  it. None is a fine answer.
- **Scans** (`commands.scan`): what looks for drift across the whole repo. `/sdlc:health`
  runs it, and it produces findings rather than a pass or fail. A repo task named `doctor` or
  `health` is usually this, not the plugin's own `readiness`. And **worktree setup**
  (`commands.worktree_setup`): what a fresh worktree lacks that the repo's tools need. None is fine
  for either.
- **The invariants**: what a design here must never break. These go in the policy doc
  (`docs.policy`: `CLAUDE.md`, or `AGENTS.md` when that's the repo's only one), which ship's
  contract pass reads.
- **Numbering and archive** (`archive.target`): from where changes are tracked, which also
  decides where their numbers come from. GitHub sets `target = "github"`: each change is numbered
  by its issue. Local sets `target = "none"`, the default written out so the choice reads in
  the file: the counter numbers changes, nothing is mirrored and close files no issue. When the person picks GitHub and `readiness`'s `gh auth` isn't `ok`,
  still set github, and say that `/sdlc:intent` refuses until `gh auth login` has run. Never leave
  it local in its place: a repo that later moves to GitHub would hand out a number twice.
- **The base branch** (`git.base`), only when `config` gives it as null (`git.base_source` is
  `unset`: no `main`, and `origin/HEAD` names no local branch): which branch every change starts
  from and lands on. Every change refuses to start until it is set.
- **Evidence** (`retro.evidence`), only when a product doc is being drafted: commands that print
  what users did with the product, as counts and summaries, for the retrospective's product pass.
  Ask; never guess them from task files. None is a fine answer, and the pass then has only the
  history.

Propose an answer for each from what Step 1 found; the human corrects rather than composes.

## Step 3 — Draft everything

Each item `readiness` reported as `missing` or `warn` gets a draft. Show new files in full and every
edit to an existing file as a diff. A doc drafted from a default keeps the `>` note under its
title: it says what the plugin reads from the doc, which whoever edits it later needs.

- **`.gitignore`**: a `.claude/worktrees/` line, where each change's worktree lives. Never `.sdlc/work/`:
  a change's artifacts are committed with it, and `readiness` reports an ignored `.sdlc/work/`.
- **`.sdlc/config.toml`**: only the keys that differ from their defaults, each with a comment
  saying why. Include `[archive] target`, either way. Include `[git] base` when the base branch
  isn't `main`: the branch Step 2 was given, or the one `config` detected (`git.base_source` is
  `detected` and `git.base` isn't `main`), so a later change to `origin/HEAD` never moves it. A
  repo on `main` gets no `[git]` section.
- **The process doc** (`docs.process`, `.sdlc/SDLC.md` by default): start from `defaults.process`,
  this repo's answers to the plugin's guide (`docs.process.guide`), which the skills read with it.
  Fill in every line that starts with `<`. Those are where this repo differs: the failure it most
  needs to stop, its always-Tier-2 carve-outs, its gate and slower check, how a commit reaches its
  users. A prompt whose answer is the guide's is deleted, its heading kept. Copy a block of the
  guide in only to change it here. A `<` line left in is a blank the human has to fill.
- **The review passes** (`docs.review`, `.sdlc/REVIEW.md`): start from `defaults.review`, this
  repo's additions to the plugin's review guide (`docs.review.guide`), and list the ways this
  repo's code actually fails, found in Step 1: what its tests guard against, what its history
  fixes. Don't invent failure classes the code gives no sign of.
- **The health doc** (`docs.health`, `.sdlc/HEALTH.md`), when `readiness` reports it
  `missing`, which it does only once there is a scan. Start from `defaults.health`, and fill its
  table from what Step 1 found the scan checks (its task file, its script) and what the human says
  it reports: each finding, what it means here, and the response tier it usually gets. Fill its
  blind spots from what the scan needs to reach. Setup never runs the scan, and a finding nobody
  can explain yet is left out, not guessed.
- **The project doc** (`docs.project`, `.sdlc/PROJECT.md`), for a team tracked on GitHub, or
  with the `project` argument; `readiness` reports it `ok` and off while absent. One person needs
  none (each change's issue is assigned to whoever opens it), and a local repo has no issue for
  its fields to go on: say so in Step 6 rather than drafting it. When it's drafted, start from
  `defaults.project` with `assignees: tracker` uncommented in its frontmatter, and ask whether
  each change's issue also takes a milestone (`milestone: tracker`) or a project; uncomment those
  named, with the lookup each one uses. Fill in each field's section from the answers: who is
  assigned (whoever opens a change, an owner per area), and what decides the milestone. Delete
  the section of a field left off, so no `<` prompt is left behind.
- **The product doc** (`docs.product`, `.sdlc/PRODUCT.md`), for a product, or with the `product`
  argument; `readiness` reports it `ok` and off while absent. A lightweight repo gets none. Start
  from `defaults.product`, and interview for it the way `/sdlc:intent` does for an intent, asking
  only what Step 1 left open, with its reading of the README as the proposals:
  - **Users:** who reaches for this, and what they're trying to get done.
  - **Problem:** what's hard for them without it, in their terms rather than the code's.
  - **Outcomes:** two or three, `- O1.` on, each with a short `name` in bold
    (`- O1. **Unaided setup.** …`), two or three words a person remembers, and `Measured by:`
    with the signal that says so. Every skill shows the name beside the id, as
    `O1 (Unaided setup)`, so propose one with each outcome.
    Push back once on an outcome that is a feature in disguise ("add an export" is a feature;
    "users get their data out without asking for help" is an outcome), then take their answer.
  - **Bets:** no question of their own. Draft one or two from what the outcomes assume, for the
    human to correct.

  Say that from then on every open change needs a `serves:` line, and add the `retro.evidence`
  commands to `.sdlc/config.toml`.
- **Lightweight**: no product or project doc. Everything else above and below is drafted as it
  would be for a product, and every gate stays.
- **`AGENTS.md` and `CLAUDE.md`**: when the repo has neither, write the guide as `AGENTS.md`, which
  other coding agents read too, by `/init`'s rules: the commands to build, lint and test,
  including one test alone; the architecture that takes several files to see; nothing generic,
  and no file listing. Add an **Invariants** section with Step 2's answers. Then a `CLAUDE.md`
  holding only `@AGENTS.md`, so every Claude Code version loads it, and `docs.policy = "AGENTS.md"`
  in `.sdlc/config.toml`, since that `CLAUDE.md` holds no invariants. When the repo has either
  file, never rewrite it and never add the other: propose the Invariants section, or other
  additions, to that one as a diff. If the human would rather keep invariants out of it, set
  `docs.policy` to a separate file instead.
- **`.claude/settings.json`**: the rules `readiness` lists under `permissions.missing`, merged into
  `permissions.allow`, keeping everything already there. They cover only the script's read-only
  subcommands; everything that writes keeps asking. Say that the file is shared: it is committed
  and applies to everyone who works in the repo.
- **Issue forms**, only when `archive.target` is `github`: each of `readiness`'s `issue_forms`
  not yet `present`, copied from its `from` file to its path under `.github/ISSUE_TEMPLATE/`, with
  the bug form's `<severities>` line replaced by one `- <word>` option per word of the process
  doc's severities, most severe first. They give a person filing an issue the fields
  `/sdlc:triage` reads into an entry. One already `present` is the repo's: never redraft it. Once
  written, both are the repo's too: no later setup proposes changes to them, and
  `/sdlc:uninstall` leaves them.
- **What the plugin update changed** (`drift`), on a repo already set up. Show `breaking` first,
  each with what it breaks and its `fix`: a retired key is edited to the key that replaced it, an
  override lacking a heading or key gets it back (or a `reset`). Then each `refresh` doc as one
  diff from the host's text to its `proposed`, naming each block taken and whether the plugin
  `added`, `refreshed` or `removed` it. Then `report`, with no edit drafted: for a `conflict`,
  both texts side by side, for the human to merge by hand or leave; for `differs`, that there is
  no record of who changed the block, so it's theirs to judge; for `new` keys, the default and
  where `docs/REFERENCE.md` says what it does. A `report` item the human asks to take becomes a
  draft like any other, and goes back through Step 4.

## Step 4 — WAIT for explicit approval

Ask literally, listing every path:

> `Write these files and edits: <paths>? (yes / change one / leave one out)`

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
left out, and how changes are numbered and archived. Then report each item and what became of
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
