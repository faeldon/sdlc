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

## [2026-11-13-1] [idea] Approve-path cases for the skill evals

053 landed the six stop-at-WAIT cases; the cases approved through a WAIT (its spec's R3, R5 and
R6: intent and ship continuing a stop case's transcript with `yes`) are left. The native
transcript is in a run kept with `run-cases --keep`, under its `config/projects/*/<session>.jsonl`,
and ends at the WAIT as needed, but it carries the machine's absolute paths (the plugin root in
every command), so it can't be committed or replayed elsewhere. The likely design: histories kept
out of git, captured per machine before a run, and approve cases skipped while theirs is missing.
See .sdlc/work/053-skill-evals/notes.md in 053's commit.
Theme: tests

## [2026-11-17-59] [idea] The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.

Left undone by 099-board-page-fixes, carried forward when it landed: The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.
See .sdlc/work/099-board-page-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-18-2] [idea] Ship's security pass at the factory's depth

Left undone by 114-one-review, carried forward when it shipped: gap: security: ship checks only secrets, plus the fresh reviewer on a sensitive path; it has no security pass at the depth of the factory's `reviewer-security`.
See .sdlc/work/114-one-review/notes.md in its commit.
Raised 2026-11-18.


## [2026-11-18-3] [idea] Ship runs the spec's path end to end

Left undone by 114-one-review, carried forward when it shipped: gap: end-to-end: ship never runs the spec's path end to end, as the factory's `reviewer-behaviour` does at landing.
See .sdlc/work/114-one-review/notes.md in its commit.
Raised 2026-11-18.


## [2026-11-18-4] [idea] Ship's UI review for changes that render a page

Left undone by 114-one-review, carried forward when it shipped: gap: ui: ship has no UI review of a change that renders a page, where the factory runs `reviewer-ui` when `[ui]` is set.
See .sdlc/work/114-one-review/notes.md in its commit.
Raised 2026-11-18.


## [2026-11-18-5] [idea] Ship's UX review when `[ui]` is set

Left undone by 114-one-review, carried forward when it shipped: gap: ux: ship has no UX review, where the factory runs `reviewer-ux` when `[ui]` is set.
See .sdlc/work/114-one-review/notes.md in its commit.
Raised 2026-11-18.


## [2026-11-18-11] [idea] findings.md template note names the landing as a writer

Left undone by 127-landing-rounds-in-findings, carried forward when it landed: `templates/findings.md`'s note (and its copy `FINDINGS_HEAD`) still says only "the factory's `carry` writes its agents' findings into it"; it could name the landing too. Left out: the note is pinned to the template, ships to hosts, and needs `sdlc.py record`.
See .sdlc/work/127-landing-rounds-in-findings/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-8] [idea] The board's drawer says a file is empty instead of showing a blank pane

Left undone by 124-board-renders-markdown, carried forward when it landed: ux: scripts/board.html:570: a `.md` file with no text (`doc.text` is `""`) draws a blank pane, because `??` keeps the empty string and the markdown branch renders an empty `div`. The drawer looks broken. Say the file is empty, for example "This file is empty." in the same note style as "This folder holds no file yet."
See .sdlc/work/124-board-renders-markdown/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-9] [bug] A slow fetch in the board's drawer can show an older file under a newer file's highlight

Found by the review of 124-board-renders-markdown.
pre-existing: scripts/board.html:573-585: `show()` assigns `doc` when its fetch resolves, whichever file was asked for last. If two files are clicked quickly and the older response arrives second, the pane shows the older file while the list highlights the newer one. Filed for later, not reworked here.

Severity: med
Paths: scripts/board.html

## [2026-11-18-10] [idea] The factory's spec gate asks a question worded by the script

Left undone by 125-build-gate-shows-the-change, carried forward when it landed: `/sdlc-factory:spec`'s WAIT still words its question in the skill (`Write this as .sdlc/work/NNN-<slug>/spec.md and advance the change to stage: design?`), but its only placeholder is the folder name, so there is nothing a model could get wrong in it; left out of this change, per the intent's scope.
See .sdlc/work/125-build-gate-shows-the-change/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-12] [idea] Triage's dangling bullet says an issue an unpushed commit closes waits on the push

