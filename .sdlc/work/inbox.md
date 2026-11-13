# Ideas

Seeds, not a backlog. `/sdlc:intent` promotes one into a change.

## [2026-10-24-1] [idea] UX and UI reviewers for the factory, and how a repo declares a front end

The factory ships code, security and test reviewers. The factory it learned from also
runs UX and UI reviewers against a running app. agent-skills has no such agent, only its
`frontend-ui-engineering` skill to write them from, and the plugin can't know a repo has a UI: it
needs a declaration (a `factory.toml` key, or `commands.preview` for a dev server) before a UI
reviewer can run. Raised 2026-10-24.
Theme: factory
Priority: low

## [2026-10-24-2] [idea] A factory queue, and parallel runs across worktrees

The factory runs one change per session. A queue (`/sdlc-factory:next` over seeds or
open intents) and several runs at once, one per worktree, would let ideas move while nobody
watches. GitHub issues and `work/ideas.md` are already the queue; this is the runner. Raised
2026-10-24.
Theme: factory
Priority: low

## [2026-10-24-3] [idea] A factory status board

A page that shows each running change's stage, round and verdicts as they land, from the change
folders' files, the way the factory it learned from shows a dashboard. Read-only. Raised
2026-10-24.
Theme: factory
Priority: low

## [2026-10-24-4] [idea] A retro report and process views from each change's numbers

Close records each change's numbers; render them: a templated report the
script fills with no model tokens, committed with each retrospective. Then add the process views
it makes possible: capacity (how many changes one person runs at once before cycle time rises
and throughput doesn't), changes open at once, the human's wait time against agent time, and
throughput by tier per week alongside cycle time and rework, roughly DORA's set. Avoid a single
velocity figure, which invites optimising the number. A dashboard is optional and comes after the
report: the process doc keeps "no dashboard" for the signals. Raised 2026-10-24.
Theme: retro

## [2026-10-24-6] [idea] Landing changes through pull requests, for teams

Close lands a change by fast-forwarding `main` locally, and only publish pushes. A team that
reviews through pull requests would want ship to push the branch and open a PR (its body carrying
`Closes #N`), close to wait for the merge on GitHub and then fast-forward from the remote, and the
PR's review to stand alongside ship's. An opt-in way of landing, not a default, and an exception
to "only publish pushes" made on purpose. It builds on the issue closing when its `Close` commit
reaches the remote. Raised 2026-10-24.
Theme: landing
Priority: low

## [2026-10-25-1] [idea] A process map of the three loops, kept true by the gate

A map of the change loop (intent → spec → plan → build → ship → close), the release loop (release
→ publish) and the retro loop: each stage's gates, the `sdlc.py` calls, the checks (gate,
acceptance checks, review passes) and what it writes. Mermaid in the repo (`docs/PROCESS.md`,
rendered by GitHub), with a test that fails when a stage, skill or WAIT is missing from it; HTML
or a diagramming tool can be generated from it later. Decide whether hosts get a copy from setup.
Raised 2026-10-25.
Theme: docs
Priority: low

## [2026-10-25-2] [idea] Decide at intent whether a change reaches hosts

This repo is the plugin's testbed, so whatever it builds for itself should reach hosts in some
form, but whether, and how generically, is decided late and implicitly today (010's `after_bump`
was settled mid-intent; 008 and 009 changed this repo alone). Ask it at intent as its own question
(plugin only, host-facing, or both, with this repo as the first user) and record it, so the spec
designs for the host from the start and ship can check the change delivered on it. Raised
2026-10-25.
Theme: intent
Priority: low

## [2026-10-25-3] [idea] A glossary of the process's terms

The plugin's words (change, tier, stage, gate, WAIT, stop, seed, nit, finding, impact, landed,
retro, direction, outcome, drift…) are defined only where they're used, and someone new meets them
in skill prompts long before SDLC.md. A `docs/GLOSSARY.md`, linked from the README, gives each a
line and points at where it's specified, with a test that fails when a term the code fixes
(`STAGES`, tiers, impacts, nit costs and values, review passes) has no entry. Hosts read it on
GitHub; a copy from setup is a later, Tier 2 question. Pairs with the process map, whose labels
should use its terms. Raised 2026-10-25.
Theme: docs
Priority: low

## [2026-10-25-4] [idea] A changelog that keeps its own layout

