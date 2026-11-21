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

## [2026-11-20-62] [nit] the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

Raised by the test review of 199-landing-records-unforgeable, round 1: tests/test_records_ledger.py:152: the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

Theme: tests
Paths: tests/test_records_ledger.py
Cost: S
Value: low
Raised by: 199-landing-records-unforgeable (correctness)

## [2026-11-21-3] [nit] the register paragraph now has a line well over 100 characters, because "Each line's command is `/sdlc:intent <id>`." was glued onto the end of the new clause.

Raised by the code review of 207-change-origin, round 1: docs/REFERENCE.md:508: the register paragraph now has a line well over 100 characters, because "Each line's command is `/sdlc:intent <id>`." was glued onto the end of the new clause. Rewrap it

Theme: style
Paths: docs/REFERENCE.md
Cost: S
Value: low
Raised by: 207-change-origin (correctness)

## [2026-11-21-4] [nit] the two lines edited for `origin:` run past the file's wrapping width.

Raised by the code review of 207-change-origin, round 1: skills/intent/batch.md:34: the two lines edited for `origin:` run past the file's wrapping width. Rewrap them

Theme: style
Paths: skills/intent/batch.md
Cost: S
Value: low
Raised by: 207-change-origin (correctness)

## [2026-11-21-5] [nit] `origin_trailer()` catches every `Exception`, not just a git or read failure, so a coding error there would make origins quietly unknown on every close instead of failing a test; `fix_trailers()` does the same

Raised by the security review of 207-change-origin, round 1: scripts/closing.py:558: `origin_trailer()` catches every `Exception`, not just a git or read failure, so a coding error there would make origins quietly unknown on every close instead of failing a test; `fix_trailers()` does the same

Theme: robustness
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 207-change-origin (contract)

## [2026-11-21-6] [nit] `test_idea_and_bug_offer_an_origin_line` only asserts that `Origin: self` is absent from the skill text.

Raised by the test review of 207-change-origin, round 1: tests/test_skills.py: `test_idea_and_bug_offer_an_origin_line` only asserts that `Origin: self` is absent from the skill text. It would not catch the skills telling the person to write `self` in other words

Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 207-change-origin (correctness)

## [2026-11-21-7] [idea] Manually verify the update hook and /sdlc:update in a scratch repo

Left undone by 206-update-skill, carried forward when it landed: Manual (the spec's Verification): in a scratch repo with the plugin installed from GitHub at an older version, a new session shows the one line (proves `systemMessage` reaches the person), `/sdlc:update` lists its steps, and `--scope project` acts on the folder it runs in.
See .sdlc/work/206-update-skill/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-8] [nit] `update_line` returns None when the sdlc install here is read from a folder, so a stale `sdlc-factory` install is also never mentioned.

Raised by the code review of 206-update-skill, round 1: scripts/sdlc.py:9507: `update_line` returns None when the sdlc install here is read from a folder, so a stale `sdlc-factory` install is also never mentioned. This follows D2 but is broader than it needs to be. Check the factory row separately if that matters

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)

## [2026-11-21-9] [nit] `update_line`'s first form ("this session runs X") also fires when the install is already updated and only the restart is missing.

Raised by the code review of 206-update-skill, round 1: scripts/sdlc.py:9546: `update_line`'s first form ("this session runs X") also fires when the install is already updated and only the restart is missing. `/sdlc:update` then handles it through `restart_first`, so this is fine. A short comment would say so

Theme: docs
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)

## [2026-11-21-10] [nit] the fake `claude` opens its log and rows files without an encoding, unlike the `encoding="utf-8"` the repo's tests use elsewhere.

Raised by the test review of 206-update-skill, round 1: tests/test_update.py:107: the fake `claude` opens its log and rows files without an encoding, unlike the `encoding="utf-8"` the repo's tests use elsewhere. It is not a portable test, so it only matters on a non-UTF-8 locale.

