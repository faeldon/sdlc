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
Priority: low

## [2026-11-17-59] [idea] The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.

Left undone by 099-board-page-fixes, carried forward when it landed: The page's tests read its source; nothing runs the drawer's trap in a browser. A headless check would need a dependency the gate doesn't have.
See .sdlc/work/099-board-page-fixes/notes.md in its commit.
Raised 2026-11-17.

## [2026-11-18-41] [bug] factory.py reads [models] from the change's own worktree, not the base branch

factory.py reads [models] from the change's own worktree, while mode, [land], [ui] and gate_jobs
come from the base branch (`_base_factory()`): a change only gets a [models] setting committed on
main once its branch includes it, and a change can pick its own agents' models by editing its own
.sdlc/factory.toml. Seen 2026-11-18: builder = "claude-fable-5-1" committed on main (329748d) left
140's and 143's builders on Opus. [models] should be read from the base branch like the rest, or
the README should say it isn't.

Severity: low
Paths: plugins/factory/scripts/factory.py, plugins/factory/README.md
Theme: factory

## [2026-11-18-42] [bug] An agent's record can cite a change by its bare number and fail the gate

An agent's record can cite a change by its bare number and fail the gate: 140's behaviour check
ran `ls` on its own folder as a glob, `.sdlc/work/NNN*/…` with the number in place of NNN, and
filed it in its ## Evidence, which matches test_nothing_local's `work/\d{3,}\b(?!-)` rule; the
approver's decision and the code and test reviews then quoted the same glob while describing the
failure, so the record kept re-committing it (2026-11-18, 7 lines in 4 files fixed by hand). The
gate ran before the behaviour check wrote it, so only the reviewers' own suite runs saw it. When
factory.py files any agent's reply it should write a change's own folder glob or bare number
(`work/NNN*`, `work/NNN/`) as its full NNN-slug, as _placeholders() does for machine paths.

Severity: med
Paths: plugins/factory/scripts/factory.py
Theme: factory

## [2026-11-18-43] [idea] Move close, push, the lock and the landing into modules the deep review can name

Move close, push and the main lock out of scripts/sdlc.py, and the landing out of
plugins/factory/scripts/factory.py, into modules of their own (as retro.py and board.py are), each
loaded by path with its docstring as its contract, and list those modules in [review] sensitive.
Today the deep review matches paths, and those two files are touched by most changes (60 and 50
commits this month), so listing them would make nearly every run full depth; 139-landing-train
rewrote close's lock and the landing at light depth with no security review. Open it after the
139–147 batch and the release, so the move is made on quiet code.
Theme: factory
Raised 2026-11-18.

## [2026-11-18-44] [idea] Fold `factory.py resolve`'s base-branch rebase into `--onto <base>`

Left undone by 139-landing-train, carried forward when it landed: `factory.py resolve` without `--onto` still rebases onto the base branch: no skill runs it that way now (the land skill always stacks with `--onto`), and only the register-conflict tests in `tests/test_land.py` exercise it. Fold it into `--onto <base>` or drop it once those tests are rewritten over a train.
See .sdlc/work/139-landing-train/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-45] [idea] Stage the landing agent's reply and `land-resolved` with `RESOLVE_RECORDS`

Left undone by 139-landing-train, carried forward when it landed: After `resolve --continue`, the landing agent's reply (`build/land-<n>.md`) and the `runs/land-resolved` marker stay uncommitted until the close amends them, as before the train; staging them with the other mid-rebase records (`RESOLVE_RECORDS`) would leave the tree clean after every stack.
See .sdlc/work/139-landing-train/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-46] [idea] One shared test helper that drives a landing train

Left undone by 139-landing-train, carried forward when it landed: `tests/test_train.py`'s `_drive()` and `tests/test_land.py`'s `_land_train()` both drive a train as the skill does; one helper in a shared test module would do.
See .sdlc/work/139-landing-train/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-53] [idea] Reflow AGENTS.md's remaining lines past 100 columns

Left undone by 142-pay-down-todays-nits, carried forward when it landed: `AGENTS.md` has other lines past 100 columns (12, 29, 34, the *Writes before a WAIT* paragraph at 109-110, 223, 232-233, 238, 255, 276, 314), outside 2026-11-18-25's scope.
See .sdlc/work/142-pay-down-todays-nits/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-54] [idea] Replace the "111 C1" review label in test_a_server_that_fails_on_its_own_is_started_once with the rule it pins

Left undone by 142-pay-down-todays-nits, carried forward when it landed: `tests/test_factory.py`'s `test_a_server_that_fails_on_its_own_is_started_once` docstring cites "111 C1", another review-only label no reader can resolve.
See .sdlc/work/142-pay-down-todays-nits/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-55] [idea] Wrap the supersedes sentence in reviewer-code.md and reviewer-ux.md