`release.changelog` puts each release's `## X.Y.Z — date` section right under the file's `# `
title. A changelog that opens with prose or a table before its releases is split by it, and a Keep
a Changelog file's `## [Unreleased]` section is left above the new one. Let a host mark where
releases go (`<!-- sdlc:releases -->`, inserted after), falling back to today's place, and make the
section heading a template a host can override. Tier 2: it changes what release writes in a host.
Raised 2026-10-25 by a host.
Theme: release
Priority: low

## [2026-10-25-5] [idea] Version lines release can't read, and the first release's baseline

`VERSION_RE` reads `version = "x"` and `"version": "x"`, not Python's `__version__ = "x"`, so a
host has to move its version elsewhere to use `/sdlc:release`. And with no tag for the current
version, release's `git tag -a` hint points at the last commit that touched the version files,
which can predate the repo's adoption of the plugin, so the first release takes in every change
closed since. Read the dunder form, and point the hint at the adoption commit when that is later.
Raised 2026-10-25 by a host.
Theme: release
Priority: low

## [2026-10-25-6] [idea] Publish's "published" note never leaves the machine

Publish marks a tag `published` in `refs/notes/sdlc` so a rerun skips the host's upload, but the
notes ref isn't pushed: from a second clone, publish runs the upload again. Push the notes ref with
the tag (inside `cmd_publish`, so only publish still pushes), or ask the remote. Also say in
`docs/REFERENCE.md` that the tag message holds the notes (`gh release create {tag}
--notes-from-tag`), that `release.prepare` can show what a push will upload (`git lfs push
--dry-run`), and that releases outside `release.tag`'s pattern live outside the loop. Raised
2026-10-25 by a host.
Theme: release
Priority: low

## [2026-10-25-7] [idea] Close warns before its merge deletes files in the main checkout

A change that untracks files the main checkout still holds (data kept out of git from then on)
deletes them there when close fast-forwards `main`. They are in history, but the person isn't
told. `close --check` could list the tracked paths the merge removes, so the approval names them.
Not an automatic `after_close` command: `close_cleanup` stays the person's to run. Raised
2026-10-25 by a host.
Theme: landing

## [2026-10-25-8] [idea] Small gaps in sync and worktree setup

`sync` rewrites an issue's body but never its title, so an intent retitled at spec leaves the issue
on the old one. `commands.worktree_setup` gets `{worktree}` but not `{main}`, so a host linking
untracked data from the main checkout works the path out from `git rev-parse --git-common-dir`.
Tier 1 together. Raised 2026-10-25 by a host.
Theme: robustness

## [2026-10-25-9] [idea] A local channel for bug reports and feature requests from other sessions

