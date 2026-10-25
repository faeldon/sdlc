# Ideas

Seeds, not a backlog. `/sdlc:intent` promotes one into a change.

## [2026-10-24-1] [seed] UX and UI reviewers for the factory, and how a repo declares a front end

The factory ships code, security and test reviewers. The factory it learned from also
runs UX and UI reviewers against a running app. agent-skills has no such agent, only its
`frontend-ui-engineering` skill to write them from, and the plugin can't know a repo has a UI: it
needs a declaration (a `factory.toml` key, or `commands.preview` for a dev server) before a UI
reviewer can run. Raised 2026-10-24.

## [2026-10-24-2] [seed] A factory queue, and parallel runs across worktrees

The factory runs one change per session. A queue (`/sdlc-factory:next` over seeds or
open intents) and several runs at once, one per worktree, would let ideas move while nobody
watches. GitHub issues and `work/ideas.md` are already the queue; this is the runner. Raised
2026-10-24.

## [2026-10-24-3] [seed] A factory status board

A page that shows each running change's stage, round and verdicts as they land, from the change
folders' files, the way the factory it learned from shows a dashboard. Read-only. Raised
2026-10-24.

## [2026-10-24-4] [seed] A retro report and process views from each change's numbers

Close records each change's numbers; render them: a templated report the
script fills with no model tokens, committed with each retrospective. Then add the process views
it makes possible: capacity (how many changes one person runs at once before cycle time rises
and throughput doesn't), changes open at once, the human's wait time against agent time, and
throughput by tier per week alongside cycle time and rework, roughly DORA's set. Avoid a single
velocity figure, which invites optimising the number. A dashboard is optional and comes after the
report: the process doc keeps "no dashboard" for the signals. Raised 2026-10-24.

## [2026-10-24-5] [seed] Architecture indicators for the retro loop

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

## [2026-10-24-6] [seed] Landing changes through pull requests, for teams

Close lands a change by fast-forwarding `main` locally, and only publish pushes. A team that
reviews through pull requests would want ship to push the branch and open a PR (its body carrying
`Closes #N`), close to wait for the merge on GitHub and then fast-forward from the remote, and the
PR's review to stand alongside ship's. An opt-in way of landing, not a default, and an exception
to "only publish pushes" made on purpose. It builds on the issue closing when its `Close` commit
reaches the remote. Raised 2026-10-24.

## [2026-10-25-1] [seed] A process map of the three loops, kept true by the gate

A map of the change loop (intent → spec → plan → build → ship → close), the release loop (release
→ publish) and the retro loop: each stage's gates, the `sdlc.py` calls, the checks (gate,
acceptance checks, review passes) and what it writes. Mermaid in the repo (`docs/PROCESS.md`,
rendered by GitHub), with a test that fails when a stage, skill or WAIT is missing from it; HTML
or a diagramming tool can be generated from it later. Decide whether hosts get a copy from setup.
Raised 2026-10-25.

## [2026-10-25-2] [seed] Decide at intent whether a change reaches hosts

This repo is the plugin's testbed, so whatever it builds for itself should reach hosts in some
form, but whether, and how generically, is decided late and implicitly today (010's `after_bump`
was settled mid-intent; 008 and 009 changed this repo alone). Ask it at intent as its own question
(plugin only, host-facing, or both, with this repo as the first user) and record it, so the spec
designs for the host from the start and ship can check the change delivered on it. Raised
2026-10-25.

## [2026-10-25-3] [seed] A glossary of the process's terms

The plugin's words (change, tier, stage, gate, WAIT, stop, seed, nit, finding, impact, landed,
retro, direction, outcome, drift…) are defined only where they're used, and someone new meets them
in skill prompts long before SDLC.md. A `docs/GLOSSARY.md`, linked from the README, gives each a
line and points at where it's specified, with a test that fails when a term the code fixes
(`STAGES`, tiers, impacts, nit costs and values, review passes) has no entry. Hosts read it on
GitHub; a copy from setup is a later, Tier 2 question. Pairs with the process map, whose labels
should use its terms. Raised 2026-10-25.

## [2026-10-25-4] [seed] A changelog that keeps its own layout

