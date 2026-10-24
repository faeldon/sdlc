# Ideas

Seeds, not a backlog. `/sdlc:intent` promotes one into a change.

## [2026-10-24] [seed] UX and UI reviewers for the factory, and how a repo declares a front end

The factory ships code, security and test reviewers. The factory it learned from also
runs UX and UI reviewers against a running app. agent-skills has no such agent, only its
`frontend-ui-engineering` skill to write them from, and the plugin can't know a repo has a UI: it
needs a declaration (a `factory.toml` key, or `commands.preview` for a dev server) before a UI
reviewer can run. Raised 2026-10-24.

## [2026-10-24] [seed] A factory queue, and parallel runs across worktrees

The factory runs one change per session. A queue (`/sdlc-factory:next` over seeds or
open intents) and several runs at once, one per worktree, would let ideas move while nobody
watches. GitHub issues and `work/ideas.md` are already the queue; this is the runner. Raised
2026-10-24.

## [2026-10-24] [seed] A factory status board

A page that shows each running change's stage, round and verdicts as they land, from the change
folders' files, the way the factory it learned from shows a dashboard. Read-only. Raised
2026-10-24.

## [2026-10-24] [seed] A retro report and process views from each change's numbers

Close records each change's numbers; render them: a templated report the
script fills with no model tokens, committed with each retrospective. Then add the process views
it makes possible: capacity (how many changes one person runs at once before cycle time rises
and throughput doesn't), changes open at once, the human's wait time against agent time, and
throughput by tier per week alongside cycle time and rework, roughly DORA's set. Avoid a single
velocity figure, which invites optimising the number. A dashboard is optional and comes after the
report: the process doc keeps "no dashboard" for the signals. Raised 2026-10-24.

## [2026-10-24] [seed] Architecture indicators for the retro loop

A standard set the plugin can compute from git for any repo, for the retrospective's
architecture pass:
- how much code each change generated, by tier and per closed change (lines and files added,
  changed and deleted, and code against tests against docs);
- churn hotspots (the files most changes touch, weighted by size; today `scripts/sdlc.py`,
  touched by nearly every change);
- files that change together;
- the largest files and how they grow.

Language-specific measures (complexity, dependency cycles) come from the host through a configured
command, the way `commands.scan` works, since the plugin knows nothing about what a host builds.
Raised 2026-10-24.

## [2026-10-24] [seed] Landing changes through pull requests, for teams

Close lands a change by fast-forwarding `main` locally, and only publish pushes. A team that
reviews through pull requests would want ship to push the branch and open a PR (its body carrying
`Closes #N`), close to wait for the merge on GitHub and then fast-forward from the remote, and the
PR's review to stand alongside ship's. An opt-in way of landing, not a default, and an exception
to "only publish pushes" made on purpose. It builds on the issue closing when its `Close` commit
reaches the remote. Raised 2026-10-24.

## [2026-10-24] [seed] Triage tests by how long they should live

Tests pile up that only mattered while a change was being built, and shims kept "for one release"
outlive it because nothing enforces the deadline. Ask of each test how it could ever fail:
- **Regression**: a later change breaks it by accident. Kept in `tests/` for good.
- **Compatibility**: a shim stops working. Lives exactly as long as the shim, which names the
  version it's removed in.
- **Acceptance**: only a deliberate revert breaks it (a file moved, a key renamed). Proves the
  change once and stays out of `tests/`.

In three steps:
1. Write the rule into Stage 4 — Test, and two findings into review Pass 1 and Pass 3 (a test in
   `tests/` only a revert can fail; a shim with no removal version). Each edit goes in both
   `defaults/` and this repo's `.sdlc/`, and `AGENTS.md` gains the rule that a change editing a
   default edits this repo's copy too, and the other way round.
2. A `DEPRECATIONS` registry in `sdlc.py`, a `compat` pytest marker per shim, and one test that
   fails once a shim's `remove_in` is at or below the version in `plugin.json`, so a release
   can't carry an overdue shim; `release` and `status` list what's due.
3. Acceptance checks live in `work/NNN-slug/`, run by ship and archived by close with the folder.

Raised 2026-10-24.
