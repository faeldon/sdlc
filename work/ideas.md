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

## [2026-10-24] [seed] Rework ignores shared docs and the setup record

The first retrospective's rework list held 12 pairs, all same-day, all from `defaults/SDLC.md` or
`.sdlc/setup.json`: files nearly every change edits. None was a follow-up fix, so the signal the
process doc watches says nothing. Count rework on code and tests, or leave out the files most
changes touch. Raised by the retrospective of 2026-10-24.

## [2026-10-24] [seed] A change's size counts every commit on its branch

`retro` reads a change's files and lines from the one commit before its `Close`, so 002, two
commits and about 1,700 lines on its branch, reads as 1 file and 9 lines. Count the branch's whole
diff against the base it was shipped on. Raised by the retrospective of 2026-10-24.

## [2026-10-25] [seed] A process map of the three loops, kept true by the gate

A map of the change loop (intent → spec → plan → build → ship → close), the release loop (release
→ publish) and the retro loop: each stage's gates, the `sdlc.py` calls, the checks (gate,
acceptance checks, review passes) and what it writes. Mermaid in the repo (`docs/PROCESS.md`,
rendered by GitHub), with a test that fails when a stage, skill or WAIT is missing from it; HTML
or a diagramming tool can be generated from it later. Decide whether hosts get a copy from setup.
Raised 2026-10-25.

## [2026-10-25] [seed] Decide at intent whether a change reaches hosts

This repo is the plugin's testbed, so whatever it builds for itself should reach hosts in some
form, but whether, and how generically, is decided late and implicitly today (010's `after_bump`
was settled mid-intent; 008 and 009 changed this repo alone). Ask it at intent as its own question
(plugin only, host-facing, or both, with this repo as the first user) and record it, so the spec
designs for the host from the start and ship can check the change delivered on it. Raised
2026-10-25.

## [2026-10-25] [seed] A glossary of the process's terms

The plugin's words (change, tier, stage, gate, WAIT, stop, seed, nit, finding, impact, landed,
retro, direction, outcome, drift…) are defined only where they're used, and someone new meets them
in skill prompts long before SDLC.md. A `docs/GLOSSARY.md`, linked from the README, gives each a
line and points at where it's specified, with a test that fails when a term the code fixes
(`STAGES`, tiers, impacts, nit costs and values, review passes) has no entry. Hosts read it on
GitHub; a copy from setup is a later, Tier 2 question. Pairs with the process map, whose labels
should use its terms. Raised 2026-10-25.

## [2026-10-25] [seed] A changelog that keeps its own layout

`release.changelog` puts each release's `## X.Y.Z — date` section right under the file's `# `
title. A changelog that opens with prose or a table before its releases is split by it, and a Keep
a Changelog file's `## [Unreleased]` section is left above the new one. Let a host mark where
releases go (`<!-- sdlc:releases -->`, inserted after), falling back to today's place, and make the
section heading a template a host can override. Tier 2: it changes what release writes in a host.
Raised 2026-10-25 by a host.

## [2026-10-25] [seed] Version lines release can't read, and the first release's baseline

`VERSION_RE` reads `version = "x"` and `"version": "x"`, not Python's `__version__ = "x"`, so a
host has to move its version elsewhere to use `/sdlc:release`. And with no tag for the current
version, release's `git tag -a` hint points at the last commit that touched the version files,
which can predate the repo's adoption of the plugin, so the first release takes in every change
closed since. Read the dunder form, and point the hint at the adoption commit when that is later.
Raised 2026-10-25 by a host.

## [2026-10-25] [seed] Publish's "published" note never leaves the machine

Publish marks a tag `published` in `refs/notes/sdlc` so a rerun skips the host's upload, but the
notes ref isn't pushed: from a second clone, publish runs the upload again. Push the notes ref with
the tag (inside `cmd_publish`, so only publish still pushes), or ask the remote. Also say in
`docs/REFERENCE.md` that the tag message holds the notes (`gh release create {tag}
--notes-from-tag`), that `release.prepare` can show what a push will upload (`git lfs push
--dry-run`), and that releases outside `release.tag`'s pattern live outside the loop. Raised
2026-10-25 by a host.