`release.changelog` puts each release's `## X.Y.Z — date` section right under the file's `# `
title. A changelog that opens with prose or a table before its releases is split by it, and a Keep
a Changelog file's `## [Unreleased]` section is left above the new one. Let a host mark where
releases go (`<!-- sdlc:releases -->`, inserted after), falling back to today's place, and make the
section heading a template a host can override. Tier 2: it changes what release writes in a host.
Raised 2026-10-25 by a host.

## [2026-10-25-5] [seed] Version lines release can't read, and the first release's baseline

`VERSION_RE` reads `version = "x"` and `"version": "x"`, not Python's `__version__ = "x"`, so a
host has to move its version elsewhere to use `/sdlc:release`. And with no tag for the current
version, release's `git tag -a` hint points at the last commit that touched the version files,
which can predate the repo's adoption of the plugin, so the first release takes in every change
closed since. Read the dunder form, and point the hint at the adoption commit when that is later.
Raised 2026-10-25 by a host.

## [2026-10-25-6] [seed] Publish's "published" note never leaves the machine

Publish marks a tag `published` in `refs/notes/sdlc` so a rerun skips the host's upload, but the
notes ref isn't pushed: from a second clone, publish runs the upload again. Push the notes ref with
the tag (inside `cmd_publish`, so only publish still pushes), or ask the remote. Also say in
`docs/REFERENCE.md` that the tag message holds the notes (`gh release create {tag}
--notes-from-tag`), that `release.prepare` can show what a push will upload (`git lfs push
--dry-run`), and that releases outside `release.tag`'s pattern live outside the loop. Raised
2026-10-25 by a host.

## [2026-10-25-7] [seed] Close warns before its merge deletes files in the main checkout

A change that untracks files the main checkout still holds (data kept out of git from then on)
deletes them there when close fast-forwards `main`. They are in history, but the person isn't
told. `close --check` could list the tracked paths the merge removes, so the approval names them.
Not an automatic `after_close` command: `close_cleanup` stays the person's to run. Raised
2026-10-25 by a host.

## [2026-10-25-8] [seed] Small gaps in sync and worktree setup

`sync` rewrites an issue's body but never its title, so an intent retitled at spec leaves the issue
on the old one. `commands.worktree_setup` gets `{worktree}` but not `{main}`, so a host linking
untracked data from the main checkout works the path out from `git rev-parse --git-common-dir`.
Tier 1 together. Raised 2026-10-25 by a host.

## [2026-10-25-9] [seed] A local channel for bug reports and feature requests from other sessions