Theme: tests
Paths: tests/test_update.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)

## [2026-11-21-11] [nit] the fake `claude` opens its log and rows files without `encoding="utf-8"`.

Raised by the test review of 206-update-skill, round 2: tests/test_update.py:107: the fake `claude` opens its log and rows files without `encoding="utf-8"`. It is not a portable test, so it only matters on a non-UTF-8 locale.

Theme: tests
Paths: tests/test_update.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)

## [2026-11-21-13] [nit] R3 says a listed path under this repo's `.claude/worktrees/` is skipped and counted as `own`.

Raised by the test review of 208-retro-reads-hosts, round 1: tests/test_retro_hosts.py:329: R3 says a listed path under this repo's `.claude/worktrees/` is skipped and counted as `own`. Only the main checkout is listed in the fixtures, so the worktree case is never exercised. Add a worktree path to `_listed`.

Theme: tests
Paths: tests/test_retro_hosts.py
Cost: S
Value: med
Raised by: 208-retro-reads-hosts (correctness)

## [2026-11-21-14] [nit] the `!` exclusion is only shown against a path that doesn't exist, so it would pass even if an excluded host were still read.

Raised by the test review of 208-retro-reads-hosts, round 1: tests/test_retro_hosts.py:325: the `!` exclusion is only shown against a path that doesn't exist, so it would pass even if an excluded host were still read. Exclude a real fixture host and assert it is absent from `read`.

Theme: tests
Paths: tests/test_retro_hosts.py
Cost: S
Value: med
Raised by: 208-retro-reads-hosts (correctness)

## [2026-11-21-15] [nit] R12 says no host figure enters the indicators the next retro reads back.

Raised by the test review of 208-retro-reads-hosts, round 1: tests/test_retro_hosts.py:426: R12 says no host figure enters the indicators the next retro reads back. The test compares `retro`'s JSON with and without a list, but doesn't compare the report's indicators block.

Theme: tests
Paths: tests/test_retro_hosts.py
Cost: S
Value: low
Raised by: 208-retro-reads-hosts (correctness)

## [2026-11-21-16] [nit] the reflowed *Setup* paragraph leaves a short line, "same change.

Raised by the code review of 213-setup-nudge, round 1: AGENTS.md:218: the reflowed *Setup* paragraph leaves a short line, "same change. `git.attribution` has no default on", that could be rewrapped.

Theme: style
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 213-setup-nudge (correctness)

## [2026-11-21-17] [nit] the R5 test never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned; a second mock that raises `UnicodeDecodeError` would close it

Raised by the test review of 213-setup-nudge, round 1: tests/test_setup_lifecycle.py:735: the R5 test never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned; a second mock that raises `UnicodeDecodeError` would close it

Theme: tests
Paths: tests/test_setup_lifecycle.py
Cost: S
Value: low
Raised by: 213-setup-nudge (correctness)

## [2026-11-21-18] [nit] match `UPSTREAM_MARKER` only on the body's first line, as R12 describes it.

Raised by the security review of 209-upstream-bugs, round 1: scripts/sdlc.py:7883: match `UPSTREAM_MARKER` only on the body's first line, as R12 describes it.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 209-upstream-bugs (contract)

## [2026-11-21-19] [nit] the triage skill's `Origin: host` instruction has no text test

Raised by the test review of 209-upstream-bugs, round 1: tests/test_skills.py: the triage skill's `Origin: host` instruction has no text test

Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 209-upstream-bugs (correctness)

## [2026-11-21-20] [nit] also turn a dotless ssh-alias remote (`user@alias:path`) into `<remote>`

Raised by the security review of 209-upstream-bugs, round 2: scripts/sdlc.py:9721: also turn a dotless ssh-alias remote (`user@alias:path`) into `<remote>`

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 209-upstream-bugs (contract)

## [2026-11-21-22] [idea] Pin CI actions to commit SHAs