Left undone by 128-unmark-withdrawn-issues, carried forward when it landed: `skills/triage/SKILL.md`'s `dangling` bullet offers every dangling issue for triage again, one an unpushed commit closes included: it could say that one waits on the push.
See .sdlc/work/128-unmark-withdrawn-issues/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-13] [idea] The approver weighs assumed defaults, and shows alternatives for the ones it escalates

The approver escalates for every assumed default, but confirming one offers no alternatives, so it's
hard to judge. Have the approver weigh the defaults itself and escalate only what it can't decide;
for those, show the default beside the alternatives that were considered, with pros and cons.
Theme: factory
Raised 2026-11-18.

## [2026-11-18-14] [idea] Factory rounds that are enough, and that stop early on a fault no round can fix

Build and landing rounds run out, and escalate or force a ship by hand: decide whether to raise the
round limits or the reviewer and rework models (124 and 125 stopped at landing on findings light
haiku rounds missed). Escalate early when every round fails on the same error, or on something that
can't be tested, instead of running more rounds.
Theme: factory
Raised 2026-11-18.

## [2026-11-18-15] [idea] A factory skill that walks the person through one change's open decisions

A factory skill (/sdlc-factory:decide, not "resolve", which already means rebase conflicts) that
walks the person through one change's open decisions and confirmations one at a time: the
background, the default, the alternatives and why the default was chosen, so escalations across
changes are decided quickly and with context.
Theme: factory
Raised 2026-11-18.

## [2026-11-18-16] [idea] A landing whose only conflict is the register skips the reviewers

A landing rebase whose only conflict is the register (.sdlc/work/inbox.md) still sends every
reviewer at the run's depth to read it; check mechanically that both sides' entries survived and
skip the reviewers.
Theme: landing
Raised 2026-11-18.

## [2026-11-18-17] [idea] Move a stopped landing's card to Needs you

Left undone by 133-board-tracks-landing, carried forward when it landed: A stopped landing shows on its card but keeps its column; moving it to Needs you would mean `sdlc.needs_of()` (shared with `status`) reading `runs/land-step.md`.
See .sdlc/work/133-board-tracks-landing/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-18] [idea] Record a landing step for factory.py accept

Left undone by 133-board-tracks-landing, carried forward when it landed: `factory.py accept` during a landing records no step: the track shows the gate's position until review starts.
See .sdlc/work/133-board-tracks-landing/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-19] [idea] A stopped landing at shipped names /sdlc:close by hand, not /sdlc:ship

Left undone by 133-board-tracks-landing, carried forward when it landed: ui: scripts/board.py:731: a landing that stopped at `close` on a card already at `shipped` reads `or /sdlc:ship 012 by hand`. That change is already committed, so `/sdlc:ship` is the wrong step. The by-hand way on for a shipped card is `/sdlc:close NNN`. Use `/sdlc:close` when the stage is in `CLOSED`, and `/sdlc:ship` otherwise. The stop at `close` is recorded in `factory.py:4515` after the ship commit, so this case is reachable. No screenshot shows a stopped landing, so this is from the code, not the image.
See .sdlc/work/133-board-tracks-landing/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-20] [idea] Plain words for every landing stop reason on the board

Left undone by 133-board-tracks-landing, carried forward when it landed: ux: the stop reasons are still raw git or tool text on the landing paths. They reach the card as `landing stopped: …` without plain words: factory.py:4449 (`git status couldn't be read`), :4453 (`uncommitted outside the change's folder: <paths>`), :4456 (`HEAD isn't the landing's commit, so its record has nothing to be amended into`), :4459, :4483 and :4486 (`landed by=auto, and …`, where `by=auto` is jargon), and the `_amend_record` text passed at :4362, :4498 and :4509. Give each a `plain` line that says what failed and what to do, as `SHIP_REFUSED` and the commit-failed line already do, and keep the raw words in the output.
See .sdlc/work/133-board-tracks-landing/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-21] [idea] A landing train: one integration of the batch, one gate, one conflict resolution

A landing train: /sdlc-factory:land stacks the batch on a landing branch in order, one landing
agent (opus, with every change's spec and diff) resolves conflicts once across the batch, the gate
runs once at the tip, failures are bisected to eject the change at fault, and main is
fast-forwarded with each change's own commit and Close commit kept on its first-parent line.
Evidence 2026-11-18: four landing conflicts, two moves, and 131 re-conflicting in factory.py
against 129 after a move. Weigh it at the retro once the register fix has landed and the remaining
conflicts are counted.
Theme: landing
Raised 2026-11-18.
