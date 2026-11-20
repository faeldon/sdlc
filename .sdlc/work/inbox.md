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

## [2026-11-19-69] [idea] Landing records that an agent in the change's folder can't forge

Left undone by 185-landing-gates, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:2180: gate/build/accept records are trusted by the hash they state, which any agent that can write in the change's folder can write; a script-side signature or a record kept outside the tree would close it
See .sdlc/work/185-landing-gates/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-73] [nit] the R9 test drives a real train to `accept` and then edits `checks.md`.

Raised by the test review of 185-landing-gates, round 1: tests/test_train.py:2307: the R9 test drives a real train to `accept` and then edits `checks.md`. The edited command is `rm -f bb.txt`, which is off the list, so it never exercises the case where an edit passes R5 but loses the approver's clearance.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 185-landing-gates (correctness)

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

## [2026-11-20-2] [nit] the phrasing fixture's `# fmt: skip` list packs several phrasings per line, which makes a future edit harder to read

Raised by the test review of 187-one-word-one-meaning, round 1: tests/test_feature_map.py:273: the phrasing fixture's `# fmt: skip` list packs several phrasings per line, which makes a future edit harder to read

Theme: tests
Paths: tests/test_feature_map.py
Cost: S
Value: low
Raised by: 187-one-word-one-meaning (correctness)

## [2026-11-20-4] [nit] the `east` fixture uses `time.tzset()`, which doesn't exist on Windows.

Raised by the code review of 188-local-day-elapsed, round 1: tests/test_archive.py:2500: the `east` fixture uses `time.tzset()`, which doesn't exist on Windows. That is fine as long as these tests stay unmarked `portable`, but a comment saying so would stop someone adding the marker later.

Theme: tests
Paths: tests/test_archive.py
Cost: S
Value: low
Raised by: 188-local-day-elapsed (correctness)

## [2026-11-20-5] [idea] The retrospective's Insights section (S15)

S15: The retrospective's Insights section — the synthesis questions in a guide file a host can
extend, each answered by a read-only sub-agent on its pillar's data, in the fixed answer shape.
After S14 (184, landed). From docs/RETRO-SCORECARD.md's seeds.
Theme: retro
Raised 2026-11-20.

## [2026-11-20-6] [idea] The person's experience at the retrospective (S16)

S16: The person's experience — one rating and one line asked at the retrospective's approval,
recorded in its report. A change to a WAIT, so Tier 2. After S14 (184, landed). From
docs/RETRO-SCORECARD.md's seeds.
Theme: retro
Raised 2026-11-20.

## [2026-11-20-14] [bug] The landing's resolve crashes on a modify/delete conflict

When a train stacks a change that deletes a file an earlier change in the train edited (or the
other way round), git stops the rebase with a modify/delete conflict (`UD`/`DU`). The train names
`resolve`, but `factory.py` raises `FileNotFoundError` on the deleted path before the resolver
agent starts. The loop stops there, with the change mid-rebase. Expected: the resolver is handed
the conflict like any other: which side deleted the file, what the other side changed, and where
that content now lives, so it can carry the edit across. To see it: on 2026-11-20, 193 added tests
to `tests/test_factory.py` and 194 deleted that file to split it; landing 193 then 194 stopped at
`resolve 194` with `FileNotFoundError: .../tests/test_factory.py`.

Severity: med
Paths: plugins/factory/scripts/factory.py, plugins/factory/scripts/landing.py
Introduced by: 139-landing-train
Theme: factory

## [2026-11-20-15] [idea] Give the workarounds' `unknown` block its `n`, as `_workarounds()`'s docstring says

Left undone by 191-tests-paydown, carried forward when it landed: `retro.py`'s workarounds block gives `unknown` a `count` and `rows` but no `n`, though `_workarounds()`'s docstring says "each count carries its `n`" (nit 2026-11-19-56). That is a code change, and this change is tests-only, so its test pins the row's `change` key and leaves `n` alone.
See .sdlc/work/191-tests-paydown/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-16] [nit] `UNCACHED`'s `offline` and `no solution found` are broad, so a script failure that happens to print "offline" would skip the test when it should fail.