Left undone by 211-ci-token-read, carried forward when it landed: pre-existing: .github/workflows/check.yml:23: `actions/checkout@v4` and `astral-sh/setup-uv@v6` are pinned by moveable tag, not by commit SHA. Pin each to a full SHA with the version in a comment, and let Dependabot or Renovate bump them.
See .sdlc/work/211-ci-token-read/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-24] [idea] Let ugrep's `-O EXT` pass the read-only grep check while BSD's `-O` stays refused

Left undone by 212-landing-gaps, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:816: `GREP_FOLLOWS` refuses `-O` (BSD's follow-links flag) for every grep, so ugrep's harmless `-O EXT` (search by file extension) is refused too. This is overly strict, not a hole.
See .sdlc/work/212-landing-gaps/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-25] [nit] the `--filter`, `--pager` and `--view` refusals match the exact name only, not `--filter-magic-label`.

Raised by the code review of 212-landing-gaps, round 1: plugins/factory/scripts/landing.py:921: the `--filter`, `--pager` and `--view` refusals match the exact name only, not `--filter-magic-label`. That is harmless and ugrep takes no prefixes, but a comment saying so would help.

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 212-landing-gaps (correctness)

## [2026-11-21-26] [nit] a GNU or BSD grep refusal of `--config` or `---…` says "makes ugrep …", which may confuse a person reading it on a host without ugrep.

Raised by the security review of 212-landing-gaps, round 1: plugins/factory/scripts/landing.py:925: a GNU or BSD grep refusal of `--config` or `---…` says "makes ugrep …", which may confuse a person reading it on a host without ugrep. "makes grep (ugrep) …" would be clearer

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 212-landing-gaps (contract)

## [2026-11-21-27] [nit] no case checks a bare `-d dereference-recurse` word that is really a grep pattern, which D2 accepts refusing.

Raised by the test review of 212-landing-gaps, round 1: tests/test_train.py:2340: no case checks a bare `-d dereference-recurse` word that is really a grep pattern, which D2 accepts refusing. A pin would document the trade-off.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 212-landing-gaps (correctness)

## [2026-11-21-29] [idea] Add `update` to AGENTS.md's Skills invariant list of WAIT skills

Left undone by 210-wait-previews, carried forward when it landed: AGENTS.md's *Skills* invariant lists the skills that write and owe a WAIT, but leaves out `update`, which `tests/test_skills.py`'s `GATED` includes. Found while building 210; left as it was, since naming it is a separate edit to the list.
See .sdlc/work/210-wait-previews/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-30] [nit] R7 says `--preview` takes the same clause flags as `--question`.

Raised by the code review of 210-wait-previews, round 1: scripts/sdlc.py:8308: R7 says `--preview` takes the same clause flags as `--question`. They parse, but `cmd_ship_preview` ignores them without saying so. Refuse them with `--preview`, as the code already refuses clause flags without `--question`, or say in the help text that they are ignored.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 210-wait-previews (correctness)

## [2026-11-21-31] [nit] the `PREVIEW_NAMES` words are checked with substring `in`, so a key word like `path` or `tag` matches any text that contains it

Raised by the test review of 210-wait-previews, round 1: tests/test_skills.py:263: the `PREVIEW_NAMES` words are checked with substring `in`, so a key word like `path` or `tag` matches any text that contains it

Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 210-wait-previews (correctness)

## [2026-11-21-32] [idea] Autopilot level 1: the factory runs from seed to landing without a person

`/sdlc-factory:autopilot` runs the whole loop while the person is away or asleep: it picks
compelling seeds from the register (bugs by severity, `Priority: high`, the product doc's outcomes
and milestones), groups them into waves that won't overlap, opens their intents, builds each as
soon as what it depends on has landed, and lands what is ready in batches, waiting for a
nearly-ready change when landing them together saves runs and cases.

