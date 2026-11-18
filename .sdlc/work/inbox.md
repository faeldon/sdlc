# Ideas

Seeds, not a backlog. `/sdlc:intent` promotes one into a change.

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
Priority: low

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
Priority: low
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
Theme: landing
Raised 2026-11-18.

## [2026-11-18-67] [idea] A Windows test for a killed train run

Left undone by 147-landing-runs-unattended, carried forward when it landed: `test_a_killed_train_run_resumes` kills a process group, so it doesn't run on Windows; a Windows kill test would need `CREATE_NEW_PROCESS_GROUP` and `taskkill /T`.
See .sdlc/work/147-landing-runs-unattended/notes.md in its commit.
Theme: tests
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

## [2026-11-18-74] [idea] Limit CI's GITHUB_TOKEN to contents: read in check.yml

Left undone by 152-board-drawer-browser-test, carried forward when it landed: pre-existing: .github/workflows/check.yml:13: no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token
See .sdlc/work/152-board-drawer-browser-test/notes.md in its commit.
Theme: ci
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

## [2026-11-18-80] [nit] `any((folder / "reviews" / f"land-{n}").iterdir())` raises if the round's folder is missing; `land_round` presumably only counts existing folders, so it is safe today.

Raised by the code review of 154-landing-fix-before-gate, round 1: plugins/factory/scripts/factory.py:5880: `any((folder / "reviews" / f"land-{n}").iterdir())` raises if the round's folder is missing; `land_round` presumably only counts existing folders, so it is safe today. Guarding with `.is_dir()` would make that explicit

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 154-landing-fix-before-gate (correctness)

## [2026-11-18-81] [idea] Wrap the reviewer agents' other lines past 100 columns

Left undone by 150-pay-down-batch-nits, carried forward when it shipped: `plugins/factory/agents/reviewer-code.md` and `reviewer-ux.md` keep other lines past 100 columns (each frontmatter `description`, and the "Under a decision's line" paragraph after the `supersedes` sentence -55 wrapped), outside -55's scope.
See .sdlc/work/150-pay-down-batch-nits/notes.md in its commit.
Theme: docs
Raised 2026-11-18.

## [2026-11-18-82] [idea] Rewrap the factory README's lines past 100 columns

Left undone by 150-pay-down-batch-nits, carried forward when it shipped: `plugins/factory/README.md` keeps about twenty other lines past 100 columns, outside -63's scope (the one paragraph it named).
See .sdlc/work/150-pay-down-batch-nits/notes.md in its commit.
Theme: docs
Raised 2026-11-18.

## [2026-11-18-83] [nit] the edited *The factory* paragraph now has a very long line, 4 lines down from the reflow.

Raised by the code review of 149-landing-resolver-agent, round 1: AGENTS.md:237: the edited *The factory* paragraph now has a very long line, 4 lines down from the reflow. Re-wrap it near the 100-column width the rest of the file keeps.

Theme: style
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 149-landing-resolver-agent (correctness)

## [2026-11-18-84] [nit] in `cmd_resolve --continue`, `_stray()` runs before the register is pruned, which is what the spec says.

Raised by the code review of 149-landing-resolver-agent, round 1: plugins/factory/scripts/factory.py:6966: in `cmd_resolve --continue`, `_stray()` runs before the register is pruned, which is what the spec says. If `.sdlc/last-id` is still modified in the worktree after `_rebase_settling()`, it would count as stray. Spec R9 says it is staged, and a test covers the clean path, so I'm only flagging it. A test where a conflicting stack also touches `last-id` would settle it.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 149-landing-resolver-agent (correctness)

## [2026-11-18-85] [nit] the fence test mixes tracked and untracked strays in one flow.

Raised by the test review of 149-landing-resolver-agent, round 1: tests/test_train.py:976: the fence test mixes tracked and untracked strays in one flow. A failure message won't say which case broke, so the `refused` helper could take a label

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 149-landing-resolver-agent (correctness)

## [2026-11-18-86] [nit] `a["ready"]` now adds `held_by_rebase(home)`.