Working locally across several repos, a session in a host that hits a plugin bug or wants a
feature has no channel but the person: they copy what it wrote into the plugin's session, which
files it by hand. Give it one: a host session sends a report (what happened, the repro, the
plugin version, the host's change) to a live session working on the plugin, by cross-session
message or a drop folder the plugin's session reads, and that session triages it into a seed or a
bug entry behind one approval. A report never names the host in what lands here (the repo's
nothing-local rule), so triage rewrites it in neutral terms. The first phase of an intake for bugs
and requests; the register and the GitHub channel are their own seeds. Raised 2026-10-25.

## [2026-10-25-11] [seed] GitHub issues as the intake for bugs and requests, in hosts too

Where `archive.target` is GitHub, a bug or request filed as an issue (by a person, or by a host
session through `gh`) is the remote form of the local channel: triage reads open issues that no
change claims (no `sdlc` archive label), and files each as a seed or a bug entry, or links it to
the change that takes it on. This serves hosts as much as the plugin: a host's own users file
issues, and its sessions triage them the same way, so the design is a host feature first, with
this repo as its first user. Phases: the plugin's own local intake, the register, then GitHub
triage, then the same in hosts (an issue template from setup, a `/sdlc:triage` skill). Raised
2026-10-25.

After: 2026-10-25-10

## [2026-10-25-12] [seed] Rework as a declared fix, with surviving lines as the cross-check

Retro pairs any two changes closed within a week that share a file. With the common files left
out (021), the 17 changes since the last retrospective still hold 42 pairs, nearly all same-week
changes adding to a shared skill or test file, not one fixing another. Reframe it in two parts:
- **Declared, the signal.** A later change names the earlier changes it reworks, in a `reworks:`
  frontmatter line (one or more change ids, read as text like `depends_on:`), which intent asks
  for when the problem traces to an earlier change. Retro counts these links, whatever the gap in
  days, and `check` refuses an id that names no change.
- **Inferred, the cross-check.** Lines an earlier change added that a later one modifies or
  deletes within the window, found by blaming the earlier change's hunks. Appending to a shared
  file no longer counts; replacing what the earlier change wrote does. A hit with no `reworks:`
  link is a question for the retrospective (an undeclared fix, or a planned follow-up), never a
  count.
The file pairs, `REWORK_DAYS` as a match rule and `rework_common` go. Close's in-change rework
(`Sdlc-Rework`) is untouched. Its own key, not `fixes:`, which names the inbox's `[bug]` entries a
change fixes (024): a change can have both, a bug it fixes and the change that let it through,
which that bug's `Introduced by:` line already records, so retro can cross-check the two.
See work/021-rework-shared-files/.

## [2026-10-25-19] [seed] Push at close and at release, not only at publish

Only publish pushes, so a closed change sits on the local `main` until the next publish: no
backup, no other machine sees it, and its issue (labelled `landed`) waits for the `Closes #N` to
reach the remote. An opt-in key (a `[git] push` naming `close`, `release` or both) would let close
push `main` after its `Close` commit and release push `main` and the tag, to `release.remote`,
never forced. It is an exception to "only publish pushes" made on purpose: the test pinning that
rule names the steps allowed instead. A release push needs care where the remote's default branch
is what users install from (this repo's marketplace): a pushed version bump is already a publish,
so release may push only the tag there, or nothing. Landing through pull requests is the other
half of this, seeded on its own above. Raised 2026-10-25.

## [2026-10-25-20] [seed] Keep the change folders under .sdlc/, or where a host says

`work/` sits at a host's root, beside its own code, so adopting the plugin adds a top-level folder
a host never asked for. Move it under `.sdlc/` (`.sdlc/work/`, with `ideas.md` and `nits.md`), or
make it a config key (`[paths] work`, defaulting to `work` so no host moves unasked). `work_dir()`
is already the one place the path is built, but `work/` is written literally across the script's
messages and globs, the skills, the defaults, the templates and the docs. History is the harder
part: `closed_changes()` reads each intent from the `Close` commit's parent at its old path, the
seed counter reads `Close` and `Drop` subjects, and retro reads `ideas.md` and `nits.md` across
the window, so a move needs either a reader that looks in both places or a recorded switch point
(setup's record, or a `Move work` commit). Decide whether setup moves an existing host's folder
and records it, what `drift()` makes of a host on the old path, and whether the key is ever
retired. Worktrees follow the folder, since each holds its own `<work>/<branch>/`. Tier 2: it
changes where every host's artifacts live. Raised 2026-10-25.

## [2026-10-25-21] [seed] Agent attribution in a host's commits, off by default

The commits `sdlc.py` makes (`Close`, `Drop`, release, retro) carry only the `Sdlc-*` trailers,
but the ones a session makes for a skill (ship's commit, the factory's build) take the harness's
`Co-Authored-By:` line and, on a pull request, its "Generated with Claude Code" footer. This repo
forbids them in AGENTS.md; a host gets them unless it writes the same rule. Make it a config key
(`[git] attribution = false` by default) that setup turns into Claude Code's own `attribution`
setting in the host's `.claude/settings.json`, beside the allow rules it already writes there, and
records, so `uninstall` takes it out and `drift()` sees a host that changed it. The object form,
`{"commit": "", "pr": "", "sessionUrl": false}` (an empty string hides that line, `sessionUrl`
the session link a cloud session appends), not `"attribution": false`: Claude Code before
v2.1.281 rejects that and skips the whole settings file, allow rules and all. Have the skills that
commit say the same in prose, since `.claude/settings.local.json` and managed settings override
the project file. Ask at setup rather than assume: some teams want the line. Also decide whether the
text the plugin writes into issues follows the same key. Raised 2026-10-25.

## [2026-10-25-23] [seed] Setup refreshes template overrides the way it refreshes docs

A host's override in `.sdlc/templates/` drifts from the plugin's template just as a host doc drifts
from its default, but setup handles only the docs. `record` keeps one hash of each whole plugin
template, so `drift()` can only say `changed` and point at the plugin's file; a person diffs and
merges it by hand, and an override nobody revisits keeps an old shape while the plugin's moves on.
Treat overrides like docs: record a hash per block (`doc_units()`, a section or a `- **lead**`
bullet) of each plugin template, classify an override's blocks three ways against it, and put the
blocks the plugin changed and the host never touched under `refresh`, with the whole override as
`proposed` and every other block as the host wrote it; a block both sides changed is a
`conflict` in `report`. `breaking` (`_template_misses()`, `TEMPLATE_READS`) stays as it is.
Decide what a template's frontmatter counts as (it is keys, not a block), whether
`templates/issue.md`, whose text is every issue's body, splits into blocks at all, and what a
record from before this change reads as (`base: none`, so `differs`, never proposed). Raised
2026-10-25.

## [2026-10-24-7] [nit] A deprecations status test whose patched half can't fail

The half of the `status` test that runs with a patch applied can't fail, so it proves nothing.

Theme: tests
Paths: tests/test_deprecations.py
Cost: S
Value: low
Raised by: 003-test-lifetimes (correctness)

## [2026-10-24-8] [nit] The `RECORD_CLEARS` tuple-unpacking idiom

The set is built from two unpacked tuples where one set literal reads plainer.

Theme: style
Paths: tests/test_defaults.py
Cost: S
Value: low
Raised by: 009-drift-message (cost)

## [2026-10-24-9] [nit] Two release-skill lines run past 100 characters

The WAIT variant and a Step 1 line added for `after_bump`.

Theme: style
Paths: skills/release/SKILL.md
Cost: S
Value: low
Raised by: 010-release-lock (cost)

## [2026-10-25-13] [nit] A mistyped After: title makes a seed "next in series"

`next_up` labels a ready seed `next in series` when none of its `After:` titles is in the
register, so a title naming nothing gets that label as well as its `⚠` warning. Check it against
the titles history has shipped too.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 019-status-next-work (correctness)

## [2026-10-25-14] [nit] A loop through a seed's second After: title isn't reported

`_after_loops` follows only each waiting seed's first waiting `After:` title, so seeds that wait
on each other through a later title are never listed and never warned about.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 019-status-next-work (correctness)

## [2026-10-25-15] [nit] Status can walk main's history twice

With an open milestone and a dangling `After:` title, `next_up` calls `closed_changes(home, None)`
once through `_milestone_verdicts` and once for the shipped titles, reading every closed intent
both times. Walk it once and pass it in.

Theme: cost
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 019-status-next-work (cost)

## [2026-10-25-16] [nit] load_config runs git on every call to resolve the base branch

`_resolve_trunk` runs up to three `git` calls each time `load_config()` does, and some commands
call it several times; nothing is slow yet, but one resolved value could be passed down instead.

Theme: perf
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 018-base-branch (cost)

## [2026-10-25-17] [nit] A failed commit or prepare doesn't list a new file after-bump staged

`restore()` after a later failure unstages it into an untracked file, but `untracked` was taken
at after-bump, so the report never names it.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 022-robustness-nits (correctness)

## [2026-10-25-18] [nit] A change sized from an intent committed to main early counts others' commits

`_change_base` takes the parent of the commit that first added the intent. If that commit landed
on main before other changes closed (an intent committed outside its branch), the range from it
to the change's commit spans their commits too, in `retro`'s size and in close's `_change_diff`.
A `Close` or `Drop` commit inside the range would show it.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 023-branch-size (correctness)

## [2026-10-25-22] [nit] A test that close alone records fixes greps the source

`test_only_a_close_records_fixes_never_a_drop` checks `inspect.getsource` for `fix_trailers(`, so
only a rename or a revert fails it. Close a dropped change that has `fixes:` and assert its `Drop`
commit carries no `Sdlc-Fixes:` line.

Theme: tests
Paths: tests/test_bugs.py
Cost: M
Value: low
Raised by: 024-bugs-register (correctness)
