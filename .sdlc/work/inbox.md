# Ideas

Seeds, not a backlog. `/sdlc:intent` promotes one into a change.

## [2026-10-24-2] [idea] A factory queue

A queue (`/sdlc-factory:next` over seeds or open intents) would let ideas move while nobody
watches: the supervisor (070) already runs several changes at once, one per worktree, but the
person still starts each. The register and GitHub issues are already the queue; this is the
runner. Raised 2026-10-24.
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


## [2026-11-17-19] [idea] Port 0 for the factory's UI review server

089 closed the pick-then-bind window in the board's tests by serving on port 0. `factory.py`'s
`_free_port()` (about line 2767) keeps a cousin of it: it picks a port for the UI review's dev
server and releases it before the outside `[ui] serve` command binds it, so a parallel run could
take it between. It needs a design of its own (a retry, or a serve command that reports its port).
The board's half, `sdlc.py board --port 0` printing `http://127.0.0.1:0/`, goes with the board
fixes of 2026-11-17-30.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-22] [nit] The board's step track reads decision.md at any stage

`_progress()` takes any `decision.md` as a finished run, so a change put back to `build` shows
every step done in the Build column. Gate it by stage, as 086 did for the column and the next
action.
Theme: robustness
Paths: scripts/board.py
Cost: M
Value: med
Raised by: 086-board-signals-by-stage (correctness)

## [2026-11-17-23] [bug] A board card whose file won't read says /sdlc:close at a closed stage

Found by the review of 086-board-signals-by-stage. `next_action()` returns `/sdlc:close NNN`
before it looks at `problems`, so a card under Needs you names a close (scripts/board.py:574-577).
Severity: low
Paths: scripts/board.py

## [2026-11-17-24] [bug] At phone width the board's Needs you column comes last

Found by the review of 086-board-signals-by-stage. Below 760px the columns stack in stage order,
so the one that waits on the person is under all the others (scripts/board.html:44-46).
Severity: low
Paths: scripts/board.html

## [2026-11-17-25] [bug] The board's file drawer has no focus trap

Found by the review of 086-board-signals-by-stage. The drawer is `aria-modal`, but Tab moves into
the page behind the scrim (scripts/board.html:136).
Severity: low
Paths: scripts/board.html

## [2026-11-17-26] [bug] The verifier's chip on a board card explains itself only in a tooltip

Found by the review of 086-board-signals-by-stage. `kept 1 · dropped 2` says whose count it is
only in its `title`, which keyboard, touch and screen-reader users don't get
(scripts/board.html:196-198).
Severity: low
Paths: scripts/board.html

## [2026-11-17-27] [idea] Bring sdlc.py's docstrings up to date: the .sdlc/work/ name and the subcommand list

AGENTS.md now points at docstrings for detail, and some are stale: `sdlc.py`'s module docstring,
`change_dirs()`, `next_id()`, `claim()` and `cmd_uninstall()` still name the change folder `work/`
(its pre-1.4.0 name), and the module docstring lists about half the subcommands (no `base`,
`resolve`, `preflight`, `findings`, `checks`, `accept`, `board`, `record`, `drift`, …): complete
it, or cut it to the module's purpose. See .sdlc/work/090-agents-rules-once/notes.md in 090's
commit.
Theme: docs
Raised 2026-11-17.

## [2026-11-17-28] [idea] CONTRIBUTING's Writing a tracker lists the intake methods

AGENTS.md points at CONTRIBUTING.md's *Writing a tracker* for the tracker interface, which leaves
out the intake methods core calls when a tracker has them: `mark()`, `unmark()`, `needs_info()`,
`open_marks()`, `open_numbers()`, `closed_by()`. See .sdlc/work/090-agents-rules-once/notes.md in
090's commit.
Theme: docs
Raised 2026-11-17.

## [2026-11-17-29] [bug] _drop_record()'s docstring breaks off mid-sentence

Found by the review of 090-agents-rules-once.
Its docstring ends "Why not, or" (scripts/sdlc.py:4186), so a reader following AGENTS.md's
pointers into close's docstrings meets half a rule.

Severity: low
Paths: scripts/sdlc.py

## [2026-11-17-30] [bug] The board drops a change while its branch is being rebased

While `resolve` or a landing rebases a change, git lists its worktree as a detached `HEAD`, so the
board can't match the worktree to its branch and the card vanishes until the rebase ends. Seen on
2026-11-17 for 091, 090 and 095 during their landings. It should find the branch from the
rebase's own state (`rebase-merge/head-name`) and keep the card, marked as rebasing.

Severity: med
Paths: scripts/board.py, scripts/sdlc.py
Theme: board

## [2026-11-17-37] [idea] The landing follows main when it moves before the close

When another session lands a change between a landing's review and its close, `land --close`
refuses (close only fast-forwards) and someone runs `base` by hand, then gates again. The landing
could loop back to its own rebase step and regate, stopping only on a conflict. Hit by 094 and 095
on 2026-11-17.
Theme: landing
Raised 2026-11-17.

## [2026-11-17-38] [idea] A fix made at landing goes back through review

When the person asks for a fix after the approver (088's plan hint, 094's AGENTS.md line on
2026-11-17), the supervisor makes it by hand and the change lands `by=person` with no reviewer
having read the fix. The landing could hand such a fix to the change's builder and its reviewers,
or at least record on the commit that a hand fix landed unreviewed.
Theme: landing
Raised 2026-11-17.

## [2026-11-17-40] [idea] factory.py start brings the change's branch up to date first

