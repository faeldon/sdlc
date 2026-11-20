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

## [2026-11-18-74] [idea] Limit CI's GITHUB_TOKEN to contents: read in check.yml

Left undone by 152-board-drawer-browser-test, carried forward when it landed: pre-existing: .github/workflows/check.yml:13: no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token
See .sdlc/work/152-board-drawer-browser-test/notes.md in its commit.
Theme: ci
Raised 2026-11-18.

## [2026-11-18-99] [idea] Clear the eval workspaces left in /tmp by earlier case runs

Left undone by 156-cases-that-tell, carried forward when it landed: 26 `e-*` workspaces from earlier case runs sit in `/private/tmp` (made before runs removed their own); a one-off `run-cases --prune` or a line in CONTRIBUTING could clear them, behind the same `_workspace_of()` guard
See .sdlc/work/156-cases-that-tell/notes.md in its commit.
Raised 2026-11-18.
Theme: tests

## [2026-11-19-24] [nit] R14 still says "a `time.monotonic()` deadline of 60 s", but the test and its sibling `_killed_at_its_gate` now use 120 s.

Raised by the code review of 171-factory-run-state, round 2: .sdlc/work/171-factory-run-state/spec.md:42: R14 still says "a `time.monotonic()` deadline of 60 s", but the test and its sibling `_killed_at_its_gate` now use 120 s. Change R14 to 120 s, since startup here takes about 60 s.

Theme: docs
Paths: .sdlc/work/171-factory-run-state/spec.md
Cost: S
Value: med
Raised by: 171-factory-run-state (correctness)

## [2026-11-19-25] [nit] R14 still says a 60 s deadline, but the test and `plan.md` now use 120 s.

Raised by the test review of 171-factory-run-state, round 2: .sdlc/work/171-factory-run-state/spec.md:42: R14 still says a 60 s deadline, but the test and `plan.md` now use 120 s. Reword R14 to 120 s so the spec matches the code.

Theme: docs
Paths: .sdlc/work/171-factory-run-state/spec.md
Cost: S
Value: med
Raised by: 171-factory-run-state (correctness)

## [2026-11-19-27] [idea] Rewrap the remaining factory agents' prose lines past 100 columns

Left undone by 173-style-paydown, carried forward when it landed: The other factory agents (`approver.md`, `builder.md`, `resolver.md`, `reviewer-behaviour.md`, `reviewer-security.md`, `reviewer-test.md`, `reviewer-ui.md`, `spec-writer.md`, `verifier.md`) keep prose lines past 100 columns; no entry named them, so they stayed out of this change.
See .sdlc/work/173-style-paydown/notes.md in its commit.
Raised 2026-11-19.
Theme: style

## [2026-11-19-28] [nit] the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

Raised by the test review of 173-style-paydown, round 1: plugins/factory/agents/reviewer-test.md:13: the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

Theme: docs
Paths: plugins/factory/agents/reviewer-test.md
Cost: S
Value: low
Raised by: 173-style-paydown (correctness)

## [2026-11-19-78] [nit] the builder's note is right that it also runs `uv run --script` and could share `_uv()`.

Raised by the code review of 186-gate-reliability, round 1: tests/test_train.py: the builder's note is right that it also runs `uv run --script` and could share `_uv()`. Filed as a follow-up.

Theme: refactor
Paths: tests/test_train.py
Cost: M
Value: med
Raised by: 186-gate-reliability (correctness)

## [2026-11-20-7] [idea] Read-only list refuses ugrep's symlink-following long options (`--dereference-files` and its prefixes)

Left undone by 193-ledger-and-landing-fixes, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:795: the grep refusals cover GNU grep and BSD grep only. If a host's `grep` on `PATH` is ugrep, `grep -r --dereference-files keep .` is allowed and follows links to files outside the checkout. This change didn't add or touch that gap, but it is in the same function. Fix: refuse `--dereference-files` and its prefixes too, or check every word against a list of such long options.
See .sdlc/work/193-ledger-and-landing-fixes/notes.md in its commit.
Raised 2026-11-20.
Theme: landing