Left undone by 142-pay-down-todays-nits, carried forward when it landed: `plugins/factory/agents/reviewer-code.md:94` and `reviewer-ux.md:67`, the `supersedes` sentence, are single long lines.
See .sdlc/work/142-pay-down-todays-nits/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-56] [nit] the new "unverified" case asserts only `stuck == []`.

Raised by the code review of 142-pay-down-todays-nits, round 1: tests/test_factory.py:1676: the new "unverified" case asserts only `stuck == []`. Also asserting `next == "rework"` would pin the full outcome, as the neighbouring cases do.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 142-pay-down-todays-nits (correctness)

## [2026-11-18-57] [idea] Tell a hand-built change how to take screenshots for ship's UI review

Left undone by 143-ship-review-parity, carried forward when it landed: Say in `ui.md`, or in `passes.ui.why` when `sdlc-factory` is enabled, how a hand-built change takes its screenshots (`factory.py shots`), once the person decides whether ship should point at a command that starts a dev server.
See .sdlc/work/143-ship-review-parity/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-58] [nit] the line says "whose own behaviour reviewer ran" and security.md and ui.md say the same of their factory reviewers.

Raised by the code review of 143-ship-review-parity, round 1: skills/ship/behaviour.md:3: the line says "whose own behaviour reviewer ran" and security.md and ui.md say the same of their factory reviewers. Only the factory case is meant, so "a factory run, whose own reviewers ran" would match `_passes_report()`'s wording.

Theme: docs
Paths: skills/ship/behaviour.md
Cost: S
Value: low
Raised by: 143-ship-review-parity (correctness)

## [2026-11-18-59] [nit] it says the pass applies when the diff touches a `review.sensitive` path.

Raised by the code review of 143-ship-review-parity, round 1: skills/ship/security.md:3: it says the pass applies when the diff touches a `review.sensitive` path. The script keys on `risk.deep`, so the sentence is only as exact as `deep` is. Say "a deep diff" to follow R2.

Theme: docs
Paths: skills/ship/security.md
Cost: S
Value: low
Raised by: 143-ship-review-parity (correctness)

## [2026-11-18-47] [idea] Reword `_no_verdict()` and `NO_DECISION` now that an answer after prose is read

Left undone by 140-agent-replies-that-file-right, carried forward when it landed: `_no_verdict()` and `NO_DECISION` still say "doesn't open with VERDICT…/DECISION…", which the spec kept so the board's and status's problem text doesn't move. Since `opening()` now reads an answer after prose, the words now mean "holds no answer the script reads". A rewording would change the board's and status's text together, and their pins with it.
See .sdlc/work/140-agent-replies-that-file-right/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-48] [nit] `replies[-1]` is a safe fallback only because `_claude()` guarantees a non-empty list when it returns no problem.

Raised by the code review of 140-agent-replies-that-file-right, round 1: plugins/factory/scripts/factory.py:3840: `replies[-1]` is a safe fallback only because `_claude()` guarantees a non-empty list when it returns no problem. A one-line comment saying so would help.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 140-agent-replies-that-file-right (correctness)

## [2026-11-18-49] [idea] Board says "builder is resolving a conflict" on a factory landing mid-rebase

Left undone by 141-board-landing-track-truth, carried forward when it landed: A shipped change whose landing rebase is stopped shows the hand-run `sdlc.py resolve` line as its next step while the factory's builder is resolving the conflict (`next_action()` puts `rebasing` first): a landing-aware line ("its builder is resolving a conflict: wait for it") would be truer. Left for a change of its own, since `PRECEDENCE` and `BOTH` pin the order.
See .sdlc/work/141-board-landing-track-truth/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-50] [idea] Landing track shows post-rebase `accept` as its own step after the gate

Left undone by 141-board-landing-track-truth, carried forward when it landed: `factory.py accept` run after a rebase (inside a landing round) records no step: the track stays at `gate`, which it runs beside. A `checks` position after the gate would need the record to say where it sits.
See .sdlc/work/141-board-landing-track-truth/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-51] [nit] `stop_text` types `stuck` and `untestable` as `list[str] = ()`.

Raised by the code review of 141-board-landing-track-truth, round 1: plugins/factory/scripts/factory.py:1956: `stop_text` types `stuck` and `untestable` as `list[str] = ()`. The annotation says list while the default is a tuple. `list[str] | tuple = ()` or `None` would match what callers pass.

Theme: style
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 141-board-landing-track-truth (correctness)

## [2026-11-18-52] [nit] `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand.

Raised by the code review of 141-board-landing-track-truth, round 1: scripts/sdlc.py:9986: `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand. A test pins the resulting output, so this is fine. If `needs_of` later reads more fields at `shipped`, this site is easy to miss.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 141-board-landing-track-truth (correctness)

## [2026-11-18-60] [idea] Status groups its sections by the board's columns

status groups its sections by the board's columns (Planned, Designing, Building, Ready, Landing,
Needs you), so the board and status use one vocabulary. Raised by 145-escalations-that-clear,
whose spec left status as it is: it reshapes status's output for every host, a change of its own.
Theme: board
Raised 2026-11-18.
