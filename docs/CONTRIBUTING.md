# Contributing to sdlc

How to work on the plugin itself: run it from a clone, keep the gate green, and make a change the
way this repo makes every change, through its own pipeline. [`AGENTS.md`](../AGENTS.md) is the
same ground written for a coding agent, with the architecture function by function and every
invariant the tests enforce; read it before changing `scripts/sdlc.py` or a skill.

## Working from a clone

Register the clone as the marketplace, from its path, and the plugin is read in place: an edit
takes effect in the next session, with no reinstall and no version bump.

```bash
claude plugin marketplace add <path-to-clone>/   # the trailing slash matters
claude plugin install sdlc@sdlc
claude plugin list                               # "Read from: <path-to-clone>"
```

The `Read from:` line is the check. Without it, sessions run a cached copy in
`~/.claude/plugins/cache/sdlc/sdlc/<version>/`, which changes only when a release bumps
the version. A session started before the switch keeps its old path, so `/sdlc:close` in the
plugin's own repo hands itself to the clone's `scripts/sdlc.py`, and after its merge to the merged
one; its report says which (`ran`). Both registrations are named
`sdlc`, so to switch from GitHub to a clone, `claude plugin marketplace remove sdlc`
first. That uninstalls the plugin at every scope, so reinstall it after the `add`, with
`--scope project` from each repo that had it installed there.

`--plugin-dir` loads the plugin from a path for one session, without the marketplace: a clone
(`claude --plugin-dir <path-to-clone>`), or a change's worktree, to try a skill as edited there
without touching your registration:

```bash
claude --plugin-dir .claude/worktrees/NNN-slug
```

## The gate

```bash
./check.sh                                    # ruff, the formatter check, pytest, claude plugin validate --strict
uv run --group dev pytest -q                  # tests only
uv run --group dev pytest tests/test_sdlc.py::test_name -q   # one test
uv run --group dev ruff format .              # fix formatting
```

It's offline: GitHub is driven through a fake `gh` on `PATH` (`tests/test_archive.py`), and
`tests/test_adoption.py` runs a change from `new` to `close` in a bare scratch repo through
`uv run --script`, which is the test that the plugin works in a repo that isn't the one it came
from. A run that collects no tests is a failure. `pyproject.toml` only gives the tests an
environment; the script declares its own dependencies inline, and the two lists are kept in step.

## How a change is made here

The plugin runs on its own repo. Open a change with `/sdlc:intent`, and it goes through the
stages like any host's: [`.sdlc/SDLC.md`](../.sdlc/SDLC.md) is this repo's process (tiers, what
is always Tier 2, the three loops) and [`.sdlc/REVIEW.md`](../.sdlc/REVIEW.md) the review passes
`/sdlc:ship` works through. Two things are always Tier 2 here, whatever the size of the diff:
anything that changes what `sdlc.py` reads or writes in a host repo, and a skill's WAIT step or
`allowed-tools`. A bug fix starts with a failing test.

The repo is numbered by GitHub issues, so an intent opens an issue on `faeldon/sdlc`.

## Design philosophy

**Mechanism vs. judgment.** `scripts/sdlc.py` does the mechanical half (numbering, worktrees,
scaffolding, auditing artifacts, landing and archiving) and never writes artifact prose. The
skills in `skills/*/SKILL.md` do the judgment and call the script. Logic a rule must be able to
cover goes in the script, not in a skill's bash.

**Mechanism vs. policy.** The plugin knows nothing about what a host builds. Everything
host-specific (commands, docs, templates) comes from the host's `.sdlc/config.toml`, read only by
`sdlc.py config`; skills ask `config` rather than guessing. A change that only makes sense for one
repo belongs in that repo's config or docs, and if it needs a new key to get there, the key is the
change.

**One approval per writing skill.** Every skill that writes drafts the exact content, shows it,
asks a literal yes/no question and waits: exactly one step headed WAIT, never zero (approval is
never standing) and never two (the second gets skipped).

