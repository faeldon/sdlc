# Ideas

Seeds, not a backlog. `/sdlc:intent` promotes one into a change.

## [2026-10-24-1] [idea] UX and UI reviewers for the factory, and how a repo declares a front end

The factory ships code, security and test reviewers. The factory it learned from also
runs UX and UI reviewers against a running app. agent-skills has no such agent, only its
`frontend-ui-engineering` skill to write them from, and the plugin can't know a repo has a UI: it
needs a declaration (a `factory.toml` key, or `commands.preview` for a dev server) before a UI
reviewer can run. Raised 2026-10-24.

## [2026-10-24-2] [idea] A factory queue, and parallel runs across worktrees

The factory runs one change per session. A queue (`/sdlc-factory:next` over seeds or
open intents) and several runs at once, one per worktree, would let ideas move while nobody
watches. GitHub issues and `work/ideas.md` are already the queue; this is the runner. Raised
2026-10-24.

## [2026-10-24-3] [idea] A factory status board

A page that shows each running change's stage, round and verdicts as they land, from the change
folders' files, the way the factory it learned from shows a dashboard. Read-only. Raised
2026-10-24.

## [2026-10-24-4] [idea] A retro report and process views from each change's numbers

Close records each change's numbers; render them: a templated report the
script fills with no model tokens, committed with each retrospective. Then add the process views
it makes possible: capacity (how many changes one person runs at once before cycle time rises
and throughput doesn't), changes open at once, the human's wait time against agent time, and
throughput by tier per week alongside cycle time and rework, roughly DORA's set. Avoid a single
velocity figure, which invites optimising the number. A dashboard is optional and comes after the
report: the process doc keeps "no dashboard" for the signals. Raised 2026-10-24.

## [2026-10-24-5] [idea] Architecture indicators for the retro loop

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

## [2026-10-24-6] [idea] Landing changes through pull requests, for teams

Close lands a change by fast-forwarding `main` locally, and only publish pushes. A team that
reviews through pull requests would want ship to push the branch and open a PR (its body carrying
`Closes #N`), close to wait for the merge on GitHub and then fast-forward from the remote, and the
PR's review to stand alongside ship's. An opt-in way of landing, not a default, and an exception
to "only publish pushes" made on purpose. It builds on the issue closing when its `Close` commit
reaches the remote. Raised 2026-10-24.

## [2026-10-25-1] [idea] A process map of the three loops, kept true by the gate

A map of the change loop (intent → spec → plan → build → ship → close), the release loop (release
→ publish) and the retro loop: each stage's gates, the `sdlc.py` calls, the checks (gate,
acceptance checks, review passes) and what it writes. Mermaid in the repo (`docs/PROCESS.md`,
rendered by GitHub), with a test that fails when a stage, skill or WAIT is missing from it; HTML
or a diagramming tool can be generated from it later. Decide whether hosts get a copy from setup.
Raised 2026-10-25.

## [2026-10-25-2] [idea] Decide at intent whether a change reaches hosts

This repo is the plugin's testbed, so whatever it builds for itself should reach hosts in some
form, but whether, and how generically, is decided late and implicitly today (010's `after_bump`
was settled mid-intent; 008 and 009 changed this repo alone). Ask it at intent as its own question
(plugin only, host-facing, or both, with this repo as the first user) and record it, so the spec
designs for the host from the start and ship can check the change delivered on it. Raised
2026-10-25.

## [2026-10-25-3] [idea] A glossary of the process's terms

The plugin's words (change, tier, stage, gate, WAIT, stop, seed, nit, finding, impact, landed,
retro, direction, outcome, drift…) are defined only where they're used, and someone new meets them
in skill prompts long before SDLC.md. A `docs/GLOSSARY.md`, linked from the README, gives each a
line and points at where it's specified, with a test that fails when a term the code fixes
(`STAGES`, tiers, impacts, nit costs and values, review passes) has no entry. Hosts read it on
GitHub; a copy from setup is a later, Tier 2 question. Pairs with the process map, whose labels
should use its terms. Raised 2026-10-25.

## [2026-10-25-4] [idea] A changelog that keeps its own layout

