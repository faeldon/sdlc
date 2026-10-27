# Process

> The sdlc plugin's own answers to the process guide, which the skills read with this file
> (`docs.process.guide` in `sdlc.py config`). Each block here, a heading or a `- **lead**`
> bullet, stands in for the guide's block of the same heading path, or lead, when it holds text of
> its own, and is read after its parent's block there when the guide has none like it. A heading
> with nothing under it only places what follows. Copy any block of the guide here to change it
> for this repo; delete a prompt to keep what the guide says.

## The point of the process

### The failure it stops

**A change to the plugin that breaks the pipeline in a host repo it has never seen.**

Half of this plugin is prose a model follows, and a skill that reads well can still run a command
no `allowed-tools` rule covers, skip its WAIT, or lean on something only this repo has. The other
half writes into other people's repos: it numbers their changes, commits their folders and removes
them once landed, so a one-line slip renumbers or loses someone's work. Everything below exists to
put a checkable claim between a change and the people who rely on it.

## Tiers: the overhead control

### Always Tier 2, whatever the size of the diff

- **Anything that changes what `sdlc.py` reads or writes in a host repo**: a config key, the
  intent frontmatter, the `.sdlc/work/` layout, how numbers are allocated, how a change is archived or
  its folder removed. One line here can hand out a number twice or remove a folder that never
  reached `main`, in a repo the tests have never seen.
- **A skill's WAIT step or `allowed-tools`.** Either one changes what runs without asking, which
  is the plugin's main promise to a host.

## Where a change is worked: one worktree per change

### What a worktree needs

A fresh worktree needs nothing: `uv run` builds its own `.venv` the first time the gate runs.
The session itself runs the *installed* plugin, not the worktree's copy, so to try an edited skill
start a second session with `claude --plugin-dir .claude/worktrees/NNN-slug`.

## Running the stages

### Stage 1 — Plan → `/sdlc:intent`

#### Push-backs at Stage 1

**Is this mechanism or one host's policy?** The plugin knows nothing about what a host builds. A
change that only makes sense for one repo belongs in that repo's `.sdlc/config.toml`, templates or
docs, not here; if it needs a new key to get there, the key is the change.

### Stage 4 — Test

#### The gate and the slower check

Here the gate is `./check.sh`: ruff, the formatter check, pytest, and `claude plugin validate
--strict`. pytest includes `tests/test_adoption.py`, which runs a change from `new` to `close` in a
bare scratch repo through `uv run --script`, and `tests/test_archive.py`, which drives GitHub
through a fake `gh`, so it stays offline. There is no slower check: nothing here needs a real
service.

### Stage 5 — Ship → `/sdlc:ship`

#### The path to users

A shipped commit reaches users in a release: `/sdlc:release` bumps the version and tags it,
`/sdlc:publish` pushes `main` and the tag to `faeldon/sdlc`, then `claude plugin
marketplace update sdlc` and `claude plugin update sdlc@sdlc` on their side. Their
install is a cached copy pinned to that version, so a push without a bump changes nothing for them. A clone registered as a marketplace from its own path is
read in place instead, so for its owner a change is live in the next session as soon as
`/sdlc:close` fast-forwards `main`. `claude plugin list` shows `Read from:` when that holds, and
without it the owner is running a cached copy too. Ship stops before the push.

### Stage 6 — Maintain → `/sdlc:health`

#### What the scans watch

No scans are configured yet (`commands.scan` is unset), so `/sdlc:health` runs only
`sdlc.py check`. The gate already pins the skills' shape and the vocabulary; a scan earns its place
when it finds something a test can't, such as a skill whose prose drifted from the script's flags.