## [2026-10-25] [seed] Close warns before its merge deletes files in the main checkout

A change that untracks files the main checkout still holds (data kept out of git from then on)
deletes them there when close fast-forwards `main`. They are in history, but the person isn't
told. `close --check` could list the tracked paths the merge removes, so the approval names them.
Not an automatic `after_close` command: `close_cleanup` stays the person's to run. Raised
2026-10-25 by a host.

## [2026-10-25] [seed] Small gaps in sync and worktree setup

`sync` rewrites an issue's body but never its title, so an intent retitled at spec leaves the issue
on the old one. `commands.worktree_setup` gets `{worktree}` but not `{main}`, so a host linking
untracked data from the main checkout works the path out from `git rev-parse --git-common-dir`.
Tier 1 together. Raised 2026-10-25 by a host.

## [2026-10-25] [seed] A local channel for bug reports and feature requests from other sessions

Working locally across several repos, a session in a host that hits a plugin bug or wants a
feature has no channel but the person: they copy what it wrote into the plugin's session, which
files it by hand. Give it one: a host session sends a report (what happened, the repro, the
plugin version, the host's change) to a live session working on the plugin, by cross-session
message or a drop folder the plugin's session reads, and that session triages it into a seed or a
bug entry behind one approval. A report never names the host in what lands here (the repo's
nothing-local rule), so triage rewrites it in neutral terms. The first phase of an intake for bugs
and requests; the register and the GitHub channel are their own seeds. Raised 2026-10-25.

## [2026-10-25] [seed] A bugs register beside the ideas register

A bug isn't a seed: it has a severity, a repro and something already broken, and wants triage
before it waits its turn, where a seed waits until someone wants it. Weigh a `work/bugs.md` shaped
like `work/nits.md` (`## <id> [<severity>] <title>`, `reported`, `repro`, `paths`, read as text by
`sdlc.py`, written by skills behind a WAIT), against tagging bugs inside `work/ideas.md`
(`[bug]`, one register, no new reader, but no severity to sort by and nothing for status or retro
to count apart). Feature requests stay seeds either way. Then: what status and retro show
(open bugs by severity, age), how `/sdlc:intent` promotes one, and whether a fix's ship retires
it as it does a nit. Raised 2026-10-25.

Track fixes through the change cycle, for the retrospective. A change that fixes a bug names it
(`fixes: [B3]` in the intent, set when `/sdlc:intent` promotes the entry), ship retires the entry,
and close writes an `Sdlc-Fixes:` trailer (extending the trailer contract, not redefining it), so
history keeps the link. Triage may record `introduced_by:` the change that let the bug through:
that splits escaped bugs from retro's rework, which can't tell a planned follow-up from a defect.
Retro then counts bugs reported and fixed in its window by severity, time from report to fix, open
bugs by age, and escapes per introducing change against its tier; the product doc may own a
measure such as escaped bugs per release. This leans the choice above toward the separate
register: tags in `work/ideas.md` give retro nothing to count or link a fix to. Raised 2026-10-25.

After: "A local channel for bug reports and feature requests from other sessions"

## [2026-10-25] [seed] GitHub issues as the intake for bugs and requests, in hosts too

Where `archive.target` is GitHub, a bug or request filed as an issue (by a person, or by a host
session through `gh`) is the remote form of the local channel: triage reads open issues that no
change claims (no `sdlc` archive label), and files each as a seed or a bug entry, or links it to
the change that takes it on. This serves hosts as much as the plugin: a host's own users file
issues, and its sessions triage them the same way, so the design is a host feature first, with
this repo as its first user. Phases: the plugin's own local intake, the register, then GitHub
triage, then the same in hosts (an issue template from setup, a `/sdlc:triage` skill). Raised
2026-10-25.

After: "A bugs register beside the ideas register"