`release.changelog` puts each release's `## X.Y.Z — date` section right under the file's `# `
title. A changelog that opens with prose or a table before its releases is split by it, and a Keep
a Changelog file's `## [Unreleased]` section is left above the new one. Let a host mark where
releases go (`<!-- sdlc:releases -->`, inserted after), falling back to today's place, and make the
section heading a template a host can override. Tier 2: it changes what release writes in a host.
Raised 2026-10-25 by a host.

## [2026-10-25-5] [idea] Version lines release can't read, and the first release's baseline

`VERSION_RE` reads `version = "x"` and `"version": "x"`, not Python's `__version__ = "x"`, so a
host has to move its version elsewhere to use `/sdlc:release`. And with no tag for the current
version, release's `git tag -a` hint points at the last commit that touched the version files,
which can predate the repo's adoption of the plugin, so the first release takes in every change
closed since. Read the dunder form, and point the hint at the adoption commit when that is later.
Raised 2026-10-25 by a host.

## [2026-10-25-6] [idea] Publish's "published" note never leaves the machine

Publish marks a tag `published` in `refs/notes/sdlc` so a rerun skips the host's upload, but the
notes ref isn't pushed: from a second clone, publish runs the upload again. Push the notes ref with
the tag (inside `cmd_publish`, so only publish still pushes), or ask the remote. Also say in
`docs/REFERENCE.md` that the tag message holds the notes (`gh release create {tag}
--notes-from-tag`), that `release.prepare` can show what a push will upload (`git lfs push
--dry-run`), and that releases outside `release.tag`'s pattern live outside the loop. Raised
2026-10-25 by a host.

## [2026-10-25-7] [idea] Close warns before its merge deletes files in the main checkout

A change that untracks files the main checkout still holds (data kept out of git from then on)
deletes them there when close fast-forwards `main`. They are in history, but the person isn't
told. `close --check` could list the tracked paths the merge removes, so the approval names them.
Not an automatic `after_close` command: `close_cleanup` stays the person's to run. Raised
2026-10-25 by a host.

## [2026-10-25-8] [idea] Small gaps in sync and worktree setup

`sync` rewrites an issue's body but never its title, so an intent retitled at spec leaves the issue
on the old one. `commands.worktree_setup` gets `{worktree}` but not `{main}`, so a host linking
untracked data from the main checkout works the path out from `git rev-parse --git-common-dir`.
Tier 1 together. Raised 2026-10-25 by a host.

## [2026-10-25-9] [idea] A local channel for bug reports and feature requests from other sessions