## [2026-11-20-11] [idea] Show a spec step and its elapsed time on a Designing card

Left undone by 195-designing-while-specified, carried forward when it landed: The board's step track (`_progress()`) shows nothing for a first spec draft, which records no `runs/step.md`; a card under Designing could show a `spec` step with its elapsed time.
See .sdlc/work/195-designing-while-specified/notes.md in its commit.
Raised 2026-11-20.
Theme: board

## [2026-11-20-12] [nit] the edited line is now about 110 characters, while its neighbours wrap near 100.

Raised by the code review of 195-designing-while-specified, round 1: docs/REFERENCE.md:575: the edited line is now about 110 characters, while its neighbours wrap near 100. Rewrap the paragraph.

Theme: style
Paths: docs/REFERENCE.md
Cost: S
Value: low
Raised by: 195-designing-while-specified (correctness)

## [2026-11-20-13] [nit] `specifying()` has a lot of branching and repeats the read-text-if-file pattern three times.

Raised by the code review of 195-designing-while-specified, round 1: scripts/factory_records.py:300: `specifying()` has a lot of branching and repeats the read-text-if-file pattern three times. A small helper would shorten it.

Theme: refactor
Paths: scripts/factory_records.py
Cost: S
Value: low
Raised by: 195-designing-while-specified (correctness)

## [2026-11-20-37] [idea] See whether fewer changes at once shortens lead time

A factory change's lead time (median 166 minutes, n=33) is a quarter queued (0.25) and a fifth
waiting at ready (0.22), against 0.21 in agents. A median of 3.5 changes ran at once (most 6), and
the 32 that ran beside three or more others took a median 68.5 minutes elapsed, against 20 for the
4 that ran alone. Four is anecdote. Try one wave built with at most three changes open, and compare
its queued and ready-wait shares with this window's. Raised by the retrospective of 2026-11-20.
Theme: autonomy
Priority: low

## [2026-11-20-44] [nit] the `staged_gone` comprehension still calls `_status_entries(root)` a second time, after `_stray()` has already read it.

Raised by the code review of 198-landing-stages-its-own-paths, round 1: `plugins/factory/scripts/landing.py:2923`: the `staged_gone` comprehension still calls `_status_entries(root)` a second time, after `_stray()` has already read it. `_staged()` and `_stray()` also read the index separately. One shared read would be cleaner.

Theme: refactor
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 198-landing-stages-its-own-paths (correctness)

## [2026-11-20-45] [nit] the `[edit]` and `[mv]` cases both stray on `.gitignore`, and nothing separately pins that a staged rename's old path is named when only the new path is owned

Raised by the test review of 198-landing-stages-its-own-paths, round 1: tests/test_train.py:1158: the `[edit]` and `[mv]` cases both stray on `.gitignore`, and nothing separately pins that a staged rename's old path is named when only the new path is owned

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 198-landing-stages-its-own-paths (correctness)

## [2026-11-20-46] [nit] `uncarried()` reports `named` (an id in both SETTLED and CONFIRM) only when the id is also CONFIRMed.

Raised by the code review of 202-defaults-to-landing, round 1: plugins/factory/scripts/run_state.py:104: `uncarried()` reports `named` (an id in both SETTLED and CONFIRM) only when the id is also CONFIRMed. A default that is open and listed as SETTLED but not ticked, because `decisions` was skipped or refused it, reads as "no `- CONFIRM:` line". The mend text then points the approver at the wrong fix. Naming the SETTLED line in that case would be clearer.

Theme: robustness
Paths: plugins/factory/scripts/run_state.py
Cost: S
Value: low
Raised by: 202-defaults-to-landing (correctness)

## [2026-11-20-47] [nit] `intent_closes()` reads `closes:` from the branch's own intent.md while the sensitive bar is read from the base branch; read it from the fork point so a build can't widen what it may carry

