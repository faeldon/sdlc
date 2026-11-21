---
id: 206
slug: update-skill
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T00:34Z
updated: 2026-11-21
shipped: 2026-11-21
idea:
depends_on:
serves: none
---

# 206 — A host learns of a new release and updates in one consistent run

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Whenever we release, a host needs more than `/sdlc:setup` to update. Updating one host repo
from 1.10.0 to 1.11.0 on 2026-11-20 took six steps, as its session transcripts and uncommitted
diffs show:

```
! claude plugin marketplace update sdlc
! claude plugin update sdlc@sdlc --scope user
! claude plugin update sdlc@sdlc --scope project
! claude plugin marketplace update sdlc                    # run again
! claude plugin update sdlc-factory@sdlc --scope project
  (restart Claude Code)
/sdlc:setup
```

Nothing tells a host any of that:

- README's *Updating* lists only `claude plugin marketplace update sdlc` and
  `claude plugin update sdlc@sdlc`. It leaves out `sdlc-factory@sdlc`, the `--scope` a project
  install needs, a second copy at another scope, and the restart.
- Every `claude plugin update` ends "Restart to apply changes": the running session keeps the old
  copy, so a setup run before the restart is the old version's setup.
- Setup's refresh is left uncommitted and nothing says to commit it: the host's
  `.claude/settings.json` (the allowlist rule renamed `check` → `vet`) and `.sdlc/setup.json`
  (1.5.0 → 1.11.0) sat modified afterwards.
- Nothing notices a newer release. `status` notices only `.sdlc/setup.json` older than the installed
  plugin, the state *after* an update; a host on 1.10.0 never hears 1.11.0 is out.
- That host built its own workaround: a SessionStart hook of its own, warning when an installed
  plugin is older than its marketplace folder. That detection belongs in the plugin, so every host gets it.

## Outcome

- A session in a host whose installed sdlc or sdlc-factory is older than the latest release says so
  once, in one line (`sdlc 1.11.0 is out (this session runs 1.10.0): /sdlc:update`), and `status`
  repeats it.
- `/sdlc:update` prints this host's exact steps (the marketplace update; one
  `claude plugin update <plugin>@sdlc --scope <scope>` per install it found; the restart;
  `/sdlc:setup`; the commit) and, behind one WAIT, runs the `claude plugin` commands.
- `/sdlc:setup` refuses to refresh while the running copy is older than the installed one ("restart
  first"), and its report names the commit to make.
- README *Updating* and REFERENCE.md describe the same sequence the command prints.
- A test runs the detection against a faked `claude plugin list` (two scopes, sdlc-factory, a
  local-path marketplace, no network) and checks the line it prints.

## Affected

- **Area:** plugin hooks, `scripts/sdlc.py`, skills, docs.
- **Files & components:** a new SessionStart hook in the plugin; a new read-only `sdlc.py update`
  (and a cached latest-release check); a new `skills/update/SKILL.md`; setup's Step 0 and report;
  `status`'s nudge; README *Updating*; REFERENCE.md *After an update*; `docs/FEATURES.md`; tests.
- **Downstream:** every host. The hook would run at the start of every session in every repo with
  the plugin enabled: hosts at project scope, user scope or both, with or without sdlc-factory, and
  this repo, whose marketplace is read from its clone and must never be told to update.
- **Contracts:** nothing runs unasked (the board's "no model starts a server unasked"); writes
  before a WAIT; narrow `allowed-tools` (a rule per `claude plugin …` command); only the named steps
  push; the scripts run on Windows; `claude plugin validate --strict`; mechanism in `sdlc.py`, not
  in a skill's bash.

## Constraints

- The hook only advises: it never updates, never blocks a session, and stays silent when it can't
  tell (offline, no `claude` on PATH, a local-path marketplace).
- Cheap at session start: at most one network check a day, cached.
- Nothing outside the repo is written without the WAIT's yes; the `claude plugin` commands change
  Claude Code's settings.
- Setup still commits nothing; it names the commit.

## Open questions

- ~~Where does "latest release" come from: the marketplace folder's `plugin.json`, a daily
  `git ls-remote --tags` on the marketplace's source, or the GitHub releases API? And what does a
  host without network or `gh` see?~~ Resolved: a daily `git ls-remote --tags --refs` on the
  running manifest's `repository`, cached in the git common dir; offline is cached as
  `latest: null` and shows nothing (spec R4)
- ~~Is a plugin-shipped SessionStart hook acceptable under "nothing runs unasked", or does detection
  live only in `status` and setup?~~ Resolved: yes, an advisory hook capped at one check a day and
  silent when unsure, approved with the spec (R1, R2)
- ~~Can a skill run `claude plugin update` reliably from inside a running session, or does
  `/sdlc:update` print the `!` commands for the person to run?~~ Resolved: the skill prints the
  steps, then runs them behind one WAIT, from the main checkout (spec R11)
- ~~How does setup tell the running copy is older than the installed one: `${CLAUDE_PLUGIN_ROOT}`'s
  version against `claude plugin list --json`?~~ Resolved: `sdlc.py update --installed` compares
  `plugin_version()` with the most specific install that applies here (spec R9, R12)
- ~~Does `/sdlc:update` cover every repo on the machine with the plugin installed, or only this
  one?~~ Resolved: only this repo and user scope; other repos' installs are listed as `elsewhere`
  (spec R8)
