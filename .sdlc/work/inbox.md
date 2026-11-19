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

## [2026-11-18-79] [nit] the test takes about 49s here, mostly waiting on the poll interval.

Raised by the test review of 152-board-drawer-browser-test, round 1: tests/test_board_browser.py:98: the test takes about 49s here, mostly waiting on the poll interval. A shorter bounded wait or a faster poll in the fixture would speed up `./check.sh`

Theme: tests
Paths: tests/test_board_browser.py
Cost: M
Value: low
Raised by: 152-board-drawer-browser-test (correctness)

## [2026-11-18-88] [idea] Pay down the tests nits in one change

Five `[nit]` entries are open under `tests` (2026-11-18-64, -70, -71, -79 and -85), which is the threshold the process guide sets for paying a theme down. Two of them are slow polls in the train's kill test (-71 and -79, about 49 seconds here). One change takes all five, and its review decides each.
Theme: tests
Raised by the retrospective of 2026-11-18.

## [2026-11-18-90] [idea] A pruning pass over the tests that drifted

Retro's `tests.drifted` names ten test files whose code moved without them over the last 30 changes:
- the board fixture `012-draft-publish` (seven files), last touched by 133, while `factory.py`, `board.py` and `board.html` changed in 17 later changes;
- `tests/test_config_resolution.py` and `tests/test_indicators.py`, last touched by 130, with 17 later changes;
- `tests/test_adoption.py`, last touched by 134, with 16 later changes.

A later change looks at each one again (merge, rewrite, move or delete it), and its review decides. There are no run times to weigh, because `retro.test_times` is unset.
Theme: tests
Raised by the retrospective of 2026-11-18.

## [2026-11-18-93] [idea] The review doc names a doc's claim left false by the change

Five changes' Important findings share one class: a context or reference doc still states a rule the change altered, or one place restates a rule changed in another. These are 072 F1, 077 F1, 127 F1, 128 F1 and F2, and 130 F1, and all were fixed before landing. The proposed bullet for `.sdlc/REVIEW.md`, *The ways this repo's code fails*:

- **A doc's claim the change made false.** A sentence in `AGENTS.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md` or a README that names the function, the command or the rule this diff changed, and still says what it did before. Grep the docs for each name the diff touches.
Theme: review
Raised by the retrospective of 2026-11-18.

## [2026-11-18-99] [idea] Clear the eval workspaces left in /tmp by earlier case runs

Left undone by 156-cases-that-tell, carried forward when it landed: 26 `e-*` workspaces from earlier case runs sit in `/private/tmp` (made before runs removed their own); a one-off `run-cases --prune` or a line in CONTRIBUTING could clear them, behind the same `_workspace_of()` guard
See .sdlc/work/156-cases-that-tell/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-101] [nit] the workspace test chmods to 0 and then restores in `finally`.

Raised by the test review of 156-cases-that-tell, round 1: tests/test_evals.py:523: the workspace test chmods to 0 and then restores in `finally`. A failure partway through could leave `outside` unreadable for pytest's tmp cleanup.

Theme: tests
Paths: tests/test_evals.py
Cost: S
Value: low
Raised by: 156-cases-that-tell (correctness)

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

## [2026-11-18-109] [nit] `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so).

