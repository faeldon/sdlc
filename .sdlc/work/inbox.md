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

## [2026-11-17-28] [idea] CONTRIBUTING's Writing a tracker lists the intake methods

AGENTS.md points at CONTRIBUTING.md's *Writing a tracker* for the tracker interface, which leaves
out the intake methods core calls when a tracker has them: `mark()`, `unmark()`, `needs_info()`,
`open_marks()`, `open_numbers()`, `closed_by()`. See .sdlc/work/090-agents-rules-once/notes.md in
090's commit.
Theme: docs
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

## [2026-11-17-51] [bug] A resolve refuses its own source as a conflict marker

`factory.py resolve --continue` (and `sdlc.py resolve`) refuse "conflict markers left in" any
conflicted file that holds a run of seven less-than signs anywhere, and both scripts hold one in
their own marker check. So whenever `factory.py` or `sdlc.py` is itself one of the conflicted files,
the resolution is refused though nothing is left: 103's landing on 2026-11-17 stopped on it, and its
rebase was finished by hand. Any text quoting that run does the same, this entry's first wording
included, which stopped 098's landing on `.sdlc/work/inbox.md`. Match a marker only as a whole line
start: seven less-than signs and a space, seven equals signs alone, or seven greater-than signs and
a space.

Severity: med
Paths: plugins/factory/scripts/factory.py, scripts/sdlc.py
Theme: landing

## [2026-11-17-52] [idea] pre-existing: scripts/board.html: the `.col-head` row lets the "who" subtitle wrap beside the heading, so the Test column's "the gate and the review" sits indented under a one-line title and looks misaligned at 1280px. Filed for later.

Left undone by 098-board-fixes, carried forward when it landed: pre-existing: scripts/board.html: the `.col-head` row lets the "who" subtitle wrap beside the heading, so the Test column's "the gate and the review" sits indented under a one-line title and looks misaligned at 1280px. Filed for later.
See .sdlc/work/098-board-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-56] [idea] pre-existing: an empty column (DESIGN, TEST, READY TO SHIP, READY TO CLOSE in the screenshots) shows a bare "—". It does not say the column is empty or that nothing is waiting there.

Left undone by 098-board-fixes, carried forward when it landed: pre-existing: an empty column (DESIGN, TEST, READY TO SHIP, READY TO CLOSE in the screenshots) shows a bare "—". It does not say the column is empty or that nothing is waiting there.
See .sdlc/work/098-board-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-57] [idea] code (round 2 note): a card with a problem and a pending decision at `build` names only "fix what its problems name", by the precedence in `plan.md`; it no longer says a decision is waiting too. The card's other lines still show `pending`; whether its next step should name both is for ship.

Left undone by 098-board-fixes, carried forward when it landed: code (round 2 note): a card with a problem and a pending decision at `build` names only "fix what its problems name", by the precedence in `plan.md`; it no longer says a decision is waiting too. The card's other lines still show `pending`; whether its next step should name both is for ship.
See .sdlc/work/098-board-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-58] [idea] code (round 2 note): the rebasing card's `--abort` wording doesn't say `resolve --abort` keeps the resolved work under `refs/sdlc/end/<branch>`.

Left undone by 098-board-fixes, carried forward when it landed: code (round 2 note): the rebasing card's `--abort` wording doesn't say `resolve --abort` keeps the resolved work under `refs/sdlc/end/<branch>`.
See .sdlc/work/098-board-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-59] [idea] The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.

Left undone by 099-board-page-fixes, carried forward when it landed: The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.
See .sdlc/work/099-board-page-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-63] [idea] The hand gate shares the factory's gate_jobs slots

Left undone by 101-factory-start-fresh, carried forward when it landed: `sdlc.py gate` (the hand gate) takes no `gate_jobs` slot, by 101's spec's boundary: sharing the slots would make the lock files' names a contract between sdlc and sdlc-factory.
See .sdlc/work/101-factory-start-fresh/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-64] [idea] /sdlc-factory:spec shows how far behind the change is and brings it up to date

