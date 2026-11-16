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

## [2026-11-04-10] [idea] Move retro's history readers out of sdlc.py

`scripts/sdlc.py` is 7,729 lines, up from 7,047 at the last retrospective, and 12 of the window's 14
changes touched it; that retrospective proposed splitting it as an intent nobody opened. Its retro
section alone runs about 1,400 lines, read-only and called only by `retro` and `retro-commit`. Move
it to `scripts/retro.py`, loaded by path like `metrics.py`, leaving the history walks it shares with
release (`closed_changes()`, `_change_base()`) in `sdlc.py`; the spec decides how they reach it.
One boundary first, not a rewrite. Raised by the retrospective of 2026-11-04.
Theme: refactor
Priority: high

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


## [2026-11-17-1] [idea] Intent shows what a change serves in its draft, rather than asking first

Every one of the 27 changes closed since 2026-11-04 asked at least one question at intent beyond
its gate, 33 in all. Most were the product-doc questions: which outcomes the change serves, and
what each should move. As a result, the median Tier 2 change stops 8 times against O3's target of
6, and the median Tier 1 change 6 against 5. Steps 1 and 3 of `skills/intent/SKILL.md` would
instead draft the `serves:` line and the `**Moves O1:**` lines from the seed and the product doc,
and show them in the draft, marked as proposed. The WAIT's "edit a section" answer is how the
person changes them, so the yes stays their decision. The change touches a WAIT, so it is Tier 2,
and it rewords the skill's "never pick for the human". Raised by the retrospective of 2026-11-17.
Theme: intent
Priority: high

## [2026-11-17-2] [idea] Two failure classes for the review doc, from the window's escapes

Three bugs escaped from changes in the window, against none in the 14 before it (rate 0.11
against 0.0, trend up):
- 2026-11-12-3 from 015;
- 2026-11-12-4 from 047, whose review had F1 on the bug's paths and answered it `minor`;
- 2026-11-12-5 from 050, a Tier 1 change whose review had no finding on its paths.

Two more bugs were tied to no change. The escapes, and the Important findings of 049, 052 and 055,
all sit in how `scripts/metrics.py` reads transcripts. 041's and 059's Important findings share a
second class.

Add both to `.sdlc/REVIEW.md`'s "The ways this repo's code fails":

- **A transcript's shape assumed, not read.** An event `scripts/metrics.py` counts from what a
  spec says the harness writes, not from a recorded transcript: a request counted where its outcome
  decides, a wait taken from agent time the turn never held, two kinds of reply read as one. A
  change to how an event is read carries a test built from a real transcript's entries.
- **A path compared as text between two sources that write it differently.** `str()` of a `Path`
  against git's POSIX output, or git's quoted path against its `-z` output. Normalise both sides
  first.

Raised by the retrospective of 2026-11-17.
Theme: review

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

## [2026-11-17-5] [idea] A supervisor agent that runs a factory change and calls the person only when needed

The factory's agents (builder, reviewers, verifier) are each started by a skill the person runs,
so every handoff is a stop. A supervisor agent would take one approved intent through build,
review and verification:
- it hands each part to the right agent and reads their reports;
- it settles what the plugin's rules and the risk signals let it settle;
- it calls the person only for a gate, a blocking decision in `decisions.md` or an ESCALATE.

Its first run is in a pilot project, the plugin's first host besides this repo, and that change's
`Close` numbers are set beside this repo's manual medians (O6).

The spec decides:
- whether the supervisor is an agent in `plugins/factory/agents/` or a skill;
- how it keeps no Write of its own, so nothing that judges also edits;
- how its calls to the person are recorded as stops.

Gates that pass themselves (2026-11-10-1) come after it. Raised by the retrospective of 2026-11-17.
Theme: factory
Priority: high
