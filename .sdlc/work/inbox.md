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

## [2026-11-19-20] [nit] R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone.

Raised by the test review of 169-decisions-and-stops-counted, round 1: tests/test_retro.py:2606: R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone. A test with `confirmed` or `settled` lines that outnumber the rest would fail if the denominator changed.

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 169-decisions-and-stops-counted (correctness)

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

## [2026-11-19-44] [nit] the docstring starts "179 R1", which cites the change by number; the rest of the repo's test docstrings name only the behaviour

Raised by the test review of 179-feature-inventory, round 1: tests/test_metrics.py:495: the docstring starts "179 R1", which cites the change by number; the rest of the repo's test docstrings name only the behaviour

Theme: style
Paths: tests/test_metrics.py
Cost: S
Value: low
Raised by: 179-feature-inventory (correctness)

## [2026-11-19-49] [nit] the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

Raised by the test review of 181-landing-nits-and-fixes, round 1: tests/test_land.py: the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

Theme: tests
Paths: tests/test_land.py
Cost: S
Value: low
Raised by: 181-landing-nits-and-fixes (correctness)

## [2026-11-19-51] [nit] no test pins that a line-1 shebang is left out of the comment count, though the plan records it as a departure

Raised by the test review of 178-comment-health, round 1: tests/test_comment_health.py: no test pins that a line-1 shebang is left out of the comment count, though the plan records it as a departure

Theme: tests
Paths: tests/test_comment_health.py
Cost: S
Value: low
Raised by: 178-comment-health (correctness)

## [2026-11-19-52] [nit] the `# 183` comments on the two new `places` entries add nothing, since git blame already says where they came from.

Raised by the code review of 183-spec-writer-nits-marker, round 1: tests/test_skills.py:1939: the `# 183` comments on the two new `places` entries add nothing, since git blame already says where they came from.

Theme: style
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 183-spec-writer-nits-marker (correctness)

## [2026-11-19-55] [nit] R5's test covers the eject path only.

Raised by the code review of 180-workarounds-tagged, round 1: tests/test_train.py: R5's test covers the eject path only. The same `problems.append(f"{name}: {problem}")` branch in `_train_stop` has no failing-append test.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 180-workarounds-tagged (correctness)

## [2026-11-19-56] [nit] the `unknown` rows carry a `change` key that no test asserts, and `unknown` has no `n`

Raised by the test review of 180-workarounds-tagged, round 1: tests/test_retro.py:3704: the `unknown` rows carry a `change` key that no test asserts, and `unknown` has no `n`

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 180-workarounds-tagged (correctness)

## [2026-11-19-57] [nit] add one assertion that a stop before any commit leaves no row, since the spec's edge-case section names it

Raised by the test review of 180-workarounds-tagged, round 1: tests/test_retro.py:3677: add one assertion that a stop before any commit leaves no row, since the spec's edge-case section names it

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 180-workarounds-tagged (correctness)

## [2026-11-19-62] [idea] One meaning per word across the docs, skills and messages

Contributors meet the same words with several meanings: "gate" is both the host's check command and
a person's approval at a WAIT (docs/FEATURES.md defines it as both); "check" is `[commands] check`
and check.sh, the acceptance checks in checks.md, and `sdlc.py check`, the artifact audit; "build"
is `stage: build`, the builder and its rounds, and `commands.build`, the slower gate. Proposed:
"gate" means only the host's commands (the code already says so: factory.py gate, gate.md); a
person's yes is an "approval" (the step, a WAIT); "acceptance checks" always keeps "acceptance";
`sdlc.py check` is "the audit" in prose; `commands.build` is "the slow gate" in prose. No command,
key or file is renamed (each would need a shim hosts must follow); only wording changes, and
docs/FEATURES.md's term test fails on a doc that uses a word in a meaning it no longer has.
Theme: docs
Raised 2026-11-19.

## [2026-11-19-63] [idea] Pass report_figures() to render_report() as one dict

Left undone by 184-scorecard-report, carried forward when it landed: `render_report()` now takes eight positional blocks and five keyword ones. One figures dict (`report_figures()`'s) passed whole would read better, but the tests' many `render_report(template, process)` calls would all change with it, so it stays out of 184.
See .sdlc/work/184-scorecard-report/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-64] [idea] Give response, autonomy and workarounds blocks a missing_because so scorecard rows name their real reason