Every run on 2026-11-17 started from a worktree branched hours earlier, so the supervisor ran
`sdlc.py base` (or `resolve`) by hand on each before building, or the builder would have built on
old code. `start` could report how far behind the change is and the build skill run `base` before
the first agent.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-41] [idea] Open changes mark their seeds without editing the register

Intent tags a change's seed `[building]` by editing the register on the change's branch, so every
inbox commit on `main` while the change is open conflicts with it at rebase: 089, 090, 092, 094
and 095 all did on 2026-11-17. Status and the board could derive "being built" from open changes'
`idea:` lines instead, leaving the register untouched until ship deletes the seed.
Theme: inbox
Raised 2026-11-17.

## [2026-11-17-42] [idea] The spec-writer's draft is written to a file

`factory.py agent --task spec` returns the draft only in its reply, so the supervisor cuts
`spec.md` out of the text; a draft holding its own code fences was cut short twice on 2026-11-17.
The command could write the draft to the change's folder (say `runs/spec-draft.md`), which Step 3
copies after the yes.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-43] [idea] Limit how many factory gates run at once

With five runs in parallel on 2026-11-17, a gate that takes 40 s alone took up to 200 s, each
`pytest -n auto` fighting the others for every core. A small `factory.gate_jobs` limit, or a lock
the gate waits on, would keep each one near its usual time.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-44] [idea] decisions flags a default that contradicts an earlier one

086's D2 (no badge on a shipped escalated card) and D4 (keep `was ESCALATE`) contradicted each
other, and only the approver noticed. `factory.py decisions` could ask a later default whether it
replaces an earlier one, and mark the earlier one superseded in the ledger.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-45] [idea] A Tier 2 at the light depth gets the test reviewer too

At the light depth only the code reviewer runs, so 092's and 095's tests were never read
requirement by requirement, and both approvers said so. A Tier 2's spec names a test per
requirement; the test reviewer could join its light rounds.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-46] [idea] The UI reviewers see the cards a change adds

No screenshot on 2026-11-17 showed 088's step track, 086's `was ESCALATE` or 091's gate badge: the
dev server served this repo's board, whose changes had none of those states, so the ui and ux
reviewers judged them from code alone. `[ui]` could name fixture data the server starts with.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-47] [idea] The board serves the code it was built from

`sdlc.py board` loads `board.py` once, so after a change to it lands the running server shows the
old behaviour (091 sat under Needs you until a restart picked up 086). It could reload the module
when the file changes, or say on the page that it's stale.
Theme: board
Raised 2026-11-17.

## [2026-11-17-48] [idea] check --strict stays quiet about a plan a running build is writing

`check --strict` reports "plan.md is still the template at stage: build" for a factory change
whose builder is writing that plan right now. It could leave out a change with a live run
(`runs/step.md` naming `build` for round 1).
Theme: factory
Raised 2026-11-17.

## [2026-11-17-49] [idea] One review checklist and one findings record for ship and the factory

`/sdlc:ship` and the factory review a change differently, and each misses what the other checks.
Ship has a context pass (docs still true), nits weighed and recorded in the register, existing
faults filed as bugs, acceptance checks, skills' cases and `How to recover:`; the factory has none
of them (35 and 39 cover part). The factory has a test reviewer (do the tests prove the
requirements, can they fail), security depth, the spec's path run end to end, a verifier that
drops false positives, and UI/UX; ship has none of them, but the fresh reviewer on a sensitive
path. Standardize what a review covers and how it is recorded, not how it runs: a keyed checklist
of review dimensions in `guide/review.md`, each naming who covers it in each way; then fill each
gap where it is cheapest (likely first: ship's correctness pass asks whether each test can fail;
the factory gets the context pass and files its nits and bugs); and both write `findings.md` in
one shape with `By: <role>`, so the retro can compare them from then on without counting a
factory review as the person's.

Decide from the evidence already in history, no experiment: the factory's `reviews/round-N/` and
`verified.md` in each landed factory change's commit, ship's `findings.md` and `Sdlc-Findings`
trailers, the `Sdlc-Totals` on each `Close` (stops; the factory's tokens there are the
supervisor's alone, its agents' in `runs/costs.jsonl`), and the bugs with `Introduced by:` (the
escape rate O6 measures). After the 1.9.0 release.
Theme: review
Raised 2026-11-17.

## [2026-11-17-50] [bug] A board poll rebuilds every card, dropping keyboard focus

Found by the review of 099-board-page-fixes. The page's render key holds each change's
`touched_ago` in whole seconds (`scripts/board.py`, `round(now - touched)`), so it changes on every
2-second poll and `replaceChildren` rebuilds every card: a keyboard user Tabbed onto a card loses
focus to `body` before Enter can open it. `#board` is `aria-live="polite"`, so a screen reader is
handed the whole board again each poll. Rebuild only when what a person sees changes (the
rendered text, or `ago()`'s minute-level string), and move `aria-live` to the status line.

Severity: med
Paths: scripts/board.html, scripts/board.py
Theme: board

## [2026-11-17-51] [bug] A resolve refuses its own source as a conflict marker

`factory.py resolve --continue` (and `sdlc.py resolve`) refuse "conflict markers left in" any
conflicted file that holds the string `<<<<<<<` anywhere, and both scripts hold it in their own
marker check (`factory.py`'s and `sdlc.py`'s `if "<<<<<<<" in …`). So whenever `factory.py` or
`sdlc.py` is itself one of the conflicted files, the resolution is refused though nothing is left:
103's landing on 2026-11-17 stopped on it, and its rebase was finished by hand. Match a marker only
at the start of a line (`^<<<<<<< `, `^=======$`, `^>>>>>>> `).

Severity: med
Paths: plugins/factory/scripts/factory.py, scripts/sdlc.py
Theme: landing