Raised by the code review of 151-status-by-board-states, round 1: scripts/sdlc.py:10620: `a["ready"]` now adds `held_by_rebase(home)`. That function calls `_change_trees` and `worktrees`, which `rebasing_branches` also calls, so `status` walks the worktree list twice. It's cheap, but `held_by_rebase` could take the branches as an argument.

Theme: refactor
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 151-status-by-board-states (correctness)

## [2026-11-18-87] [nit] `_by_state` falls back to `BY_STAGE` for a record with no `column`, and silently drops a stage `column()` would place elsewhere, such as `test`.

Raised by the code review of 151-status-by-board-states, round 1: scripts/sdlc.py:10010: `_by_state` falls back to `BY_STAGE` for a record with no `column`, and silently drops a stage `column()` would place elsewhere, such as `test`. Nothing reads such a record today.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 151-status-by-board-states (correctness)

## [2026-11-18-88] [idea] Pay down the tests nits in one change

Five `[nit]` entries are open under `tests` (2026-11-18-64, -70, -71, -79 and -85), which is the threshold the process guide sets for paying a theme down. Two of them are slow polls in the train's kill test (-71 and -79, about 49 seconds here). One change takes all five, and its review decides each.
Theme: tests
Raised by the retrospective of 2026-11-18.

## [2026-11-18-89] [idea] Pay down the style nits in one change

Five `[nit]` entries are open under `style` (2026-11-18-65, -75, -77, -78 and -83), which is the threshold. Four are lines past the 100-column wrap, the same work as ideas 2026-11-18-81 and -82. One change takes the five nits, and the two ideas with them if they are still open.
Theme: style
Raised by the retrospective of 2026-11-18.

## [2026-11-18-90] [idea] A pruning pass over the tests that drifted

Retro's `tests.drifted` names ten test files whose code moved without them over the last 30 changes:
- the board fixture `012-draft-publish` (seven files), last touched by 133, while `factory.py`, `board.py` and `board.html` changed in 17 later changes;
- `tests/test_config_resolution.py` and `tests/test_indicators.py`, last touched by 130, with 17 later changes;
- `tests/test_adoption.py`, last touched by 134, with 16 later changes.

A later change looks at each one again (merge, rewrite, move or delete it), and its review decides. There are no run times to weigh, because `retro.test_times` is unset.
Theme: tests
Raised by the retrospective of 2026-11-18.

## [2026-11-18-91] [idea] Agents stop calling sleep, which the harness refuses

`Bash:sleep` failed 18 of the 19 times it was called (error share 0.95), across 12 of the 41 changes that recorded tool calls. The harness refuses a foreground sleep, so each call is a spent turn. The agents that wait on something (the builder and the behaviour reviewer, most likely) should be told how to wait instead: poll with a bounded command, or hand the wait back to the script.
Theme: factory
Raised by the retrospective of 2026-11-18.

## [2026-11-18-92] [idea] Name the skill an after-gate stop follows

`metrics.extra` counts 15 `after_gate` stops across 11 changes: messages the person typed after a WAIT was answered. A kind that recurs means some skill could ask it in its WAIT. The retrospective can't say which skill, because the stop records no skill. Recording the skill whose gate it followed, on the `Close` trailer, would let the next retrospective name it.
Theme: metrics
Raised by the retrospective of 2026-11-18.

## [2026-11-18-93] [idea] The review doc names a doc's claim left false by the change

Five changes' Important findings share one class: a context or reference doc still states a rule the change altered, or one place restates a rule changed in another. These are 072 F1, 077 F1, 127 F1, 128 F1 and F2, and 130 F1, and all were fixed before landing. The proposed bullet for `.sdlc/REVIEW.md`, *The ways this repo's code fails*:

- **A doc's claim the change made false.** A sentence in `AGENTS.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md` or a README that names the function, the command or the rule this diff changed, and still says what it did before. Grep the docs for each name the diff touches.
Theme: review
Raised by the retrospective of 2026-11-18.