Working locally across several repos, a session in a host that hits a plugin bug or wants a
feature has no channel but the person: they copy what it wrote into the plugin's session, which
files it by hand. Give it one: a host session sends a report (what happened, the repro, the
plugin version, the host's change) to a live session working on the plugin, by cross-session
message or a drop folder the plugin's session reads, and that session triages it into a seed or a
bug entry behind one approval. A report never names the host in what lands here (the repo's
nothing-local rule), so triage rewrites it in neutral terms. The first phase of an intake for bugs
and requests; the register and the GitHub channel are their own seeds. Raised 2026-10-25.
Theme: intake

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
Theme: retro

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
Theme: setup
Priority: low

## [2026-10-25-24] [idea] Record each change's type, and let the host decide where it shows

The process doc names the types a seed grows into (`feature`, `fix`, `refactor`, `perf`, `docs`,
`test`, `chore`), but nothing records which one a change is. Give the intent a `type:` key that
intent proposes from the seed's kind (a `[bug]` suggests `fix`) and `check` validates against the
process doc's list, so a host can add its own words. Where it shows is the host's choice, said in
config: a subject prefix (`fix: …`, Conventional Commits) for a repo that uses one, an
`Sdlc-Type:` trailer on the `Close` commit beside `Sdlc-Fixes:`, or nowhere. Retro can then count
changes by type, and release can group its notes by it. Tier 2: a new intent key and what
`sdlc.py` writes in a host. Raised 2026-10-25, from 025's vocabulary.
Theme: intent
Priority: low

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

## [2026-10-26-7] [idea] Pay down the robustness nits

The `robustness` theme holds five open nits, the threshold the process doc sets for one paydown
change: 2026-10-25-13 and 2026-10-25-14 (status's `After:` handling), 2026-10-25-17 (a file
after-bump staged, missing from a failed release's report), 2026-10-25-18 (a change sized from an
intent committed early) and 2026-10-26-1 (an issue that hears nothing until the next marking).
Fix them in one change, each retired by its ship. Raised by the retrospective of 2026-10-26.
Theme: robustness
Priority: high

## [2026-10-26-8] [idea] Leave each change's measured numbers out of retro's and release's output

`sdlc.py retro` and `unreleased` print every change's full `metrics` blob, half of retro's output
in the last window (about 39 KB of 78 KB compact, twenty changes), and `release --check` prints
it again. Retro's skill reads only the medians in `metrics`, and release reads none. Leave the
per-change blob out by default, behind a flag for anyone who wants it, so each retrospective and
release reads a fraction of the tokens. Raised by the retrospective of 2026-10-26.
Theme: cost

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
Theme: intake

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
Theme: setup
Priority: low

## [2026-10-26-13] [idea] Support moving the change folder, once a host needs it

027 fixed the folder at .sdlc/work/ and supports one move only, from the old work/. Moving it
again, or choosing a path, was left out on purpose: no host needs it. It would need a `Move work`
commit with an `Sdlc-Work: from= to=` trailer, a resolver giving the folder at any commit, and a
rule every reader of history follows. History from .sdlc/work/ on sits at one path, so nothing
from before has to be carried back. See work/027-work-path/spec.md (Alternatives rejected).
Theme: setup
Priority: low

## [2026-10-26-14] [nit] No test pins that readiness lost its inbox item

A readiness `inbox` item coming back would pass the suite; assert it is absent from
`cmd_readiness`'s items.

Theme: tests
Paths: tests/test_inbox.py
Cost: S
Value: low
Raised by: 028-remove-1-4-shims (correctness)

## [2026-10-27-4] [nit] close --check previews reaches without the change's start

`--check` writes no ref, so `_change_base` falls back to the intent rule and the preview can
list fewer skills than the close reports. Pass the base branch's tip as the start under --check.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 029-close-records-base (correctness)

## [2026-10-27-8] [nit] _inbox_commit takes eleven parameters

`cmd_inbox_commit()` hands its whole state to `_inbox_commit()` to hold the lock around it; a
nested function, or the lock taken inside, would carry it with no parameter list.

Theme: style
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 031-idea-skill (cost)

## [2026-10-27-10] [idea] Let answers move a filled prompt into its guide slot

`sdlc.py answers` keeps a filled prompt under its old key, so a migrated host's answer to "the
failure it stops" stays in `## The point of the process` rather than `### The failure it stops`.
Map each old prompt to its slot. See .sdlc/work/032-process-guide-in-plugin/notes.md.
Theme: setup
Priority: low

## [2026-11-03-16] [nit] Setup offers risky-path candidates its Step 1 never looks for

Step 1 reads the README, task files, tests and entry points, not CI workflows or release scripts,
which Step 2's `[review]` question offers as candidates. Name them in Step 1.

Theme: docs
Paths: skills/setup/SKILL.md
Cost: S
Value: low
Raised by: 036-review-depth-by-risk (correctness)

## [2026-11-04-1] [nit] Retro's never-writes test greps retro-commit's source

`test_retro_proposes_review_changes_as_seeds_and_never_writes_them` asserts `review` and
`config.toml` are absent from `cmd_retro_commit`'s source, so only a rename fails it. Commit a
retro whose tree also changes `.sdlc/REVIEW.md` and assert the refusal instead.

Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 037-escaped-bugs-tune-review (correctness)

## [2026-11-04-2] [nit] A findings.md from history that no longer parses reads as fewer findings

`_review_at` drops `_findings_from_text`'s problems, so an unparseable section vanishes from
`review.findings` and `important` while `state` says `file`. Carry them as `review.problems`.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 037-escaped-bugs-tune-review (correctness)

## [2026-11-04-5] [nit] The factory's review proposes severities it may not be able to read

`/sdlc-factory:review` proposes each bug's `Severity:` from the process doc's words, but a host
whose doc has no bugs section takes them from `sdlc`'s guide, which the factory's cached copy
can't read. Leave `Severity:` for `/sdlc:bug` to ask when the host's doc has no words.

Theme: robustness
Paths: plugins/factory/skills/review/SKILL.md
Cost: S
Value: low
Raised by: 040-factory-eval-and-review (correctness)

## [2026-11-04-7] [idea] Setup stops on a set-up repo before reading its first-setup steps

Rerunning `/sdlc:setup` on a repo that is set up reads the whole skill (307 lines, about 5,500
tokens) to reach an answer `readiness` and `drift` already decide: nothing to write. Have
`readiness` say `complete` when every item is `ok` and `drift` has nothing in `breaking`, `refresh`
or `report`, and move the first setup's steps (the profile round, the drafts) to a file setup reads
only when it isn't. Raised by the retrospective of 2026-11-04.

After: 2026-11-04-6
Theme: cost

## [2026-11-04-8] [idea] Pay down the tests nits

The `tests` theme holds five open nits, the threshold the process guide sets for one paydown
change: 2026-10-24-7 (a half that can't fail), 2026-10-25-22 and 2026-11-04-1 (tests that grep a
function's source), 2026-10-26-3 (no adoption test runs `closes:`) and 2026-10-26-14 (nothing pins
that readiness lost its inbox item). Fix them in one change, each retired by its ship. Raised by
the retrospective of 2026-11-04.
Theme: tests

## [2026-11-04-10] [idea] Move retro's history readers out of sdlc.py

`scripts/sdlc.py` is 7,729 lines, up from 7,047 at the last retrospective, and 12 of the window's 14
changes touched it; that retrospective proposed splitting it as an intent nobody opened. Its retro
section alone runs about 1,400 lines, read-only and called only by `retro` and `retro-commit`. Move
it to `scripts/retro.py`, loaded by path like `metrics.py`, leaving the history walks it shares with
release (`closed_changes()`, `_change_base()`) in `sdlc.py`; the spec decides how they reach it.
One boundary first, not a rewrite. Raised by the retrospective of 2026-11-04.
Theme: refactor
Priority: low

## [2026-11-04-12] [nit] The LF test checks write_text only, not a write-mode open

`test_every_file_written_is_lf` walks `write_text` calls; a later `open(p, "w")` would write CRLF on
Windows unnoticed. Walk write-mode `open` calls too.

Theme: tests
Paths: tests/test_windows.py
Cost: S
Value: low
Raised by: 041-windows-lock (correctness)

## [2026-11-04-13] [nit] The CI workflow runs twice on every publish

`on: push` fires for the branch push and again for the tag push `/sdlc:publish` makes. Filter it
to branches.

Theme: cost
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 041-windows-lock (cost)

## [2026-11-04-14] [nit] The factory's `_utf8_streams` copy isn't pinned to sdlc.py's

The repo pins its other copies by test (`risk_paths()`, the regexes, `trackers/command.py`'s
`_sh`); this one can drift. Pin it the same way.

Theme: tests
Paths: plugins/factory/scripts/factory.py, tests/test_windows.py
Cost: S
Value: low
Raised by: 041-windows-lock (contract)

## [2026-11-08-1] [idea] Readiness groups for the backlog, and taking a theme as one change

Status now ranks and groups by theme (044), but two things were deferred. First, readiness groups
(ship today / needs you / blocked) need an effort signal ideas don't carry, and tagging every
entry by hand is too much work. Infer it from where an entry came from: findings a change's review
raised versus seeds the person wrote themselves, which go in a group of their own for the person
to decide whether they're worth building. Keep status short: either make it deterministic or give
it a skill of its own. Second, one change should be able to take a whole theme's ideas: today
`idea:` names one seed and ship deletes only that one.
Theme: status
Raised 2026-11-08.

## [2026-11-08-2] [nit] A change folder in the main checkout reads as in flight from any dirty file

last_touched() reads every dirty path in the checkout; for a folder in the main checkout, keep
only the paths under the change's own folder.
Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 044-status-ranks-the-backlog (correctness)

## [2026-11-08-3] [idea] Retro re-ranks the inbox

After its passes, the retrospective proposes Priority: lines for the register's open ideas and bugs:
high for what the new direction and milestones make urgent, or what a pass found biting now (stops
measured past their target, a rule a seed says is broken, landed work piling up unpushed); low for
what the direction puts off; and drops a Priority: line that no longer holds. It proposes a Theme:
for any entry still without one, the way /sdlc:idea --themes does. One table behind retro's one
approval, committed with the Retrospective commit, so status's Next up starts each cycle in the
order the retro decided, without the person ranking it by hand between retros.
After: 2026-11-08-1
Theme: retro
Raised 2026-11-08.

## [2026-11-10-1] [idea] Factory gates that pass themselves when nothing is risky

The factory is meant to be fully automated development that raises only high-risk decisions to
the person. Build already runs that way (one WAIT, then unattended, with blocking decisions and
ESCALATE raised), but intent, spec, ship and close still stop for a yes every time, and skills
carry `disable-model-invocation: true`, so only something like `factory.py` could run the loop.

Let a gate pass itself only when every risk signal the script already reads is clear: no
`[review] sensitive` or `irreversible` path in the diff, impact below `major`, no contract
touched, no open blocking decision, no ESCALATE, no Important finding from the fresh reviewer, the
gate green. Any signal stops it, with the reason. Staged:

1. After M8: one factory-built change closed here, its numbers beside the manual medians.
2. Ship passes itself on a clear diff. The reply is recorded as its own kind (`reply=auto`), never
   as the person's approve, so retro's stops and review counts stay true (G3). `checks.md` still
   needs a person for `accept`, or a factory change carries none.
3. Close stays the person's, or at least its push: in factory mode `push = []`, and changes wait
   for one `/sdlc:publish` the person approves as a batch.
4. Intent stays the person's: a queue (2026-10-24-2) takes only seeds the person marked ready.

Risks it has to answer: agents reviewing agents (the fresh reviewer's blind spots match the
builder's); close's push is the least reversible step; issue text filed from the public reaching
an unattended build that lands and pushes (prompt injection); unattended token spend, capped per
run today, not per queue.
Theme: factory
Raised 2026-11-10.

## [2026-11-10-2] [idea] Cover the tool prompts a default-mode host's skills meet

What 2026-10-26-5 first set out to do, left once 047 found no prompt recorded here
(`prompt_modes=auto` on every Close commit): once a host running in `default` mode records
`Sdlc-Prompt` lines, give each recurring prompt that isn't asking on purpose the `allowed-tools`
rule its skill lacks, or move its logic into `sdlc.py`. See .sdlc/work/047-cut-extra-stops/notes.md.
Theme: permissions
Raised 2026-11-10.

## [2026-11-12-1] [nit] A hotspot's lines: null reads as deleted for a binary or empty file

`hotspots()` takes `lines` from `git grep -I -c ''`, which skips binary and empty files, so a
much-edited image or empty file shows `lines: null`, which the docstring calls "once it is gone".
Say which, or count those files' presence from `git ls-tree`.
Theme: retro
Paths: scripts/indicators.py, scripts/sdlc.py
Cost: S
Value: low
Raised by: 048-architecture-indicators (correctness)

## [2026-11-12-2] [idea] Verbosity, tool-call and test-pruning indicators for the retro loop

The parts of 2026-10-24-5 that 048-architecture-indicators left out of scope, to build on the
`architecture` block it added to `sdlc.py retro`:
- verbosity against complexity: how much a change's code comments say, and how much the human and
  the agent said in its conversation, set beside how complex the change is (its diff, its tier,
  and the host's complexity measure where there is one, now `retro.indicators`), so a change that
  commented or talked far more than its size needed stands out. Close already records the
  conversation's tokens and turns per stage (`Sdlc-Totals`, `Sdlc-Stage`); comments come from the
  diff;
- tool calls: how often each tool is called in a change, by stage (by program for a shell call),
  set beside what the calls led to (an edit kept, a check run, a finding), to show which calls are
  most useful and which are spent. Close already names each tool prompt on the `Close` commit;
  this counts every call, prompted or not;
- a pruning pass for the suite: the process guide sets each test's lifetime when it is written,
  and ship flags a test that can't fail or that only a revert could fail, but only in the diff it
  reviews. Nothing looks at the tests already in the suite again: one whose code was rewritten,
  one that repeats a newer test, one that now passes for the wrong reason, the slowest. Retro
  proposes the candidates as a `tests` paydown seed, and the person decides which go.
Any of the three may become a seed of its own when an intent finds it too big.
Theme: retro
Raised 2026-11-12.

## [2026-11-13-1] [idea] Approve-path cases for the skill evals

053 landed the six stop-at-WAIT cases; the cases approved through a WAIT (its spec's R3, R5 and
R6: intent and ship continuing a stop case's transcript with `yes`) are left. The native
transcript is in a run kept with `run-cases --keep`, under its `config/projects/*/<session>.jsonl`,
and ends at the WAIT as needed, but it carries the machine's absolute paths (the plugin root in
every command), so it can't be committed or replayed elsewhere. The likely design: histories kept
out of git, captured per machine before a run, and approve cases skipped while theirs is missing.
See .sdlc/work/053-skill-evals/notes.md in 053's commit.
Theme: tests

## [2026-11-13-2] [nit] A bare pointer to a renamed side file passes the side-file test

The side-file test checks a bare `file.md` pointer in SKILL.md only against files that exist, so
a pointer left naming a renamed branch file isn't caught; full `skills/<name>/<file>` paths are.
Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 056-ship-reads-rare-branches (correctness)