Left undone by 184-scorecard-report, carried forward when it landed: A scorecard row whose block has no `missing_because` (response by tier, autonomy, the workarounds) says `none in the window` when null, even when the window held changes that just weren't measured: R5's rule as written. A per-row reason would need those blocks to carry one.
See .sdlc/work/184-scorecard-report/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-65] [nit] `_trend` compares the unrounded `value` with the `last` read back from the report's cell, which was written through `indicators.number`.

Raised by the code review of 184-scorecard-report, round 1: scripts/retro.py:423: `_trend` compares the unrounded `value` with the `last` read back from the report's cell, which was written through `indicators.number`. A figure that rounds to the same cell (for example 0.174 against a written 0.17) could read `up` when the person saw two equal numbers. Compare after rounding `value` the way the table writes it, or confirm `number()` writes full precision.

Theme: robustness
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 184-scorecard-report (correctness)

## [2026-11-19-66] [nit] `_minutes` rounds a median response to a whole number.

Raised by the code review of 184-scorecard-report, round 1: scripts/retro.py:433: `_minutes` rounds a median response to a whole number. The report above shows a median response of "1" minute in both tiers, so small values lose their trend resolution. This follows the spec's "integers" rule, so it is only worth a Note in REFERENCE.md.

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 184-scorecard-report (correctness)

## [2026-11-19-67] [nit] `test_the_pillar_sections_show_autonomy_pipeline_and_cost` checks the Speed pipeline terms as bare lowercase substrings ("gates", "bisections").

Raised by the test review of 184-scorecard-report, round 1: tests/test_retro.py: `test_the_pillar_sections_show_autonomy_pipeline_and_cost` checks the Speed pipeline terms as bare lowercase substrings ("gates", "bisections"). It would still pass if they appeared anywhere in the Speed section, such as in prose rather than the landing line. Match the landing line's label instead.

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 184-scorecard-report (correctness)

## [2026-11-19-68] [idea] Land skill description names the build at the tip and the approver's check judgement

Left undone by 185-landing-gates, carried forward when it landed: The land skill's frontmatter `description` still lists what a landing runs without the build at the tip or the approver's judgement of changed checks; Step 3 and the steps list say both. A wording pass on the description alone, kept out of this change.
See .sdlc/work/185-landing-gates/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-69] [idea] Landing records that an agent in the change's folder can't forge

Left undone by 185-landing-gates, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:2180: gate/build/accept records are trusted by the hash they state, which any agent that can write in the change's folder can write; a script-side signature or a record kept outside the tree would close it
See .sdlc/work/185-landing-gates/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-70] [nit] the edited factory paragraph has two lines over the file's ~100-column wrap (`change calls for it (build_due()).

Raised by the code review of 185-landing-gates, round 1: AGENTS.md:263: the edited factory paragraph has two lines over the file's ~100-column wrap (`change calls for it (build_due()). Landing, in …`, and `approver and the read-only list together, …`). Re-wrap them.

Theme: docs
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 185-landing-gates (correctness)

## [2026-11-19-71] [nit] `_train_begin` calls `_preflight` once per change at begin, as the spec says.

Raised by the code review of 185-landing-gates, round 1: plugins/factory/scripts/landing.py:1900: `_train_begin` calls `_preflight` once per change at begin, as the spec says. Where preflight can't be read, it records `checks: []` with a hash. This is safe, since every check then counts as changed, but a one-line comment saying so would help.

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 185-landing-gates (correctness)

## [2026-11-19-72] [nit] the docstring says a symlink out is refused "for a word naming an existing path"; say that a program walking the tree itself is not covered

Raised by the security review of 185-landing-gates, round 1: plugins/factory/scripts/landing.py:842: the docstring says a symlink out is refused "for a word naming an existing path"; say that a program walking the tree itself is not covered

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 185-landing-gates (contract)

## [2026-11-19-73] [nit] the R9 test drives a real train to `accept` and then edits `checks.md`.

Raised by the test review of 185-landing-gates, round 1: tests/test_train.py:2307: the R9 test drives a real train to `accept` and then edits `checks.md`. The edited command is `rm -f bb.txt`, which is off the list, so it never exercises the case where an edit passes R5 but loses the approver's clearance.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 185-landing-gates (correctness)

## [2026-11-19-74] [nit] GNU grep accepts unambiguous long-option prefixes, so `--der`/`--dereference` passes the exact `GREP_FOLLOWS_LONG` match and still follows symlinks while recursing; refuse any `--` word that is a prefix of `--dereference-recursive` (length ≥ 3), or refuse every grep long option not on a short allow-list