## [2026-11-18-95] [bug] A builder's "UNTESTABLE: none." stops the run as untestable

A builder that writes `- UNTESTABLE: none.` is read as having one untestable requirement named "none.": `UNTESTABLE_RE` (plugins/factory/scripts/factory.py:201) captures any text, so `early_stop()` stops the run and the approver must ESCALATE a change with no gap. 155's round 1 showed it: three PASSes, a green gate, and an ESCALATE whose only reasons were this stop and a look. `none` (with or without a period) should mean no untestable requirements.

Severity: low
Paths: plugins/factory/scripts/factory.py
Introduced by: 136-factory-rounds-that-catch-enough
Theme: factory

## [2026-11-18-96] [nit] the rewrapped "One gate at a time" bullet leaves one line over the wrap width

Raised by the code review of 155-agent-test-runs-share-the-slot, round 1: plugins/factory/README.md:170: the rewrapped "One gate at a time" bullet leaves one line over the wrap width

Theme: style
Paths: plugins/factory/README.md
Cost: S
Value: low
Raised by: 155-agent-test-runs-share-the-slot (correctness)

## [2026-11-18-97] [nit] `FACTORY_CHECK_RE` accepts an optional quote after `.py`, so a quoted path matches, which the test covers.

Raised by the code review of 155-agent-test-runs-share-the-slot, round 1: scripts/metrics.py:132: `FACTORY_CHECK_RE` accepts an optional quote after `.py`, so a quoted path matches, which the test covers. The same quote case isn't handled for `HAND_GATE_RE`, so the two regexes treat quoted paths differently

Theme: robustness
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 155-agent-test-runs-share-the-slot (correctness)

## [2026-11-18-98] [nit] the new R3 and R4 tests carry no `@pytest.mark.portable` even though the spec says "marked `portable` where they use no shebang fakes".

Raised by the test review of 155-agent-test-runs-share-the-slot, round 1: tests/test_factory.py:4900: the new R3 and R4 tests carry no `@pytest.mark.portable` even though the spec says "marked `portable` where they use no shebang fakes". The two-checks test uses `sleep` and `sh`, so leaving them unmarked is probably right, but the spec's intent is unclear.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 155-agent-test-runs-share-the-slot (correctness)

## [2026-11-18-99] [idea] Clear the eval workspaces left in /tmp by earlier case runs

Left undone by 156-cases-that-tell, carried forward when it landed: 26 `e-*` workspaces from earlier case runs sit in `/private/tmp` (made before runs removed their own); a one-off `run-cases --prune` or a line in CONTRIBUTING could clear them, behind the same `_workspace_of()` guard
See .sdlc/work/156-cases-that-tell/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-100] [nit] `ceiling = int((5 - spent) * 100) / 100` can lose a cent to float error (for example 4.35 becomes 4.34).

Raised by the code review of 156-cases-that-tell, round 1: scripts/sdlc.py:3877: `ceiling = int((5 - spent) * 100) / 100` can lose a cent to float error (for example 4.35 becomes 4.34). That is harmless, because it only errs low. Using `Decimal`, or `math.floor(x * 100 + 1e-9)`, would be more exact.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 156-cases-that-tell (correctness)

## [2026-11-18-101] [nit] the workspace test chmods to 0 and then restores in `finally`.

Raised by the test review of 156-cases-that-tell, round 1: tests/test_evals.py:523: the workspace test chmods to 0 and then restores in `finally`. A failure partway through could leave `outside` unreadable for pytest's tmp cleanup.

Theme: tests
Paths: tests/test_evals.py
Cost: S
Value: low
Raised by: 156-cases-that-tell (correctness)

## [2026-11-18-103] [bug] A second repo's dashboard reports another repo's board as its own

A second repo's /sdlc:dashboard reports "serving: already" on 5170 when another repo's board holds it: _is_board() (scripts/board.py:1015) checks only state.json's "board": "sdlc" marker, never which repo the board shows, so a host's dashboard points at another repo's board. Expected: "already" only for the same repo root; another repo's board is a refusal naming the port, and the skill starts on another --port. To see it: start a board in one repo with `sdlc.py board --port 5170`, then run /sdlc:dashboard in another.