Working locally across several repos, a session in a host that hits a plugin bug or wants a
feature has no channel but the person: they copy what it wrote into the plugin's session, which
files it by hand. Give it one: a host session sends a report (what happened, the repro, the
plugin version, the host's change) to a live session working on the plugin, by cross-session
message or a drop folder the plugin's session reads, and that session triages it into a seed or a
bug entry behind one approval. A report never names the host in what lands here (the repo's
nothing-local rule), so triage rewrites it in neutral terms. The first phase of an intake for bugs
and requests; the register and the GitHub channel are their own seeds. Raised 2026-10-25.

## [2026-10-25-12] [idea] Rework as a declared fix, with surviving lines as the cross-check

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

## [2026-10-25-19] [idea] Say when to push, and nudge when landed work piles up unpushed

Only publish pushes, so a closed change sits on the local `main` until the next publish: no
backup, no other machine sees it, and its issue (labelled `landed`) waits for the `Closes #N` to
reach the remote. Pushing stays a step the person approves, never automatic. Two parts:
- **When, as config.** A `[git] push` key naming the points a skill offers a push: `close` (after
  its `Close` commit), `release` (`main` and the tag), or none, the default. At each point named,
  the skill asks, behind its WAIT or as its own question after the commit, and pushes to
  `release.remote`, never forced. It is an exception to "only publish pushes" made on purpose: the
  test pinning that rule names the steps allowed instead.
- **A nudge, whatever the key.** `status` and close's report count what `main` holds that the
  remote doesn't: closed changes, and on GitHub the issues labelled `landed` still open because
  their `Closes #N` hasn't reached it. Past a threshold (a count of changes or an age, in config),
  they suggest a push and name what it would close. A nudge is never a problem and never a gate.
A release push needs care where the remote's default branch is what users install from (this
repo's marketplace): a pushed version bump is already a publish, so release may push only the tag
there, or nothing, and the nudge says so rather than suggesting a push that releases. Landing
through pull requests is the other half of this, seeded on its own above. Raised 2026-10-25;
revised 2026-10-26: never automatic, and a nudge when landed work piles up.

## [2026-10-25-21] [idea] Agent attribution in a host's commits, off by default

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

## [2026-10-25-23] [idea] Setup refreshes template overrides the way it refreshes docs

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

## [2026-10-25-24] [idea] Record each change's type, and let the host decide where it shows

The process doc names the types a seed grows into (`feature`, `fix`, `refactor`, `perf`, `docs`,
`test`, `chore`), but nothing records which one a change is. Give the intent a `type:` key that
intent proposes from the seed's kind (a `[bug]` suggests `fix`) and `check` validates against the
process doc's list, so a host can add its own words. Where it shows is the host's choice, said in
config: a subject prefix (`fix: …`, Conventional Commits) for a repo that uses one, an
`Sdlc-Type:` trailer on the `Close` commit beside `Sdlc-Fixes:`, or nowhere. Retro can then count
changes by type, and release can group its notes by it. Tier 2: a new intent key and what
`sdlc.py` writes in a host. Raised 2026-10-25, from 025's vocabulary.

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

## [2026-10-25-17] [nit] A failed commit or prepare doesn't list a new file after-bump staged

`restore()` after a later failure unstages it into an untracked file, but `untracked` was taken
at after-bump, so the report never names it.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 022-robustness-nits (correctness)

## [2026-10-25-22] [nit] A test that close alone records fixes greps the source

`test_only_a_close_records_fixes_never_a_drop` checks `inspect.getsource` for `fix_trailers(`, so
only a rename or a revert fails it. Close a dropped change that has `fixes:` and assert its `Drop`
commit carries no `Sdlc-Fixes:` line.

Theme: tests
Paths: tests/test_bugs.py
Cost: M
Value: low
Raised by: 024-bugs-register (correctness)

## [2026-10-26-1] [nit] An issue intent carries onto closes: hears nothing until the next marking

`/sdlc:intent` copies an entry's `Issue:` numbers onto `closes:`, and its `sync` makes each a
sub-issue, but the "Taken on by" comment waits for the next `mark-triaged` or the change's close.

Theme: robustness
Paths: skills/intent/SKILL.md, scripts/sdlc.py
Cost: S
Value: low
Raised by: 026-github-intake (correctness)

## [2026-10-26-2] [nit] mark_issues views every open recorded issue on each run

`mark_issues()` runs one `gh issue view` per open issue the repo records, on every triage and every
close, idempotent but growing with the open issues. Skip the ones already labelled `triaged` with
their marker, from one `issue list`.

Theme: cost
Paths: scripts/sdlc.py, scripts/trackers/github.py
Cost: S
Value: low
Raised by: 026-github-intake (cost)

## [2026-10-26-3] [nit] No adoption test runs a change with closes: through uv run --script

Spec Verification named one; the `closes:` → `Closes #N` path is covered in `test_archive.py`
through the imported script only.

Theme: tests
Paths: tests/test_adoption.py
Cost: S
Value: low
Raised by: 026-github-intake (correctness)

## [2026-10-26-4] [idea] Close records what each permission stop asked for

Close counts a change's permission prompts among its stops (median 3 for a Tier 2 change and 2.5
for a Tier 1 in the last window), but not which tool or command each was for, so nobody can tell
the ones a skill's `allowed-tools` should have covered from the ones that ask on purpose (`accept`).
Record each prompt's tool and the command's first word, numbers and names only, on the `Close`
commit, and let retro group them across the window. Raised by the retrospective of 2026-10-26.

## [2026-10-26-5] [idea] Cover the permission prompts a skill's rules should have

Once close names them, take the prompts that recur across changes and aren't asking on purpose,
and give each the rule its skill was missing, or move its logic into `sdlc.py` where a rule can
cover it. This is what brings the median Tier 1 change within its stop target (7 against 5 in the
last window). Raised by the retrospective of 2026-10-26.

After: 2026-10-26-4

## [2026-10-26-6] [idea] A ship that fixes its own review finding is not a miss