Left undone by 101-factory-start-fresh, carried forward when it landed: `/sdlc-factory:spec` gets `start`'s new `base` and `behind` keys but doesn't show them, and doesn't run `fresh`, so a spec can be drafted on a stale branch.
See .sdlc/work/101-factory-start-fresh/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-65] [idea] Six `#` comments in `scripts/sdlc.py` still call the change folder `work/` (above `ENTRY_RE`, `OPEN_ITEM_RE`, `DOC_TEMPLATES`, `LAST_ID`, `config`'s `"work"` key, and the trackers section). They aren't docstrings, so they're outside this change's scope.

Left undone by 102-sdlc-docstrings, carried forward when it landed: Six `#` comments in `scripts/sdlc.py` still call the change folder `work/` (above `ENTRY_RE`, `OPEN_ITEM_RE`, `DOC_TEMPLATES`, `LAST_ID`, `config`'s `"work"` key, and the trackers section). They aren't docstrings, so they're outside this change's scope.
See .sdlc/work/102-sdlc-docstrings/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-66] [idea] /sdlc:idea --themes skips seeds an open change names

`/sdlc:idea --themes` leaves out entries tagged `[building]` but not those an open change's
`idea:` names, so it may propose a `Theme:` for a seed being built: harmless (an update, which
`inbox-commit` allows), but it could read `status`'s `building` list to match. See
.sdlc/work/100-seeds-marked-by-changes/notes.md in its commit.
Theme: inbox
Raised 2026-11-17.

## [2026-11-17-67] [idea] The build skill's summary of `start`'s `ui` (`serve`, `shoot`, `paths`) doesn't name `fixture`; the README does.

Left undone by 106-factory-reviewer-coverage, carried forward when it landed: The build skill's summary of `start`'s `ui` (`serve`, `shoot`, `paths`) doesn't name `fixture`; the README does.
See .sdlc/work/106-factory-reviewer-coverage/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-68] [idea] `tests/test_board.py::test_the_board_fixture_shows_every_card_state` takes about 30s on a cold `uv` cache (two `sdlc.py gate` runs); a `--no-gate` path in `build.sh` isn't worth it yet.

Left undone by 106-factory-reviewer-coverage, carried forward when it landed: `tests/test_board.py::test_the_board_fixture_shows_every_card_state` takes about 30s on a cold `uv` cache (two `sdlc.py gate` runs); a `--no-gate` path in `build.sh` isn't worth it yet.
See .sdlc/work/106-factory-reviewer-coverage/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-69] [idea] Make the board and status read an unreadable stop record the same way