Severity: low
Paths: scripts/board.py, skills/dashboard/SKILL.md
Introduced by: 075-factory-dashboard
Theme: board

## [2026-11-18-104] [nit] the spec's `test_the_source_guards_reach_closing_py` plants all four cases (main ref, `gh` call, literal `work/`, second push).

Raised by the test review of 153-risky-code-in-its-own-modules, round 1: tests/test_sdlc.py:1921: the spec's `test_the_source_guards_reach_closing_py` plants all four cases (main ref, `gh` call, literal `work/`, second push). It plants only two, and the other two live in `test_work_folder.py` and presumably `test_skills.py`.

Theme: tests
Paths: tests/test_sdlc.py
Cost: S
Value: low
Raised by: 153-risky-code-in-its-own-modules (correctness)

## [2026-11-18-105] [idea] Hosts: the scorecard reaches hosts when S14 and S15 build it into the plugin: the numbers in `sdlc.py retro` (core, language-neutral), the page in `templates/retro.md` (a host overrides it in `.sdlc/templates/`), the synthesis questions in a `guide/` file a host extends, and the metrics' meanings in `docs/REFERENCE.md`'s *Retrospectives*.

Left undone by 159-retro-scorecard-doc, carried forward when it landed: Hosts: the scorecard reaches hosts when S14 and S15 build it into the plugin: the numbers in `sdlc.py retro` (core, language-neutral), the page in `templates/retro.md` (a host overrides it in `.sdlc/templates/`), the synthesis questions in a `guide/` file a host extends, and the metrics' meanings in `docs/REFERENCE.md`'s *Retrospectives*. This doc stays this repo's design reference. In a host, the Simplicity pillar means the process's overhead and workarounds there; the plugin's own surface (skills used, footprint, growth) is this repo's measure alone. The structural debt index comes from the host's own `retro.indicators`, in its language.
See .sdlc/work/159-retro-scorecard-doc/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-107] [idea] Hosts: the skills' cases are this repo's only, so nothing about them is in a host's scorecard, and a host with no factory gets the by-hand view: mode comparison and pipeline health say "no factory changes" rather than show zeros.

Left undone by 159-retro-scorecard-doc, carried forward when it landed: Hosts: the skills' cases are this repo's only, so nothing about them is in a host's scorecard, and a host with no factory gets the by-hand view: mode comparison and pipeline health say "no factory changes" rather than show zeros.
See .sdlc/work/159-retro-scorecard-doc/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-108] [nit] `heat()` ignores the `--root` blame edge when a file was created after the boundary.

Raised by the code review of 161-function-heat, round 1: `.sdlc/function-heat.py:123`: `heat()` ignores the `--root` blame edge when a file was created after the boundary. A commit that only added the whole file counts as 1, which is correct, but a one-line comment would say so

Theme: docs
Paths: .sdlc/function-heat.py
Cost: S
Value: low
Raised by: 161-function-heat (correctness)

## [2026-11-18-109] [nit] `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so).

