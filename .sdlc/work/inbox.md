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

## [2026-11-18-48] [nit] `replies[-1]` is a safe fallback only because `_claude()` guarantees a non-empty list when it returns no problem.

Raised by the code review of 140-agent-replies-that-file-right, round 1: plugins/factory/scripts/factory.py:3840: `replies[-1]` is a safe fallback only because `_claude()` guarantees a non-empty list when it returns no problem. A one-line comment saying so would help.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 140-agent-replies-that-file-right (correctness)

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

## [2026-11-18-62] [nit] `work/<008>*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`.

Raised by the code review of 144-factory-records-and-models, round 1: plugins/factory/scripts/factory.py:2822: `work/<008>*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`. The shape is unrealistic, but `(?![\w-])` after an optional `\*?` could be made possessive or tightened

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 144-factory-records-and-models (correctness)

## [2026-11-18-63] [nit] the re-wrapped paragraph leaves one over-long line (`serve`, `shoot` and `paths` …)

Raised by the code review of 144-factory-records-and-models, round 1: plugins/factory/README.md:383: the re-wrapped paragraph leaves one over-long line (`serve`, `shoot` and `paths` …)

Theme: docs
Paths: plugins/factory/README.md
Cost: S
Value: low
Raised by: 144-factory-records-and-models (correctness)

## [2026-11-18-72] [nit] A record quoting a term from .sdlc/terms.local is still filed as written

DEFUSE covers the scan's PATTERNS only; the scan also refuses each regex in the main checkout's gitignored terms file, so a reply quoting one still reaches a landing's gate as written.
Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: M
Value: low
Raised by: 144-factory-records-and-models (correctness)

## [2026-11-18-64] [nit] `bg` only looks for a trailing `&` at the end of the whole command.

Raised by the code review of 146-measure-how-agents-work, round 1: scripts/metrics.py:306: `bg` only looks for a trailing `&` at the end of the whole command. A multi-line command that backgrounds a middle line, such as `a &\nb`, isn't counted. The spec calls every count a lower bound, so this is allowed. Saying so in the docstring or adding a test would settle it.

Theme: tests
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 146-measure-how-agents-work (correctness)

## [2026-11-18-65] [nit] the `uvx`/`npx` branch builds the program list with `[...][:1] + words[2:]`, and that is only correct when the program is the first non-flag word.

Raised by the code review of 146-measure-how-agents-work, round 1: scripts/metrics.py:261: the `uvx`/`npx` branch builds the program list with `[...][:1] + words[2:]`, and that is only correct when the program is the first non-flag word. A short comment would help the next reader.

Theme: style
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 146-measure-how-agents-work (correctness)

## [2026-11-18-66] [idea] The board shows an unattended landing from the run lock

Left undone by 147-landing-runs-unattended, carried forward when it landed: The board could read the run lock (`sdlc-factory-train-run.lock`) to say a landing is running unattended, rather than inferring it from `runs/land-step.md` alone; the spec left the board unchanged.
See .sdlc/work/147-landing-runs-unattended/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-67] [idea] A Windows test for a killed train run

Left undone by 147-landing-runs-unattended, carried forward when it landed: `test_a_killed_train_run_resumes` kills a process group, so it doesn't run on Windows; a Windows kill test would need `CREATE_NEW_PROCESS_GROUP` and `taskkill /T`.
See .sdlc/work/147-landing-runs-unattended/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-68] [nit] `RUN_STEPS["eject"]` is looked up, but `RUN_EJECTS` and the cause check already guard it.

Raised by the code review of 147-landing-runs-unattended, round 1: plugins/factory/scripts/factory.py:6291: `RUN_STEPS["eject"]` is looked up, but `RUN_EJECTS` and the cause check already guard it. The `RUN_STOPS` tuple (line 6163) looks unused; remove it or use it for the `accept` and `stop` branches.

Theme: refactor
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 147-landing-runs-unattended (correctness)

## [2026-11-18-69] [nit] after a SIGKILL of the loop, an orphaned agent subprocess can still be running when a rerun starts, because the lock descriptor isn't inherited.

