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

## [2026-11-17-87] [idea] Retro proposes a pruning pass over the test suite

Left undone by 118-retro-spend-indicators, carried forward when it landed: R11, at ship: file the suite-pruning pass as a seed through `/sdlc:idea` (`inbox-commit`, on the base branch, never this branch), carrying 2026-11-12-2's third bullet: nothing looks at the tests already in the suite again (one whose code was rewritten, one a newer test repeats, one that passes for the wrong reason, the slowest). Needs per-test run times and a test-to-code map no host records today (spec, *Alternatives rejected*).
See .sdlc/work/118-retro-spend-indicators/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-17-89] [idea] Unmark withdrawn issues in the full marking pass, using closed_by() on the unpushed commits

Left undone by 116-register-and-docs, carried forward when it landed: A full marking pass (close, `mark-triaged`) still leaves a core-marked issue whose record went (an entry's `Issue:` line removed by hand) as `dangling` for triage, not unmarked: close's pass runs between its Close commit and the push that closes the change's issues, so it would need `closed_by()` on the unpushed commits to tell a just-fixed issue from a withdrawn one.
See .sdlc/work/116-register-and-docs/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-18-1] [idea] `is_read()` refuses `file -C`, and git's `--ext-diff`/`--textconv`

Left undone by 123-evidence-reads, carried forward when it landed: `file` is on R1's plain-read list, but `file -C -m <magic>` compiles a magic file and writes `<magic>.mgc`. A later change could give `file` its own condition (no `-C`) the way `sort` has one; left as the spec lists it here.
See .sdlc/work/123-evidence-reads/notes.md in its commit.
Raised 2026-11-18.