Raised by the security review of 202-defaults-to-landing, round 1: plugins/factory/scripts/factory.py:1973: `intent_closes()` reads `closes:` from the branch's own intent.md while the sensitive bar is read from the base branch; read it from the fork point so a build can't widen what it may carry

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 202-defaults-to-landing (contract)

## [2026-11-20-48] [nit] the "closes" case writes `closes: [12]` by string-replacing `idea:` in `intent.md`.

Raised by the test review of 202-defaults-to-landing, round 1: tests/test_factory_decisions.py:523: the "closes" case writes `closes: [12]` by string-replacing `idea:` in `intent.md`. If the fixture's frontmatter changes, the case could pass without exercising the `closes:` rule, though the assertion on `closes: [12]` in the problem text would still catch that.

Theme: tests
Paths: tests/test_factory_decisions.py
Cost: S
Value: low
Raised by: 202-defaults-to-landing (correctness)

## [2026-11-20-49] [nit] the new block names no number of changes or days.

Raised by the code review of 205-release-cadence, round 1: .sdlc/SDLC.md:83: the new block names no number of changes or days. The "once each wave has landed" rule is fine, but a person may wonder what to do if a wave stalls past the 14-day mark. One clause would settle it.

Theme: docs
Paths: .sdlc/SDLC.md
Cost: S
Value: low
Raised by: 205-release-cadence (correctness)

## [2026-11-20-50] [idea] The train's reading runs about 1,500 git calls for a driven train of three (723 `rev-parse`, 418 `show`), which is most of each train test's time and of a real landing's bookkeeping.

Left undone by 200-tests-pruned-again, carried forward when it landed: The train's reading runs about 1,500 git calls for a driven train of three (723 `rev-parse`, 418 `show`), which is most of each train test's time and of a real landing's bookkeeping. Caching what doesn't change within one reading would speed both.
See .sdlc/work/200-tests-pruned-again/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-51] [idea] No test fails when the train's readiness refusal (`_land_readiness()`'s `refusal`, in `cmd_train`) is ejected under another cause: mutating its `"refusal"` to `"review"` passed every train and landing test.

Left undone by 200-tests-pruned-again, carried forward when it landed: No test fails when the train's readiness refusal (`_land_readiness()`'s `refusal`, in `cmd_train`) is ejected under another cause: mutating its `"refusal"` to `"review"` passed every train and landing test. The removed `test_every_ejection_names_its_cause` never reached that path either: its stray file is the `failed` path, which `test_train_run_stops_at_a_refusal` covers.
See .sdlc/work/200-tests-pruned-again/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-52] [nit] `_names()` is the one place a string-to-path match is decided, and its docstring wraps mid-sentence and is hard to read.

Raised by the code review of 200-tests-pruned-again, round 1: scripts/indicators.py:478: `_names()` is the one place a string-to-path match is decided, and its docstring wraps mid-sentence and is hard to read. Splitting it into two sentences would help.

Theme: docs
Paths: scripts/indicators.py
Cost: S
Value: low
Raised by: 200-tests-pruned-again (correctness)

## [2026-11-20-53] [nit] the paragraph opens "one is left", then lists several tests under "Kept", and only `test_function_heat.py` still drifts.

Raised by the code review of 200-tests-pruned-again, round 1: .sdlc/work/200-tests-pruned-again/notes.md:8: the paragraph opens "one is left", then lists several tests under "Kept", and only `test_function_heat.py` still drifts. Rewording it to say that would match what follows.

Theme: docs
Paths: .sdlc/work/200-tests-pruned-again/notes.md
Cost: S
Value: low
Raised by: 200-tests-pruned-again (context)

## [2026-11-20-54] [nit] `BUILT_IN` is a hand-kept list, and the check reads `node.args.args` only, so a keyword-only fixture is missed.