Raised by the code review of 147-landing-runs-unattended, round 1: plugins/factory/scripts/factory.py:6330: after a SIGKILL of the loop, an orphaned agent subprocess can still be running when a rerun starts, because the lock descriptor isn't inherited. The only guard is that the same step named twice stops the loop. A comment saying so, or a test, would help.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: M
Value: low
Raised by: 147-landing-runs-unattended (correctness)

## [2026-11-18-70] [nit] R4's stops for a non-zero step exit, an agent `problem`, `resolve` with no conflicted files and a `land.moves` stop have no test of their own.

Raised by the test review of 147-landing-runs-unattended, round 1: tests/test_train.py: R4's stops for a non-zero step exit, an agent `problem`, `resolve` with no conflicted files and a `land.moves` stop have no test of their own. The spec lists four R4 tests and all four exist, so the gap is only in what R4's list promises.

Theme: tests
Paths: tests/test_train.py
Cost: M
Value: low
Raised by: 147-landing-runs-unattended (correctness)

## [2026-11-18-71] [nit] the kill test waits up to 120 s (600 polls of 0.2 s) for the stand-in reviewer to start, which is slow on a loaded machine but not flaky.

Raised by the test review of 147-landing-runs-unattended, round 1: tests/test_train.py:1468: the kill test waits up to 120 s (600 polls of 0.2 s) for the stand-in reviewer to start, which is slow on a loaded machine but not flaky.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 147-landing-runs-unattended (correctness)

## [2026-11-18-73] [bug] resolve --continue misses non-ASCII conflicted paths

factory.py's _conflicted() and sdlc.py's _unmerged() list the conflicted files with
`git diff --name-only --diff-filter=U`, which quotes a path holding non-ASCII characters
("docs/caf\303\251.md"), so resolve --continue stages the quoted name, misses the real file, and the
rebase's continue refuses or the resolution leaves it out. They should read the list with -z (or
core.quotePath=false). To see it: stack a change that conflicts in a file with a non-ASCII name and
run resolve --continue. Not reproduced yet: found by reading the code (149's spec-writer).

Severity: low
Paths: plugins/factory/scripts/factory.py, scripts/sdlc.py
Theme: factory

## [2026-11-18-74] [idea] Limit CI's GITHUB_TOKEN to contents: read in check.yml

Left undone by 152-board-drawer-browser-test, carried forward when it landed: pre-existing: .github/workflows/check.yml:13: no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token
See .sdlc/work/152-board-drawer-browser-test/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-75] [nit] the header comment line now runs to 166 characters; the rest of the file wraps near 100.

Raised by the code review of 152-board-drawer-browser-test, round 1: .github/workflows/check.yml:3: the header comment line now runs to 166 characters; the rest of the file wraps near 100. Re-wrap it

Theme: style
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (correctness)

## [2026-11-18-76] [nit] the intent's open question on a skip note in `./check.sh`'s summary is not addressed.

Raised by the code review of 152-board-drawer-browser-test, round 1: tests/test_board_browser.py:75: the intent's open question on a skip note in `./check.sh`'s summary is not addressed. Recorded here as a possible follow-up; the gate record shows 28 skipped without saying why

Theme: docs
Paths: tests/test_board_browser.py
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (correctness)

## [2026-11-18-77] [nit] the rewrapped header comment runs past the file's line width

Raised by the security review of 152-board-drawer-browser-test, round 1: .github/workflows/check.yml:3: the rewrapped header comment runs past the file's line width

Theme: style
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (contract)

## [2026-11-18-78] [nit] the reflowed header comment leaves one line far over the file's roughly 100-column wrapping

Raised by the test review of 152-board-drawer-browser-test, round 1: .github/workflows/check.yml:3: the reflowed header comment leaves one line far over the file's roughly 100-column wrapping

Theme: style
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (correctness)

## [2026-11-18-79] [nit] the test takes about 49s here, mostly waiting on the poll interval.

Raised by the test review of 152-board-drawer-browser-test, round 1: tests/test_board_browser.py:98: the test takes about 49s here, mostly waiting on the poll interval. A shorter bounded wait or a faster poll in the fixture would speed up `./check.sh`

Theme: tests
Paths: tests/test_board_browser.py
Cost: M
Value: low
Raised by: 152-board-drawer-browser-test (correctness)