Raised by the code review of 191-tests-paydown, round 1: tests/uv_run.py:17: `UNCACHED`'s `offline` and `no solution found` are broad, so a script failure that happens to print "offline" would skip the test when it should fail. The `--offline` run only gets here after the index was unreachable, which makes this unlikely, but a tighter match would cost little.

Theme: robustness
Paths: tests/uv_run.py
Cost: S
Value: low
Raised by: 191-tests-paydown (correctness)

## [2026-11-20-7] [idea] Read-only list refuses ugrep's symlink-following long options (`--dereference-files` and its prefixes)

Left undone by 193-ledger-and-landing-fixes, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:795: the grep refusals cover GNU grep and BSD grep only. If a host's `grep` on `PATH` is ugrep, `grep -r --dereference-files keep .` is allowed and follows links to files outside the checkout. This change didn't add or touch that gap, but it is in the same function. Fix: refuse `--dereference-files` and its prefixes too, or check every word against a list of such long options.
See .sdlc/work/193-ledger-and-landing-fixes/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-8] [nit] `by_alts` is built from every ledger entry with options.

Raised by the code review of 193-ledger-and-landing-fixes, round 1: plugins/factory/scripts/factory.py:2018: `by_alts` is built from every ledger entry with options. The match relies on options and why being identical, so a very short shared option list could merge two real decisions. D1 already accepts this trade-off.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 193-ledger-and-landing-fixes (correctness)

## [2026-11-20-9] [nit] the threshold `len(name) >= 5` counts the leading `--`, while the comment above `GREP_FOLLOWS_LONG` says "three or more characters after its `--`".

Raised by the security review of 193-ledger-and-landing-fixes, round 1: plugins/factory/scripts/landing.py:883: the threshold `len(name) >= 5` counts the leading `--`, while the comment above `GREP_FOLLOWS_LONG` says "three or more characters after its `--`". Writing it as `len(name) - 2 >= 3`, or naming the constant, would make the two read the same.

Theme: style
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 193-ledger-and-landing-fixes (contract)

## [2026-11-20-10] [nit] the third test chains its cases in one body, so a failure in the first assertion hides the later cases

Raised by the test review of 193-ledger-and-landing-fixes, round 1: tests/test_factory.py:870: the third test chains its cases in one body, so a failure in the first assertion hides the later cases

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 193-ledger-and-landing-fixes (correctness)

## [2026-11-20-11] [idea] Show a spec step and its elapsed time on a Designing card

Left undone by 195-designing-while-specified, carried forward when it landed: The board's step track (`_progress()`) shows nothing for a first spec draft, which records no `runs/step.md`; a card under Designing could show a `spec` step with its elapsed time.
See .sdlc/work/195-designing-while-specified/notes.md in its commit.
Raised 2026-11-20.

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

## [2026-11-20-17] [bug] A read whose output starts with "## " is flagged as missing its exit

`read_evidence()` in plugins/factory/scripts/factory.py ends a reply's `## Evidence` section at the
first line starting with `## `. A read that prints Markdown, such as a report or a doc, whose
first output line is a `## ` heading, therefore ends the section on its own output. The read is
then counted as having printed nothing, and is flagged "has no `exit:` line", though `is_read()`
accepts it. It costs a mend, and a second one stops the run. Expected: only a heading outside a
command's output ends the section, so a read that showed its output owes no exit. To see it:
189's builder ran `sed -n '/^## Insights/,/^## Speed/p' /tmp/rep189.md`, whose output begins
`## Insights`, and the run stopped at its second mend on 2026-11-20.

Severity: med
Paths: plugins/factory/scripts/factory.py
Introduced by: 123-evidence-reads
Theme: factory

## [2026-11-20-18] [idea] Narrow retro's tests.drifted to a test's own code and skip exact goldens

Left undone by 192-tests-pruning, carried forward when it landed: Retro's `tests.drifted` takes a test's code to be every code file its last change touched, so a test edited beside `sdlc.py` or `retro.py` drifts for good (`test_metrics.py`, `test_function_heat.py`), and an exact golden (`close-output.json`, `land-fix.txt`, `land-record-cases.json`) is named though it can't drift silently. A narrower notion of a test's code (the files it loads, or a host's list of goldens) would make the list worth acting on.
See .sdlc/work/192-tests-pruning/notes.md in its commit.
Raised 2026-11-20.