Raised by the security review of 185-landing-gates, round 2: plugins/factory/scripts/landing.py:876: GNU grep accepts unambiguous long-option prefixes, so `--der`/`--dereference` passes the exact `GREP_FOLLOWS_LONG` match and still follows symlinks while recursing; refuse any `--` word that is a prefix of `--dereference-recursive` (length ≥ 3), or refuse every grep long option not on a short allow-list

Theme: robustness
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: med
Raised by: 185-landing-gates (contract)

## [2026-11-19-75] [idea] test_train's by() should share _uv()'s offline fallback

Left undone by 186-gate-reliability, carried forward when it landed: `tests/test_train.py`'s `by()` runs `uv run --script` on a copy of the plugin at a new path, as the adoption tests did, so a gate with no network can fail it the same way. It could share the adoption tests' `_uv()` (offline from uv's cache, else a skip naming the network).
See .sdlc/work/186-gate-reliability/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-76] [nit] `"network was disabled" in cached.stderr` depends on uv's exact wording.

Raised by the code review of 186-gate-reliability, round 1: tests/test_adoption.py:65: `"network was disabled" in cached.stderr` depends on uv's exact wording. If a later uv words it differently, an offline run with an empty cache returns the failing result instead of skipping, so the gate goes red on the network again. Matching "offline" or "disabled" as well, or checking `--offline`'s non-zero exit more loosely, would be sturdier.

Theme: robustness
Paths: tests/test_adoption.py
Cost: S
Value: med
Raised by: 186-gate-reliability (correctness)

## [2026-11-19-77] [nit] `test_with_the_index_unreachable_a_copy_of_the_script_runs_from_uvs_cache` passes on the old code too.

Raised by the code review of 186-gate-reliability, round 1: tests/test_adoption.py:529: `test_with_the_index_unreachable_a_copy_of_the_script_runs_from_uvs_cache` passes on the old code too. It only fails once uv's cached index answers are stale, as the builder says. It shows the fallback works but isn't a regression guard.

Theme: tests
Paths: tests/test_adoption.py
Cost: M
Value: low
Raised by: 186-gate-reliability (correctness)

## [2026-11-19-78] [nit] the builder's note is right that it also runs `uv run --script` and could share `_uv()`.

Raised by the code review of 186-gate-reliability, round 1: tests/test_train.py: the builder's note is right that it also runs `uv run --script` and could share `_uv()`. Filed as a follow-up.

Theme: refactor
Paths: tests/test_train.py
Cost: M
Value: med
Raised by: 186-gate-reliability (correctness)

## [2026-11-19-79] [bug] A DECISION question that continues in sub-bullets is cut off and loses its options

When an agent's `- DECISION:` line continues its question in its own indented sub-bullets, with the
`- OPTION:` and `- WHY:` lines after them, `sub_lines()` stops at the first sub-bullet that is
neither. So `decisions.md` keeps only the question's first line, and the options are never read:
`ask` gives `options: []` and `why: null`, and `/sdlc-factory:decide` offers keep/change with a
truncated question. Expected: the whole question, with its options and why. To see it: 187's
builder raised D3 as "I reworded more than R7 and R9 list:" followed by three sub-bullets, and
the ledger and `ask 187` show only that line, with no options.

Severity: low
Paths: plugins/factory/scripts/factory.py
Introduced by: 137-approver-weighs-defaults
Theme: factory

## [2026-11-20-3] [bug] Close's elapsed goes negative when the local date is ahead of UTC

When close measures a change from history, it takes the change's `created:` date, which is the
local day, as midnight UTC (`datetime.combine(created, dtime(), UTC)` in `from_history`). On a
machine east of UTC, between local midnight and UTC midnight, a change created that local day
starts in the future, and `Sdlc-Totals: elapsed=` on its `Close` commit is negative. It should
measure from the local day's midnight in the machine's own timezone, never negative. To see it:
at UTC+8 between 00:00 and 08:00 local, run `pytest tests/test_archive.py -k
test_close_output_is_unchanged`. Four cases fail with `elapsed=-N`, so the gate is red for those
hours every day and ejects whatever lands then (it ejected 187 on 2026-11-20).

Severity: med
Paths: scripts/closing.py, tests/test_archive.py
Theme: metrics