Raised by the test review of 160-command-registry, round 1: tests/test_registry.py:104: `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so). It guards R7 and would catch a later regression, but it never failed on the old code. Only the `config` command is stubbed, so an adapter that bound its handler at import time would be caught for that one command and no other. Stubbing one more, such as `status` with the default no-command path, would cover R5's `--all` default through `main()`.

Theme: tests
Paths: tests/test_registry.py
Cost: S
Value: low
Raised by: 160-command-registry (correctness)

## [2026-11-19-1] [nit] `lead_time()` returns `{}` when `opened` is after `closed`, and the code files that as `lead=bad-opened`.

Raised by the code review of 162-lead-time, round 1: scripts/closing.py:474: `lead_time()` returns `{}` when `opened` is after `closed`, and the code files that as `lead=bad-opened`. That word is meant for an unparsable `opened:`. A clock that ran backwards is a different case; a distinct word such as `lead=clock` would say which one it was.

Theme: docs
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 162-lead-time (correctness)

## [2026-11-19-2] [nit] a factory change with no timed rows and no transcript events gets `ready=None`, so `ready_wait` is dropped (`source=git`).

Raised by the code review of 162-lead-time, round 1: scripts/closing.py:431: a factory change with no timed rows and no transcript events gets `ready=None`, so `ready_wait` is dropped (`source=git`). R10's "no transcripts" case says `lead`, `ready_wait` and `landing` are kept. The code is reasonable, because there is no approver row to read `ready` from. The spec could say so, or `ready` could fall back to the tip's author date for a factory change too.

Theme: robustness
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 162-lead-time (correctness)

## [2026-11-19-3] [nit] the broad `except Exception` also hides programming errors as `lead=failed`.

Raised by the security review of 162-lead-time, round 1: scripts/closing.py:475: the broad `except Exception` also hides programming errors as `lead=failed`. That fits "never refuses", but it could log the exception's type name to stderr so a regression is visible

Theme: robustness
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 162-lead-time (contract)

## [2026-11-19-4] [nit] the `lead=bad-opened` path for `opened` after `closed` (decision D3) has no test of its own; only a malformed value is parametrized

Raised by the test review of 162-lead-time, round 1: tests/test_archive.py: the `lead=bad-opened` path for `opened` after `closed` (decision D3) has no test of its own; only a malformed value is parametrized

Theme: tests
Paths: tests/test_archive.py
Cost: S
Value: low
Raised by: 162-lead-time (correctness)

## [2026-11-19-8] [nit] the R5 test only builds the `build` task, so the refusal for a broken `mend.md` or `land-review.md` under `land-mend` is untested.

Raised by the test review of 164-prompts-in-files, round 1: tests/test_prompts.py:439: the R5 test only builds the `build` task, so the refusal for a broken `mend.md` or `land-review.md` under `land-mend` is untested. `_task()` validates both files by the same code path, so the risk is low.

Theme: tests
Paths: tests/test_prompts.py
Cost: S
Value: low
Raised by: 164-prompts-in-files (correctness)

## [2026-11-19-9] [idea] Comment health as a retro indicator

Agent-written code tends to over-comment (RealHumanEval: about 2x the comments; it narrates when unsure), while too few comments make complex code unauditable, and comment text is roughly 30% of what agents read in this repo's scripts. No research gives one right ratio (open-source norm about 19% of lines, Arafat & Riehle 2009), so measure four signals rather than one: per-file density as a band (flag <0.10 or >0.40) and its trend across the window; docstring coverage of long (>=30 lines) and hot functions; the share of narration comments that restate their line; and the comment share of agent input tokens. Ship it as an indicator script beside .sdlc/function-heat.py (this repo's, Python), reported through retro.indicators in the Quality pillar with Cost as its guardrail. Follows S8 (structured indicators) in docs/RETRO-SCORECARD.md.
Theme: retro
Raised 2026-11-19.

## [2026-11-19-5] [nit] the "Modules loaded by path" and "The board" edits leave lines far over the file's wrap width (about 100 columns)

Raised by the code review of 163-factory-records-reader, round 1: AGENTS.md:68: the "Modules loaded by path" and "The board" edits leave lines far over the file's wrap width (about 100 columns)

Theme: docs
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)

## [2026-11-19-6] [nit] the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable.

Raised by the code review of 163-factory-records-reader, round 1: tests/test_board.py: the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable. It was a comparison of two copies, and with one copy it would compare the module with itself. `LAND_STOPS` still has no factory twin, so nothing checks it against the factory. It is only pinned against `LAND_STEPS` through the board's `LAND_AT` test.

Theme: tests
Paths: tests/test_board.py
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)

## [2026-11-19-7] [nit] a few helper names such as `_reached` and `_named` have no docstring

Raised by the test review of 163-factory-records-reader, round 1: tests/test_modules.py: a few helper names such as `_reached` and `_named` have no docstring

Theme: tests
Paths: tests/test_modules.py
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)
