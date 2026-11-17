# Ideas

Seeds, not a backlog. `/sdlc:intent` promotes one into a change.

## [2026-10-24-2] [idea] A factory queue, and parallel runs across worktrees

The factory runs one change per session. A queue (`/sdlc-factory:next` over seeds or
open intents) and several runs at once, one per worktree, would let ideas move while nobody
watches. GitHub issues and `work/ideas.md` are already the queue; this is the runner. Raised
2026-10-24.
Theme: factory
Priority: low

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

## [2026-10-27-10] [idea] Let answers move a filled prompt into its guide slot

`sdlc.py answers` keeps a filled prompt under its old key, so a migrated host's answer to "the
failure it stops" stays in `## The point of the process` rather than `### The failure it stops`.
Map each old prompt to its slot. See .sdlc/work/032-process-guide-in-plugin/notes.md.
Theme: setup
Priority: low

## [2026-11-10-2] [idea] Cover the tool prompts a default-mode host's skills meet

What 2026-10-26-5 first set out to do, left once 047 found no prompt recorded here
(`prompt_modes=auto` on every Close commit): once a host running in `default` mode records
`Sdlc-Prompt` lines, give each recurring prompt that isn't asking on purpose the `allowed-tools`
rule its skill lacks, or move its logic into `sdlc.py`. See .sdlc/work/047-cut-extra-stops/notes.md.
Theme: permissions
Raised 2026-11-10.

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


## [2026-11-17-3] [idea] Say each rule once in AGENTS.md

`AGENTS.md` was edited by 23 of the 27 changes in the window and is now 447 lines. It changed
alongside `docs/REFERENCE.md` 17 times and alongside `scripts/sdlc.py` 17 times. Two Important
findings came from a rule restated in several places and edited in only one:
- 046's "six lines still said only publish pushes";
- 049's "the docs that list the extra-stop kinds leave out the new `fix` kind".

Cut the Architecture map down to its boundaries and the rules that aren't obvious from the code,
and point at `docs/REFERENCE.md` or the docstring for each feature's detail. Ship's context pass
would then also ask whether a proposed line is already said elsewhere. Raised by the retrospective
of 2026-11-17.
Theme: docs

## [2026-11-17-4] [idea] Retro checks its goals and the work against the outcomes

The product pass scores each outcome, but it never asks whether the outcomes still cover the work.
8 of the window's 27 changes served `none`, most of them cost and cleanup work the person counts as
important. Last time, M12 was drafted with no goal or outcome behind it. Each retrospective would:
- name the goals and milestones that cite no outcome;
- group the changes that serve `none` by theme;
- where a theme keeps recurring, propose an outcome line (a new `O<n>`) for the person to approve
  at its WAIT.

The script could list the `none` changes by theme in `product`, so the skill doesn't group them by
hand. Raised by the retrospective of 2026-11-17.
Theme: retro

## [2026-11-17-6] [nit] No skill case runs intent with a product doc

The `intent` case's fixture has no `.sdlc/PRODUCT.md`, so no paid run shows intent proposing
`serves:` without asking and naming the outcomes at its gate; only the skill's wording is pinned.
Theme: tests
Paths: evals/intent/, evals/fixtures/
Cost: M
Value: med
Raised by: 069-intent-proposes-serves (correctness)


## [2026-11-17-10] [idea] Try the landing on a real factory batch

`/sdlc-factory:land` shipped tested against scratch repos and a fake `claude`. A paid run, two
ready changes from a real supervised run (seed 2026-11-17-7) landed from a fresh session in the
main checkout, is the only check of the marketplace cache lookup of sdlc's script, of the builder
resolving a real conflict and the reviewers checking it in headless sessions, and of close's push
from a subprocess. See .sdlc/work/072-factory-land/notes.md in 072's commit.
After: 2026-11-17-7
Theme: factory

## [2026-11-17-11] [nit] resolve stops when a merge empties one of the branch's commits

`git rebase --continue` refuses with "No changes" when merging a conflict leaves a commit with
nothing of its own, and `resolve --continue` reports "the rebase won't go on", so ship aborts and
stops. Nothing is lost. The fix is `git rebase --skip` on that answer, minding the aside commit.
Theme: landing
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 077-ship-resolves-conflicts (correctness)

## [2026-11-17-14] [idea] Board tests serve on port 0 rather than a port picked free beforehand

`tests/test_board.py`'s `_free_port()` releases the port before `board.serve()` binds it, so under
`-n auto` another worker could take it between. Serving on port 0 and reading the bound port back
closes the window. See .sdlc/work/082-parallel-gate/notes.md in 082's commit.
Theme: tests

## [2026-11-17-15] [idea] A progress indicator on the board's cards

Show how far a change has got, so the person can see it from the board rather than asking. For a
factory run, a step track from what `verdicts` already knows: build, gate, reviews n/m, verify,
rework, approve. For the step running now, a bar of elapsed time against the typical time for that
step and tier, read from history: `Close` commits' `Sdlc-Stage … elapsed=` and `runs/costs.jsonl`'s
`duration_ms` by role. It's labelled an estimate and never passes about 95% until the step ends.
Under it, a hint of how many of `plan.md`'s named files have been touched so far. Computed on every
refresh, nothing stored. Build it after 085-factory-stopped-runs lands, since both change the
factory card.
Theme: board
Raised 2026-11-17.

## [2026-11-17-16] [idea] Resume an escalated factory run

`factory.py start` refuses a change at `stage: test` (`STARTS` has no `test`), and `verdicts` reads
the old `decision.md` as `done`, so an ESCALATE can only be shipped by hand or dropped. `start`
should accept a `test` change whose decision is ESCALATE, move it back to `build`, keep the old
decision as `decision-<n>.md`, and give the next round's builder the escalation's reasons. It
touches what `start` accepts and what a run leaves in its folder, so likely Tier 2. Build it after
the board's stage-gated columns.
Theme: factory
Raised 2026-11-17.