It runs as a background loop on the landing train's model, not in the person's session. The
skill asks one WAIT, which bounds the run (which seeds or themes, a dollar cap, hours, the level),
then starts `factory.py autopilot --run` in the background. The script is the scheduler: the queue,
the waves, dependencies, the budget, the off switch, and the run's state in the git common dir, so
a stopped or compacted session loses nothing and a rerun resumes it. Each judgment goes to a fresh
agent session with no Write, its reply filed by the script as a reviewer's is: which wave is next,
an intent's draft, and the answer to an escalation. The person's session only starts it and reads
the summary, and may be closed in between.

No WAIT stops it: an escalated default is taken as the default and a look as seen, recorded as
autopilot's call (`by=autopilot`, `→ decided by autopilot:`), never as the person's, and each call
goes, with its context, into an escalations file for the person to review. A call the person
disagrees with is fixed forward, by reverting the change or by a new seed, never mid-build. It
stops for good on one kind of escalation: a change that can only be built by breaking a contract,
a hard rule or a guard, or one the supervisor judges far simpler if a contract were relaxed. That
change stays under Needs you, unlanded, and nothing that depends on it is built.

It keeps two risk budgets, each counted by the script from signals it already detects, never
judged by a model, their weights and limits in the base branch's `.sdlc/factory.toml`: review debt,
the person's unreviewed calls it made, weighted by kind (a look taken as seen least, an escalated
default, a scope call or a policy wording most); and change risk, each landed change's signals as
`land-check` counts them (sensitive or irreversible paths, `impact: major`, a conflict resolved or
a fix made while landing, failed or spoiled cases, unreviewed paths, mends, red gates), weighed
more for a pushed change than a local one, and for one stacked on another autopilot change. When
either budget is reached it starts nothing new, leaves what is in flight at `stage: test`
unlanded, and writes its summary, which leads with each budget, what spent it and on which change.

Autopilot loosens no other WAIT: by hand and in the factory, every skill still asks its own, and
`land.auto` stays the only self-approving step outside a run. The script commands its loop calls
accept `--by autopilot` only while its run lock is held, and refuse it otherwise; no skill but
autopilot's names it (a test pins this), and it adds no `allowed-tools` rule that lets another
skill's writing command run unasked. `by=person`, `by=auto` and `by=autopilot` stay three values.

It stops when no compelling seed is left, when its dollar cap, its hours or a risk budget run out,
or when the person turns it off (between steps, as `train --cancel` does), and either way writes a
summary: how long it ran and what it cost, what landed (features, bugs fixed), what is mid-build
and where, every escalation and decision it made, and the risks the person should weigh.

Open questions: whether the commands the harness asks before today (`accept`, `cases`) are allowed
for the run, or skipped; whether it pushes and syncs issues, or lands locally until the person reads
the summary; a script-drawn line for "breaks a contract" (AGENTS.md, the invariant tests, a
*Contracts touched* line); an intent opened by `new` with no person's yes; green CI as a
precondition (2026-11-21-28).
Theme: factory
Raised 2026-11-21.

## [2026-11-21-33] [idea] Autopilot levels 2–4: releases, retrospectives, direction

Beyond building (level 1): level 2 plans and cuts releases and files new seeds from what the
retrospective finds; level 3 runs the retrospectives themselves; level 4 proposes direction from
strategy, which only the person holds today. Hypothetical for now: context for how level 1's run
record, budget and summary should be built so later levels can reuse them.
After: 2026-11-21-32
Theme: factory
Priority: low
Raised 2026-11-21.

## [2026-11-21-34] [idea] The board shows an autopilot run while it runs