Raised by the test review of 160-command-registry, round 1: tests/test_registry.py:104: `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so). It guards R7 and would catch a later regression, but it never failed on the old code. Only the `config` command is stubbed, so an adapter that bound its handler at import time would be caught for that one command and no other. Stubbing one more, such as `status` with the default no-command path, would cover R5's `--all` default through `main()`.

Theme: tests
Paths: tests/test_registry.py
Cost: S
Value: low
Raised by: 160-command-registry (correctness)

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

## [2026-11-19-7] [nit] a few helper names such as `_reached` and `_named` have no docstring

Raised by the test review of 163-factory-records-reader, round 1: tests/test_modules.py: a few helper names such as `_reached` and `_named` have no docstring

Theme: tests
Paths: tests/test_modules.py
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)

## [2026-11-19-11] [nit] `_bare_repo` creates a repo with no `user.name` or `user.email`.

Raised by the test review of 167-board-knows-its-repo, round 1: tests/test_board.py:660: `_bare_repo` creates a repo with no `user.name` or `user.email`. It passes on this machine, but may fail on a clean CI box. Reuse the `repo` fixture's git config if it sets one.

Theme: tests
Paths: tests/test_board.py
Cost: S
Value: low
Raised by: 167-board-knows-its-repo (correctness)

## [2026-11-19-6] [nit] the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable.

Raised by the code review of 163-factory-records-reader, round 1: tests/test_board.py: the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable. It was a comparison of two copies, and with one copy it would compare the module with itself. `LAND_STOPS` still has no factory twin, so nothing checks it against the factory. It is only pinned against `LAND_STEPS` through the board's `LAND_AT` test.

Theme: tests
Paths: tests/test_board.py
Cost: S
Value: low
Raised by: 163-factory-records-reader (correctness)

## [2026-11-19-13] [idea] Break retro throughput down by work class

Left undone by 168-work-mix-and-follow-through, carried forward when it landed: `docs/RETRO-SCORECARD.md` *Supporting: throughput* still says "by impact S2": the work classes now exist, but throughput isn't broken down by them. A later change (S14's report, or its own) can add `process.throughput` by `work` class.
See .sdlc/work/168-work-mix-and-follow-through/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-14] [idea] Teach _milestone_verdicts() that a seed retired by inbox-commit is dropped, not vanished

Left undone by 168-work-mix-and-follow-through, carried forward when it landed: Follow-through's milestone `done` by grouped rows reads `_milestone_verdicts()` against the current register, so a grouped seed retired with `inbox-commit` reads `vanished` there (and the milestone `carried`), while the same seed scored as a seed reads `dropped`. Teaching `_milestone_verdicts()` about `Retire` subjects would change what `direction.milestones` reports, which the spec's boundaries say asks first.
See .sdlc/work/168-work-mix-and-follow-through/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-15] [nit] `_is_process` also skips `.sdlc/setup.json` (`sdlc.MANIFEST`), which R3 doesn't list.

Raised by the code review of 168-work-mix-and-follow-through, round 1: scripts/retro.py:377: `_is_process` also skips `.sdlc/setup.json` (`sdlc.MANIFEST`), which R3 doesn't list. The path is under `.sdlc/` anyway. The skip only stops a change that touched just `setup.json` from counting as process work. REFERENCE.md says so, but the spec doesn't. Drop the skip or add it to the spec.

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 168-work-mix-and-follow-through (correctness)

## [2026-11-19-17] [nit] `test_retro_and_its_report_show_the_same_figures` compares only work mix and time to users with the report, and has no assertion on the follow-through sentence.

Raised by the test review of 168-work-mix-and-follow-through, round 1: tests/test_retro.py:2126: `test_retro_and_its_report_show_the_same_figures` compares only work mix and time to users with the report, and has no assertion on the follow-through sentence. The spec asks that the report and the JSON not disagree. The other test checks the report text, but follow-through is checked only in the JSON tests.

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: med
Raised by: 168-work-mix-and-follow-through (correctness)

## [2026-11-19-18] [nit] R14 (the docs) has no test, as the spec says.

Raised by the test review of 168-work-mix-and-follow-through, round 1: tests/test_retro.py: R14 (the docs) has no test, as the spec says. Nothing here checks that `REFERENCE.md` and the retro skill's Step 0 name the three keys.

Theme: docs
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 168-work-mix-and-follow-through (correctness)

## [2026-11-19-19] [nit] `autonomy_counts` counts a ledger line with the `SUPERSEDED` and `SETTLED` marks under `defaults` only.

Raised by the code review of 169-decisions-and-stops-counted, round 1: scripts/factory_records.py:643: `autonomy_counts` counts a ledger line with the `SUPERSEDED` and `SETTLED` marks under `defaults` only. A superseded or settled blocking or look line gets no such check. It falls under answered or checked, which is probably right, since the approver settles defaults only. A one-line comment would make that explicit

Theme: docs
Paths: scripts/factory_records.py
Cost: S
Value: low
Raised by: 169-decisions-and-stops-counted (correctness)

## [2026-11-19-20] [nit] R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone.

Raised by the test review of 169-decisions-and-stops-counted, round 1: tests/test_retro.py:2606: R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone. A test with `confirmed` or `settled` lines that outnumber the rest would fail if the denominator changed.

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 169-decisions-and-stops-counted (correctness)

## [2026-11-19-21] [nit] `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