`happy()` marks ship `no` whenever the person answers anything but yes inside it, so "fix a finding
first", which is the review doing its job, counts the same as a loop that circled. Ship went
through first time in 5 of 12 Tier 2 changes and 4 of 8 Tier 1 in the last window, and those
numbers can't say which. Count a ship that stopped for a finding its own review raised apart from
one rerun for any other reason, and let `first_time` count only the second kind. Raised by the
retrospective of 2026-10-26.

## [2026-10-26-7] [idea] Pay down the robustness nits

The `robustness` theme holds five open nits, the threshold the process doc sets for one paydown
change: 2026-10-25-13 and 2026-10-25-14 (status's `After:` handling), 2026-10-25-17 (a file
after-bump staged, missing from a failed release's report), 2026-10-25-18 (a change sized from an
intent committed early) and 2026-10-26-1 (an issue that hears nothing until the next marking).
Fix them in one change, each retired by its ship. Raised by the retrospective of 2026-10-26.

## [2026-10-26-8] [idea] Leave each change's measured numbers out of retro's and release's output

`sdlc.py retro` and `unreleased` print every change's full `metrics` blob, half of retro's output
in the last window (about 39 KB of 78 KB compact, twenty changes), and `release --check` prints
it again. Retro's skill reads only the medians in `metrics`, and release reads none. Leave the
per-change blob out by default, behind a flag for anyone who wants it, so each retrospective and
release reads a fraction of the tokens. Raised by the retrospective of 2026-10-26.

## [2026-10-26-10] [idea] Setup fits the GitHub intake to a host's own issue templates

Setup offers the two issue forms whenever `archive.target` is GitHub, and counts one as the host's
only when a file already sits at its own path (`.github/ISSUE_TEMPLATE/sdlc-bug.yml`,
`sdlc-request.yml`). A host that designed its own bug and feature templates gets the plugin's
added beside them: two bug forms in the chooser, and the host's own never asked for the fields
`/sdlc:triage` reads. Read the host's `.github/ISSUE_TEMPLATE/` (forms and Markdown templates, and
`config.yml`) first, and ask per template: add the plugin's beside it, replace it, or extend it
with the fields triage needs (severity, the paths, a repro) and leave the rest as the host wrote
it. Then decide what triage does with an issue from a template that lacks them (ask for the
missing facts, as `needs-info` does), and what `drift` and `uninstall` make of a host template
setup extended rather than created. Raised 2026-10-26, after running setup on a host with its own
templates.

## [2026-10-26-11] [idea] Uninstall offers to clean the plugin's mentions out of a host