Left undone by 107-board-needs-you, carried forward when it landed: A stop record that won't read reads differently in the two places: the board makes it a problem (`fix: runs/stopped.md doesn't open …`, card `stopped: None`, as 086 pinned), while `status`'s `factory_stop()` keeps it a stop (`stopped: read runs/stopped.md`). Both put it in front of the person; aligning them means changing one of the two pinned behaviours.
See .sdlc/work/107-board-needs-you/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-70] [idea] Make the board's next step follow what the change needs

Left undone by 107-board-needs-you, carried forward when it landed: `next_action()` is unchanged, as the spec says: an escalation that still needs `decide D2` names `/sdlc:ship, or /sdlc-factory:land …` as its next step, beside its `needs you:` line. A next step that follows the needs would read better.
See .sdlc/work/107-board-needs-you/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-71] [bug] The landing's behaviour check leaves an exit off its evidence and stops a passing change

The landing's behaviour check (`agent --task land-review --role behaviour`) kept writing a command
into its `## Evidence` without an `exit:` line, mostly a trivial read (`head -5 …`, `sdlc.py
status`), so `land-verdicts` stopped four landings on 2026-11-17 (103, 098, 104, 107) whose
verdicts were all `PASS`; each was closed by hand. One also put its `VERDICT:` on line 7 after a
self-correction (105). The landing has no mend for either: its prompt or the evidence check
should make a missing exit on a read-only command mendable, or not a stop.

Severity: med
Paths: plugins/factory/scripts/factory.py, plugins/factory/agents/reviewer-behaviour.md
Theme: landing

## [2026-11-17-72] [bug] A mend during a landing writes into the build round

`factory.py agent <NNN> --task mend --role behaviour`, run on a landing's stop, wrote its reply to
`reviews/round-1/behaviour.md`, the change's build round, which had no behaviour review, instead of
`reviews/land-<n>/behaviour.md`; the landing stayed stopped and the build round gained a review it
never ran (103 on 2026-11-17, set aside as `behaviour.misfiled.md`). A mend should target the
landing round when a landing is open, or refuse.

Severity: med
Paths: plugins/factory/scripts/factory.py
Theme: landing

## [2026-11-17-73] [bug] A landing's failed commit drops git's own error

`cmd_land()` reports `the commit failed: Command … returned non-zero exit status 128` and drops
the `CalledProcessError`'s `stderr`, so why git refused can't be seen (098 on 2026-11-17; a
dry run with the same message passed, and a retry by hand committed). The refusal should carry
git's message.

Severity: low
Paths: plugins/factory/scripts/factory.py
Theme: landing

## [2026-11-17-74] [bug] A landing that fails between ship and its commit can't be resumed

When `land`'s commit fails after `sdlc.py ship` stamped the change shipped and staged it, a rerun of
`land` reads `stage: shipped` as landed before and tries to amend a commit that doesn't exist (098
on 2026-11-17, committed by hand with the landing's composed message). A rerun should see no
landing commit (`Sdlc-Landed:` on `HEAD`) and make the commit.

Severity: med
Paths: plugins/factory/scripts/factory.py
Theme: landing

## [2026-11-17-75] [bug] The intent cases' judgment grader reads only the last message

The `intent` and `intent-product` cases' `judgment` grader judges the run's last message. When the
model asks its WAIT as plain text in a message of its own (no `AskUserQuestion` in the case), the
judge never sees the draft and the tier before it and votes FAIL: 096's and 100's ships on
2026-11-17 each failed one case, a different one each run, and passed it on a rerun. The grader
should read the whole reply, or the case end on one message.

Severity: med
Paths: evals/intent/graders/judgment.md, evals/intent-product
Theme: tests

## [2026-11-17-76] [idea] Promote a change to Tier 2 in the middle of a factory run

097 was promoted from Tier 1 to Tier 2 at its builder's blocking decision on 2026-11-17, but at
`stage: build` neither `/sdlc-factory:spec` nor the build skill drafts a spec (both start from
`plan` or `design`), and the builder rightly won't write one; the supervisor moved the stage back
to `plan` by hand. A promotion should have a path: `factory.py` sets `tier: 2`, keeps the build,
and drafts the spec behind its own question.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-77] [idea] Mend an approver's or verifier's answer written after a preamble

A run mends a builder's missing evidence and a reviewer's verdict after a preamble, but not an
approver's decision or a verifier's answers that open with a preamble or in another shape (099's
verifier wrote `- **KEPT:**`; 099's and 107's approvers wrote a line before `DECISION:` on
2026-11-17). Each was set aside by hand and the agent rerun. The mend could cover those roles too.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-78] [bug] The landing carries only a note's first line, and takes its text as the seed's title

When a landing carries an undone `notes.md` item as a seed (103's `_dispose()`), it reads only the
item's first line, so a note that wraps is cut mid-sentence ("…by the spec's boundary: sharing",
"…doesn't show them, and": 2026-11-17-63 and -64, retitled by hand). With no `- UNDONE:` line
from the approver, it also uses the note's whole text as the seed's title (52–59, 65). It should
read the item's continuation lines, and title a seed with no proposal from its first sentence.

Severity: low
Paths: plugins/factory/scripts/factory.py
Theme: landing