While `/sdlc-factory:autopilot` runs, the board says so at a glance: a red border across the top of
the page, and a band under it with the run's state, read from autopilot's run state in the git
common dir, opened read-only as the board opens the train's run lock today, never created and
never written. The band shows how long it has run and how long it has left, its dollar cost
against its cap, each risk budget (review debt and change risk) as spent against its limit, the
wave under way, and the changes it has opened, building, landed and parked under Needs you. Each
autopilot call waiting for the person's review is counted and links to the escalations file.
Once the run stops, the border goes and the band says how it ended (seeds exhausted, a budget or
the hours reached, turned off) and where its summary is. Cards autopilot opened carry a small mark,
so they read apart from changes the person started by hand.
After: 2026-11-21-32
Theme: board
Raised 2026-11-21.

## [2026-11-21-36] [idea] Show a red CI on the base branch in the landing's look and in status

Left undone by 214-ci-green, carried forward when it landed: Say when CI on the base branch is red, in a landing's look or in `status`, so the local gate isn't the only word (the intent's third open question; a seed of its own).
See .sdlc/work/214-ci-green/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-37] [idea] Scan the helpers portable tests call for unencoded reads and writes

Left undone by 214-ci-green, carried forward when it landed: 275 `read_text`/`write_text` calls in non-portable tests and helpers name no encoding. They don't run on Windows today; a test moved into `portable` gets caught by the new check, but a helper it calls doesn't.
See .sdlc/work/214-ci-green/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-38] [nit] `_hand_digests` runs `git hash-object` once per call and ignores its stderr.

Raised by the code review of 214-ci-green, round 1: scripts/sdlc.py:3076: `_hand_digests` runs `git hash-object` once per call and ignores its stderr. If it fails, the fallback silently hashes raw bytes, so a git failure could make a record read stale only on the next run. That is safe, but a one-line comment saying so would help.

Theme: docs
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 214-ci-green (correctness)

## [2026-11-21-39] [nit] `_hand_digests` is now a 15-line copy of `sdlc.py`'s, kept the same by hand.

Raised by the security review of 214-ci-green, round 1: plugins/factory/scripts/factory.py:3073: `_hand_digests` is now a 15-line copy of `sdlc.py`'s, kept the same by hand. Pin the two bodies equal in `tests/test_hand_gate.py`, as the repo's other copies are pinned, so a fix to one can't skip the other

Theme: tests
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: med
Raised by: 214-ci-green (contract)

## [2026-11-21-40] [nit] `_lost()`'s new `and not _only_time_wait(port)` branch is proved only by the existing socket test, which exercises it on Linux only.

Raised by the test review of 214-ci-green, round 1: tests/test_factory_ui.py:474: `_lost()`'s new `and not _only_time_wait(port)` branch is proved only by the existing socket test, which exercises it on Linux only. No test combines a refused bind with a stubbed table; the container run is the only proof.

Theme: tests
Paths: tests/test_factory_ui.py
Cost: S
Value: low
Raised by: 214-ci-green (correctness)

## [2026-11-21-41] [nit] the `_hand_digests()` fallback is untested.

Raised by the test review of 214-ci-green, round 1: tests/test_hand_gate.py:145: the `_hand_digests()` fallback is untested. It hashes a path holding a newline with sha256, and covers a failed `hash-object`.

Theme: tests
Paths: tests/test_hand_gate.py
Cost: S
Value: low
Raised by: 214-ci-green (correctness)

## [2026-11-21-42] [idea] Record an intent's `closes:` in the records ledger at `start`

Left undone by 215-evidence-exits, carried forward when it landed: Record the intent's `closes:` at `start` in the records ledger, and have `intent_closes()` read the union of it and the working copy (nit 2026-11-20-47, done right).
See .sdlc/work/215-evidence-exits/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-44] [nit] the `# fmt: skip` on the parametrize decorator exists only to keep the table on one line; a plain `ids=` list would format normally

Raised by the test review of 217-train-gates-every-tip, round 1: tests/test_train.py:1546: the `# fmt: skip` on the parametrize decorator exists only to keep the table on one line; a plain `ids=` list would format normally

Theme: style
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 217-train-gates-every-tip (correctness)