Raised by the security review of 170-trust-band, round 1: scripts/retro.py:384: `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

Theme: robustness
Paths: scripts/retro.py
Cost: S
Value: med
Raised by: 170-trust-band (contract)

## [2026-11-19-23] [nit] `_killed_at_its_gate` waits up to 120 s for the gate to start, while the POSIX test it twins waits 60 s; neither is a defect, but the two differ for no stated reason

Raised by the test review of 171-factory-run-state, round 1: tests/test_train.py:1830: `_killed_at_its_gate` waits up to 120 s for the gate to start, while the POSIX test it twins waits 60 s; neither is a defect, but the two differ for no stated reason

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 171-factory-run-state (correctness)

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

## [2026-11-19-26] [nit] `measure.errors` holds the raw exception text.

Raised by the security review of 172-close-in-steps, round 1: scripts/closing.py:396: `measure.errors` holds the raw exception text. In the plugin's own repo, a child after a handoff passes it up unchanged. It's local stdout only, but if a future reader of the run files puts a path or a line of content in a message, that text lands in close's report, so say in the docstring that the message is meant for the person running close and must never become a trailer

Theme: docs
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 172-close-in-steps (contract)

## [2026-11-19-27] [idea] Rewrap the remaining factory agents' prose lines past 100 columns

Left undone by 173-style-paydown, carried forward when it landed: The other factory agents (`approver.md`, `builder.md`, `resolver.md`, `reviewer-behaviour.md`, `reviewer-security.md`, `reviewer-test.md`, `reviewer-ui.md`, `spec-writer.md`, `verifier.md`) keep prose lines past 100 columns; no entry named them, so they stayed out of this change.
See .sdlc/work/173-style-paydown/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-28] [nit] the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

Raised by the test review of 173-style-paydown, round 1: plugins/factory/agents/reviewer-test.md:13: the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

Theme: docs
Paths: plugins/factory/agents/reviewer-test.md
Cost: S
Value: low
Raised by: 173-style-paydown (correctness)

## [2026-11-19-29] [nit] the first check covers only the seven named files, so a rewrap that regressed another agent file would not be caught; fine for this scope

Raised by the test review of 173-style-paydown, round 1: .sdlc/work/173-style-paydown/checks.md: the first check covers only the seven named files, so a rewrap that regressed another agent file would not be caught; fine for this scope

Theme: tests
Paths: .sdlc/work/173-style-paydown/checks.md
Cost: S
Value: low
Raised by: 173-style-paydown (correctness)

## [2026-11-19-33] [idea] Figures by way of building

Scorecard S9: lead time, throughput, cost and escape rate, factory against by hand. Pillars:
Speed, Autonomy.
Theme: retro
Raised 2026-11-19.

## [2026-11-19-34] [idea] Pipeline and risk figures

Scorecard S10: gate seconds and slot-wait trend, red-gate rate, train figures (gates, ejections,
bisections, base moves, accept stops, conflicts), mends, full-depth share, unreviewed landings.
Pillars: Speed, Quality.
Theme: retro
Raised 2026-11-19.

## [2026-11-19-35] [nit] `_cost()` runs once in `retro()` and again in `retro_report()`, and each run re-reads every change's commit.

Raised by the code review of 174-waste-tagged, round 1: scripts/retro.py:1752: `_cost()` runs once in `retro()` and again in `retro_report()`, and each run re-reads every change's commit. Computing it once per `retro` call would halve the git reads.

Theme: refactor
Paths: scripts/retro.py
Cost: M
Value: low
Raised by: 174-waste-tagged (correctness)

## [2026-11-19-36] [nit] if `claude` returns no figures, no row is written, so a run that failed that way doesn't make the next try a `rerun`.

Raised by the code review of 174-waste-tagged, round 1: plugins/factory/scripts/factory.py:4392: if `claude` returns no figures, no row is written, so a run that failed that way doesn't make the next try a `rerun`. This matches R3 as worded. A line in the `purpose_of()` docstring would say so.

Theme: docs
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 174-waste-tagged (correctness)

## [2026-11-19-37] [nit] R1's `land` field is never asserted on a row written by `cmd_agent` for a landing task.

Raised by the test review of 174-waste-tagged, round 1: tests/test_factory.py: R1's `land` field is never asserted on a row written by `cmd_agent` for a landing task. `purpose_of` is tested for it, but no test runs a `land-review` through `cmd_agent` and checks the row carries `land`.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 174-waste-tagged (correctness)

## [2026-11-19-38] [nit] the stop half of `test_an_ejection_is_recorded_and_amended_in` doesn't check `at` or `land` on its rows.

Raised by the test review of 174-waste-tagged, round 1: tests/test_train.py: the stop half of `test_an_ejection_is_recorded_and_amended_in` doesn't check `at` or `land` on its rows. Only `cause` is asserted.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 174-waste-tagged (correctness)

## [2026-11-19-39] [idea] Reject indicator names and units that don't read back from the report

Left undone by 177-indicators-structured, carried forward when it landed: A `unit` that is literally `—`, or a `name` or `unit` with leading or trailing spaces, is accepted by `host_rows()` but reads back from the report as a different key (`""`, or stripped), so it gets no `last`. R1 doesn't forbid either; rejecting them would be a one-line rule in `host_rows()` if it ever matters.
See .sdlc/work/177-indicators-structured/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-40] [nit] R2's OSError case has no test; `_indicator_rows` treats it like the timeout path

Raised by the test review of 177-indicators-structured, round 1: tests/test_retro.py:1957: R2's OSError case has no test; `_indicator_rows` treats it like the timeout path

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 177-indicators-structured (correctness)

## [2026-11-19-41] [nit] the factory paragraph's reflowed line runs past 100 columns (`` `surface` (`COMMAND_RE`), never running … ``); rewrap it like its neighbours

Raised by the code review of 179-feature-inventory, round 1: AGENTS.md:253: the factory paragraph's reflowed line runs past 100 columns (`` `surface` (`COMMAND_RE`), never running … ``); rewrap it like its neighbours

Theme: style
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-42] [nit] `_surface_at` calls `COMMAND_RE.findall` on `sdlc.py` at a tag that predates the `@command` registry.

Raised by the code review of 179-feature-inventory, round 1: scripts/retro.py:1768: `_surface_at` calls `COMMAND_RE.findall` on `sdlc.py` at a tag that predates the `@command` registry. It returns `commands: None` only because `core` is empty, which is the intended behaviour, but it's implicit. A short comment would say so

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-43] [nit] `_retire` stops walking back once every item is decided, so `retire.windows` can be below `RETIRE_AFTER` while no candidate is hidden.

Raised by the code review of 179-feature-inventory, round 1: scripts/retro.py:1715: `_retire` stops walking back once every item is decided, so `retire.windows` can be below `RETIRE_AFTER` while no candidate is hidden. REFERENCE.md could say `windows` is the windows actually read

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-44] [nit] the docstring starts "179 R1", which cites the change by number; the rest of the repo's test docstrings name only the behaviour

Raised by the test review of 179-feature-inventory, round 1: tests/test_metrics.py:495: the docstring starts "179 R1", which cites the change by number; the rest of the repo's test docstrings name only the behaviour

Theme: style
Paths: tests/test_metrics.py
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-45] [idea] Board drawer focus test is flaky under a loaded gate

Left undone by 181-landing-nits-and-fixes, carried forward when it landed: `tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card` failed in 181's round-1 gate with no error in the record's tail, and passed when rerun alone: likely flaky under a loaded gate. Not this change's code.
See .sdlc/work/181-landing-nits-and-fixes/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-46] [idea] Adoption tests fail the gate when offline; skip or cache uv's deps

Left undone by 181-landing-nits-and-fixes, carried forward when it landed: `tests/test_adoption.py` needs network (uv fetches PyPI deps for `uv run --script`); a gate with no DNS fails two of its tests. A skip or cache when offline would keep the gate about the code.
See .sdlc/work/181-landing-nits-and-fixes/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-47] [nit] the refusal message is long and repeats `FIX: ALREADY MADE`

Raised by the code review of 181-landing-nits-and-fixes, round 1: plugins/factory/scripts/landing.py:1420: the refusal message is long and repeats `FIX: ALREADY MADE`

Theme: style
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 181-landing-nits-and-fixes (correctness)

## [2026-11-19-48] [nit] `taken_lines()` counts every indented line after a `Nits taken in:` line as part of it, so an indented sub-bullet that names an id to say it's left out would retire that nit.

Raised by the security review of 181-landing-nits-and-fixes, round 1: plugins/factory/scripts/factory.py:4699: `taken_lines()` counts every indented line after a `Nits taken in:` line as part of it, so an indented sub-bullet that names an id to say it's left out would retire that nit. Only the change's own author can write this, and the intent asked for an explicit marker, so the risk is low. Stopping continuation at a line that starts a new `-` bullet would tighten it

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 181-landing-nits-and-fixes (contract)

## [2026-11-19-49] [nit] the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

Raised by the test review of 181-landing-nits-and-fixes, round 1: tests/test_land.py: the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

Theme: tests
Paths: tests/test_land.py
Cost: S
Value: low
Raised by: 181-landing-nits-and-fixes (correctness)

## [2026-11-19-50] [bug] The factory's spec-writer doesn't write a `Nits taken in:` line

Since 181, a landing retires a nit only when its id is on a `Nits taken in:` line in the intent's
Approach or the spec's Requirements. 181 taught skills/intent, skills/intent/batch.md, skills/spec
and the land skill to write that line, but not the factory's spec-writer: neither
plugins/factory/agents/spec-writer.md nor plugins/factory/prompts/spec.md mentions it. Seen on 175:
its draft took in nits 2026-11-19-19 and -21 in R13 and R14 by prose only, so its landing would
have left both open; caught by hand and revised. Expected: the spec-writer puts every nit the spec
takes in on a `Nits taken in:` line in its Requirements.

Severity: low
Paths: plugins/factory/agents/spec-writer.md, plugins/factory/prompts/spec.md
Introduced by: 181-landing-nits-and-fixes
Theme: landing