**The gate is offline and deterministic.** A gate that needs the network gets skipped, and a
skipped gate still reports green from memory.

**Every near-miss becomes a test.** A rule that must always hold needs a test or a hook behind
it, not only a sentence in a skill. [`AGENTS.md`](../AGENTS.md), *Invariants the tests enforce*,
lists them: narrow `allowed-tools`, only publish pushes, nothing about a project or a workspace,
one shape for the shipped docs, and the rest.

**Nothing public names the agent.** No commit, pull request, issue or release note here says an
agent wrote it: no `Co-Authored-By` naming Claude, no session links (`AGENTS.md` has the rule).

## Layout

| Path | What |
|---|---|
| `skills/<name>/SKILL.md` | the `sdlc` skills; the directory name is the skill's name |
| `scripts/sdlc.py` | the mechanism, one file, argparse subcommands |
| `scripts/trackers/` | one module per tracker, loaded by path only when `archive.target` names it |
| `scripts/metrics.py` | what a change cost, measured at close |
| `templates/` | the shape of a file the plugin writes itself, each time it creates or rewrites one (the change artifacts, direction doc, issue, `ideas.md`, `notes.md`); a host overrides one in `.sdlc/templates/`; one shape, see `AGENTS.md` |
| `defaults/` | a doc `/sdlc:setup` copies into a host once, after which the host owns it: the plugin reads it, and a rerun of setup only proposes what a newer default changed (`drift`, against `.sdlc/setup.json`) (the process, review, project, product and health docs); one shape, see `AGENTS.md` |
| `plugins/factory/` | `sdlc-factory`, a second plugin with its own skills, agents and `factory.py`; its [README](../plugins/factory/README.md) describes it |
| `.claude-plugin/` | `plugin.json` and `marketplace.json`: this repo is its own marketplace |
| `.sdlc/` | this repo's own config and process docs |
| `tests/` | pytest; skills are tested as text, the script by loading it by path |

## Writing a tracker

A tracker is `scripts/trackers/<name>.py`; adding the file makes `archive.target = "<name>"`
valid. `sdlc.py` loads it by path and calls `make(home, cfg)`, which returns an object with:

- `numbers`: whether it numbers changes, from its own issues; when it doesn't, the counter does;
  `claim(slug, title, tier, used)`, `drop(url, why)`, `next_guess()`: only when it can;
- `unavailable()`: why it can't run here, or None, without touching the network;
- `readiness()`: `(name, status, detail)` items for `sdlc.py readiness`;
- `sync(change)`: mirror the change as it is now, returning `{"issue", "done", "skipped",
  "error"}` or `{"nothing": why}`. Never create anything;
- `archive(change)`: the final mirror at close, read back: `(where, None)` or `(None, why)`;
- `lookup(field)`: the values it has for `milestone`, `project` or `assignees`, as
  `(values, None)` or `(None, why)`. Read-only.

`change` is a dict: the change's record (`id`, `slug`, `name`, `title`, `tier`, `stage`, `impact`,
`depends_on`, `updated`), its `branch` and `sha`, the rendered `marker`, `body` and `comments`, an
`error` when it couldn't be rendered, `vocabulary` (every
tier, stage and impact) and `fields` (the project doc's fields that are on, with the intent's
values: mirror these exactly, and never touch one that isn't there). A tracker never imports
`sdlc.py` and never reads `work/` or `.sdlc/`; it has the standard library and the script's
PEP 723 dependencies, nothing more. Core never calls `gh`: every call lives in the tracker. Drive
it in the tests through a fake of its command-line tool on `PATH`, as `tests/test_archive.py` does
for `gh`.

## Releasing

Releases are made with the plugin's own release loop: `/sdlc:release` from the main checkout,
then `/sdlc:publish`. `sdlc` and `sdlc-factory` always release as one version, held in both
manifests and `pyproject.toml`.