Raised by the code review of 201-tests-and-robustness-nits, round 1: tests/test_suite_shape.py:12: `BUILT_IN` is a hand-kept list, and the check reads `node.args.args` only, so a keyword-only fixture is missed. Reading `kwonlyargs` too is a one-line fix

Theme: tests
Paths: tests/test_suite_shape.py
Cost: S
Value: low
Raised by: 201-tests-and-robustness-nits (correctness)

## [2026-11-20-55] [nit] the plan promises a line naming the test that settles each of the 20 nits 191 already fixed.

Raised by the code review of 201-tests-and-robustness-nits, round 1: .sdlc/work/201-tests-and-robustness-nits/notes.md: the plan promises a line naming the test that settles each of the 20 nits 191 already fixed. I only confirmed that `notes.md` exists (74 lines) and did not check that all 20 are covered

Theme: docs
Paths: .sdlc/work/201-tests-and-robustness-nits/notes.md
Cost: S
Value: low
Raised by: 201-tests-and-robustness-nits (context)

## [2026-11-20-56] [idea] Surface key scan follows calls only, to separate always-read keys from branch-read keys

Left undone by 204-scorecard-reads-true, carried forward when it landed: The scan's reach could follow only calls, not every mention of a name, if the surface's key share should separate keys a command reads on every run from keys it reads on one branch.
See .sdlc/work/204-scorecard-reads-true/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-57] [nit] the line `restored \`no register entry added in the window\`.

Raised by the code review of 204-scorecard-reads-true, round 1: docs/REFERENCE.md:1344: the line `restored \`no register entry added in the window\`. A greyed block's note…` is now over-long after the reflow; rewrap it

Theme: docs
Paths: docs/REFERENCE.md
Cost: S
Value: low
Raised by: 204-scorecard-reads-true (correctness)

## [2026-11-20-58] [nit] `_vouch()` calls `closing._unlock` but `_try_lock` from the local module.

Raised by the code review of 199-landing-records-unforgeable, round 1: scripts/sdlc.py:3283: `_vouch()` calls `closing._unlock` but `_try_lock` from the local module. Both work, but a one-line comment would say why the pair is split.

Theme: docs
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 199-landing-records-unforgeable (correctness)

## [2026-11-20-59] [nit] the spec's R9 requires a test of two writers at once.

Raised by the code review of 199-landing-records-unforgeable, round 1: tests/test_records_ledger.py: the spec's R9 requires a test of two writers at once. One exists (`test_two_writers_at_once_leave_whole_lines`), but it only covers `factory.py`'s writer and not core's copy under the same lock.

Theme: tests
Paths: tests/test_records_ledger.py
Cost: S
Value: low
Raised by: 199-landing-records-unforgeable (correctness)

## [2026-11-20-60] [nit] "An agent editing the change's worktree can't forge one" overstates the protection when the builder and resolver have Bash.

Raised by the security review of 199-landing-records-unforgeable, round 1: plugins/factory/README.md: "An agent editing the change's worktree can't forge one" overstates the protection when the builder and resolver have Bash. Say that it protects against the Edit and Write tools, not against a shell that can reach the git common dir

Theme: docs
Paths: plugins/factory/README.md
Cost: S
Value: med
Raised by: 199-landing-records-unforgeable (contract)

## [2026-11-20-61] [nit] check again that `earlier` is vouched when it's read after the run, not only before the slot wait

Raised by the security review of 199-landing-records-unforgeable, round 1: plugins/factory/scripts/factory.py:3358: check again that `earlier` is vouched when it's read after the run, not only before the slot wait

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: med
Raised by: 199-landing-records-unforgeable (contract)

## [2026-11-20-62] [nit] the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

Raised by the test review of 199-landing-records-unforgeable, round 1: tests/test_records_ledger.py:152: the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

Theme: tests
Paths: tests/test_records_ledger.py
Cost: S
Value: low
Raised by: 199-landing-records-unforgeable (correctness)