Uninstall removes only what setup's record says setup wrote, and lists the mentions it finds
elsewhere without editing them: `work/`, `AGENTS.md`, `CLAUDE.md` and the rest are out of its
scope. On a host set up by a much older version, before setup kept a record, that leaves most of
the plugin behind: the policy doc still describes the plugin's stages and skills, and Markdown
files and code across the repo still name `/sdlc:*`, `.sdlc/`, `work/` and the process. Offer a
cleanup as part of the same approval, mention by mention: drafted edits to the policy doc and
the context docs that take out what only the plugin needed (its sections, its invariants, the
commands it runs) and keep what the host still relies on, and the other mentions in docs and code
listed with a proposed edit or left as they are, the host's call each time. Decide what happens
to `work/` and the inbox (removed, kept as the project's history, or left for the host), what
counts as a mention (a regex over paths and skill names, or the docs `context` already lists),
and how an old host with no record is told what can't be attributed to setup. Edits stay the
host's to commit, like the rest of uninstall. Raised 2026-10-26, after uninstalling from a host
set up by an early version.

## [2026-10-26-12] [nit] move-work leaves work/ behind when it holds ignored files

`git mv` moves what git tracks; an ignored file keeps work/ on disk, and the repo then reads as
half-moved. Move or remove what's left, or refuse with the list.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 027-work-path (correctness)

## [2026-10-26-13] [idea] Support moving the change folder, once a host needs it

027 fixed the folder at .sdlc/work/ and supports one move only, from the old work/. Moving it
again, or choosing a path, was left out on purpose: no host needs it. It would need a `Move work`
commit with an `Sdlc-Work: from= to=` trailer, a resolver giving the folder at any commit, and a
rule every reader of history follows. History from .sdlc/work/ on sits at one path, so nothing
from before has to be carried back. See work/027-work-path/spec.md (Alternatives rejected).

## [2026-10-26-14] [nit] No test pins that readiness lost its inbox item

A readiness `inbox` item coming back would pass the suite; assert it is absent from
`cmd_readiness`'s items.

Theme: tests
Paths: tests/test_inbox.py
Cost: S
Value: low
Raised by: 028-remove-1-4-shims (correctness)

## [2026-10-27-2] [building] An /sdlc:idea skill, and inbox-commit for every kind of entry

Building in .sdlc/work/031-idea-skill/.
`bug-commit` already commits any change to the register: it diffs it against `HEAD` and writes
`File <id>`, `Update <id>` or `Retire <id>` for each entry, whatever its kind, and triage uses it to
file ideas split off from issues. But its name says bugs, its retire reasons (`duplicate`,
`not-a-bug`, `wontfix`, `cant-reproduce`) only fit bugs, and no skill files an idea someone
dictates mid-session: `/sdlc:bug` files bugs, triage files issues, ship files nits and carried
items, retro its own seeds. So ideas get committed by hand, under subjects nothing in history
reads (`Seed <id>: …`). Three parts:
- **Rename** `bug-commit` to `inbox-commit`, with no shim: no host has run it yet. The bug and
  triage skills' `allowed-tools` rules, the docs and the tests follow the new name.
- **Retire reasons by kind:** an idea's are `superseded` and `declined` (beside `duplicate`), a
  bug's stay as they are, and a nit is ship's to retire, so it needs none here.
- **`/sdlc:idea`**: takes the idea in the person's words, drafts the entry in neutral terms with
  an id from `next-entry` (an `After:` line when it follows another seed), and after its one WAIT
  appends it and runs `inbox-commit`. Editing or retiring an existing idea goes through the same
  skill.
Tier 2: it renames a command a skill's `allowed-tools` names, and adds a skill that writes.
Raised 2026-10-27.

## [2026-10-27-4] [nit] close --check previews reaches without the change's start

`--check` writes no ref, so `_change_base` falls back to the intent rule and the preview can
list fewer skills than the close reports. Pass the base branch's tip as the start under --check.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 029-close-records-base (correctness)

## [2026-10-27-6] [nit] preflight ignores --context, --nits, --closing and --split without --question

`preflight 030 --closing 5` prints the lookup JSON and drops the flags silently; refuse them
unless `--question` is given.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 030-ship-preflight (correctness)

## [2026-10-27-7] [nit] ship_question renders a repeated issue number twice

`--closing 4 --closing 4` reads "closing #4 and #4"; dedupe the numbers before rendering.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 030-ship-preflight (correctness)

## [2026-10-27-5] [idea] Keep the plugin's process guide in the plugin, and only a host's answers in .sdlc/

Setup copies the whole of `defaults/SDLC.md` (499 lines) into a host, though only its seven `<`
prompts and a few settings are the host's: the failure to stop, worktree needs, Stage 1 push-backs,
the gate's prose, the path to users, scans, the always-Tier-2 carve-outs, severity words, change
types and the nit rubric. The rest describes the plugin itself, and editing it in a host changes
nothing but makes the doc wrong; keeping a host's 30 lines while taking the plugin's updates to the
other 470 is most of what `drift`'s block hashes and three-way compare exist for. Same for
`REVIEW.md`: the default passes are the plugin's, the added failure classes the host's.
Read the guide and the default review in place from the plugin, as the review fallback already
does; the host's `.sdlc/SDLC.md` and `REVIEW.md` hold only its answers and additions, and skills
read both. No edit protection: there is nothing of the plugin's left in the host to protect.
The trade-off is visibility: a host no longer reads the whole process in its own repo, and a
plugin update changes it without a setup diff to review. The host file's note links the guide at
the installed version, and setup or status reports when the guide changed since setup's record, as
a note to read, never a refresh. Existing hosts migrate once (setup cuts their docs to their
answers, keeping what they edited, shown as a diff), a shim with a `remove_in`. HEALTH, PRODUCT,
PROJECT and the direction doc stay as they are: they are wholly the host's.
