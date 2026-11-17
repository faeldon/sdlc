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

## [2026-11-17-59] [idea] The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.

Left undone by 099-board-page-fixes, carried forward when it landed: The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.
See .sdlc/work/099-board-page-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-63] [idea] The hand gate shares the factory's gate_jobs slots

Left undone by 101-factory-start-fresh, carried forward when it landed: `sdlc.py gate` (the hand gate) takes no `gate_jobs` slot, by 101's spec's boundary: sharing the slots would make the lock files' names a contract between sdlc and sdlc-factory.
See .sdlc/work/101-factory-start-fresh/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-76] [idea] Promote a change to Tier 2 in the middle of a factory run

097 was promoted from Tier 1 to Tier 2 at its builder's blocking decision on 2026-11-17, but at
`stage: build` neither `/sdlc-factory:spec` nor the build skill drafts a spec (both start from
`plan` or `design`), and the builder rightly won't write one; the supervisor moved the stage back
to `plan` by hand. A promotion should have a path: `factory.py` sets `tier: 2`, keeps the build,
and drafts the spec behind its own question.
Theme: factory
Raised 2026-11-17.

## [2026-11-17-81] [idea] Wrap long tokens in a card's next step

Left undone by 110-board-says-it-plainly, carried forward when it landed: pre-existing: `scripts/board.html:82`: `.next code` has no `overflow-wrap`, so a long unbroken token in a next step could push past a narrow card. None appears in these shots, so this is for later, not a change.
See .sdlc/work/110-board-says-it-plainly/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-82] [idea] Shorten the factory's stop NEXT: wording for phone-width cards

Left undone by 110-board-says-it-plainly, carried forward when it landed: pre-existing: `scripts/board.html:292`: a stop's `next:` is a long run-on command in monospace (006's "rerun /sdlc-factory:build 006, whose one mend asks again…"), and it wraps badly at 390px. The text comes from the factory's stop record, which this change doesn't touch.
See .sdlc/work/110-board-says-it-plainly/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-83] [idea] Parenthesise the stop test in board.py's _progress()

Left undone by 110-board-says-it-plainly, carried forward when it landed: pre-existing: scripts/board.py:393: `if entry.get("stopped") or (folder / STOPPED).is_file() and entry["stage"] == "build":` mixes `or` and `and` with no parentheses. The `and` binds first, so it reads as intended, but it is easy to misread. This line is in `_progress()`, which this change doesn't touch. Parenthesise it when someone next edits `_progress()`.
See .sdlc/work/110-board-says-it-plainly/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-84] [idea] Say "stopped: mend" in plain words on the needs-you line

Left undone by 110-board-says-it-plainly, carried forward when it landed: pre-existing: scripts/sdlc.py:4108: a stop waiting on the person reads `needs you: stopped: mend`, and `mend` is the factory's word for a re-run of the reviewer, not something a person knows. The card's `next:` line spells out the step, so the person can still act, but the label is not plain.
See .sdlc/work/110-board-says-it-plainly/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-85] [bug] The factory's ui and ux reviewers can't run at once

Each of the two reviewers starts the board's dev server through `tests/fixtures/board/serve.sh`,
which builds the fixture into the same `.sdlc/reports/shots/<change>/round-<n>/fixture` folder.
So when both start together, as the build skill says to start a round's reviewers, the second is
refused before it judges anything: "build.sh: …/fixture/drafts already exists; it builds only a
new repo". Each should get a fixture of its own, or the two should share one built once. Seen on
110-board-says-it-plainly round 1, 2026-11-17; the supervisor reran ux alone after ui finished.

Severity: med
Paths: plugins/factory/scripts/factory.py, tests/fixtures/board/serve.sh, tests/fixtures/board/build.sh
Introduced by: 106-factory-reviewer-coverage
Theme: factory

## [2026-11-17-86] [bug] A landing review reads the base branch's newer commits as the change's deletions

A landing review compares a rebased change against the base branch as it is now, not against the
commit the change was rebased onto, so a commit that reaches the base branch during the landing
reads as something the change deleted. On 2026-11-17, 110-board-says-it-plainly's landing round 1
was rebased onto 09a8622; bug 2026-11-17-85 was then filed on main (e7e2f1a); the landing's code
reviewer reported that the branch "drops" 85 from .sdlc/work/inbox.md, the verifier kept it, and
land-verdicts stopped the landing ("the landing review kept 1 change(s): ship it by hand"). The
branch never held 85. Landing again rebased it and opened round 2. The landing review should read
the diff from the rebase's base (the merge base, or the head the round's gate recorded).

Severity: med
Paths: plugins/factory/scripts/factory.py, plugins/factory/agents/reviewer-code.md
Theme: factory

## [2026-11-17-87] [idea] Retro proposes a pruning pass over the test suite

Left undone by 118-retro-spend-indicators, carried forward when it landed: R11, at ship: file the suite-pruning pass as a seed through `/sdlc:idea` (`inbox-commit`, on the base branch, never this branch), carrying 2026-11-12-2's third bullet: nothing looks at the tests already in the suite again (one whose code was rewritten, one a newer test repeats, one that passes for the wrong reason, the slowest). Needs per-test run times and a test-to-code map no host records today (spec, *Alternatives rejected*).
See .sdlc/work/118-retro-spend-indicators/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-88] [idea] Share one -U0 diff per change between retro's rework and spend

Left undone by 118-retro-spend-indicators, carried forward when it landed: `retro()` and `retro_report()` each call `_change_rows()` per change, and `_spend()` now adds one `git diff -U0` per change on top; `_rework()` runs the same `-U0` diff. One diff per change shared between `_rework()` and `_spend()` would halve those calls. Not this change.
See .sdlc/work/118-retro-spend-indicators/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-89] [idea] Unmark withdrawn issues in the full marking pass, using closed_by() on the unpushed commits

Left undone by 116-register-and-docs, carried forward when it landed: A full marking pass (close, `mark-triaged`) still leaves a core-marked issue whose record went (an entry's `Issue:` line removed by hand) as `dangling` for triage, not unmarked: close's pass runs between its Close commit and the push that closes the change's issues, so it would need `closed_by()` on the unpushed commits to tell a just-fixed issue from a withdrawn one.
See .sdlc/work/116-register-and-docs/notes.md in its commit.
Raised 2026-11-17.
