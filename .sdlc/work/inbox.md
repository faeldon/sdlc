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
Theme: style

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
Theme: landing

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

## [2026-11-20-15] [idea] Give the workarounds' `unknown` block its `n`, as `_workarounds()`'s docstring says

Left undone by 191-tests-paydown, carried forward when it landed: `retro.py`'s workarounds block gives `unknown` a `count` and `rows` but no `n`, though `_workarounds()`'s docstring says "each count carries its `n`" (nit 2026-11-19-56). That is a code change, and this change is tests-only, so its test pins the row's `change` key and leaves `n` alone.
See .sdlc/work/191-tests-paydown/notes.md in its commit.
Raised 2026-11-20.
Theme: retro

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
Theme: landing

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

## [2026-11-20-18] [idea] Narrow retro's tests.drifted to a test's own code and skip exact goldens

Left undone by 192-tests-pruning, carried forward when it landed: Retro's `tests.drifted` takes a test's code to be every code file its last change touched, so a test edited beside `sdlc.py` or `retro.py` drifts for good (`test_metrics.py`, `test_function_heat.py`), and an exact golden (`close-output.json`, `land-fix.txt`, `land-record-cases.json`) is named though it can't drift silently. A narrower notion of a test's code (the files it loads, or a host's list of goldens) would make the list worth acting on.
See .sdlc/work/192-tests-pruning/notes.md in its commit.
Raised 2026-11-20.
Theme: tests

## [2026-11-20-22] [nit] a read whose printed heading follows a blank line (the `## Speed` line in 189's report) is only covered by the one combined case, so a regression to the blank-line rule would show up only there

Raised by the test review of 196-evidence-and-deleted-conflicts, round 1: tests/test_evidence_headings.py:1: a read whose printed heading follows a blank line (the `## Speed` line in 189's report) is only covered by the one combined case, so a regression to the blank-line rule would show up only there

Theme: tests
Paths: tests/test_evidence_headings.py
Cost: S
Value: low
Raised by: 196-evidence-and-deleted-conflicts (correctness)

## [2026-11-20-24] [idea] Lead-time-by-way scorecard rows name their real reason

Left undone by 189-retro-insights, carried forward when it landed: The scorecard's lead-time rows by way still say `none in the window` when the window closed changes but none of that way (`test_a_figure_with_no_data_reads_a_dash_with_its_reason` pins it): R11 named four blocks, not `process.lead`'s ways. `no <way> change in the window` would match the escape rate's.
See .sdlc/work/189-retro-insights/notes.md in its commit.
Raised 2026-11-20.
Theme: retro

## [2026-11-20-25] [nit] the lead-time-by-way rows still say `none in the window` when the window closed changes but none of that way.

Raised by the code review of 189-retro-insights, round 1: .sdlc/work/189-retro-insights/notes.md: the lead-time-by-way rows still say `none in the window` when the window closed changes but none of that way. R11 named four blocks and not `process.lead`'s ways, so this is outside the spec. Ship will give it a disposition.

Theme: robustness
Paths: .sdlc/work/189-retro-insights/notes.md
Cost: S
Value: low
Raised by: 189-retro-insights (correctness)

## [2026-11-20-26] [nit] the `test_config_reports_the_insights_doc` "off while it doesn't exist" assertion only checks that no warning mentions INSIGHTS, so it is weak

Raised by the test review of 189-retro-insights, round 1: tests/test_retro.py:4867: the `test_config_reports_the_insights_doc` "off while it doesn't exist" assertion only checks that no warning mentions INSIGHTS, so it is weak

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 189-retro-insights (correctness)

## [2026-11-20-29] [nit] nothing pins the guard in `deleted_sides()` that a path staged as kept (present in the index, changed on one side and deleted on the other) is not treated as a deletion.

Raised by the test review of 197-moved-files-after-staging, round 1: tests/test_train.py: nothing pins the guard in `deleted_sides()` that a path staged as kept (present in the index, changed on one side and deleted on the other) is not treated as a deletion. Only the gone-from-index direction is tested.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: med
Raised by: 197-moved-files-after-staging (correctness)

## [2026-11-20-30] [nit] `_neither_side()` returns True when git can't hash a moved file, so a moved file that is gone from the tree counts as `carried`.

Raised by the test review of 197-moved-files-after-staging, round 1: tests/test_train.py: `_neither_side()` returns True when git can't hash a moved file, so a moved file that is gone from the tree counts as `carried`. No test covers that case.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 197-moved-files-after-staging (correctness)

## [2026-11-20-32] [nit] `_experience_text` does `table = _table(..., [[..., rating, before, ...]])`.

Raised by the code review of 190-retro-rating, round 1: scripts/retro.py:2425: `_experience_text` does `table = _table(..., [[..., rating, before, ...]])`. A `None` rating relies on `_table` rendering it as `—`. A test pins this, but the `—` spelling is implicit.

Theme: tests
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 190-retro-rating (correctness)

## [2026-11-20-33] [nit] `_last_experience` does `int(rating)` on the table cell.

Raised by the code review of 190-retro-rating, round 1: scripts/retro.py:2467: `_last_experience` does `int(rating)` on the table cell. A hand-edited report with a non-numeric cell would raise instead of reading back as no rating. Guard it, or catch `ValueError`.

Theme: robustness
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 190-retro-rating (correctness)

## [2026-11-20-34] [nit] `test_a_rating_with_no_line_says_so` takes a `tmp_path` fixture it never uses

Raised by the test review of 190-retro-rating, round 1: tests/test_retro.py: `test_a_rating_with_no_line_says_so` takes a `tmp_path` fixture it never uses

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 190-retro-rating (correctness)

## [2026-11-20-35] [idea] Say in the process doc when a batch of closed changes is released

Forty-four changes closed since the last retrospective and none was released: v1.10.0 is still the
latest tag. So `time_to_users` has nothing to measure (44 of 44 unreleased), and no change's
**Moves** line can be checked against a user. The process doc says nothing about when to cut a
release. Propose a cadence in it, for example a release after each batch the direction groups
(each wave), so a retrospective always has something its users have had. Raised by the
retrospective of 2026-11-20.
Theme: release

## [2026-11-20-36] [idea] An escalation whose only reason is an assumed default goes to the landing's question

The person kept the default the agents assumed 18 of 18 times this window (0 changed, n=18). Yet
an approver escalates a change while any default is open, so each such change stops once more, at
`/sdlc-factory:decide`, before the landing's own question confirms its assumed decisions anyway.
When the approver's only open reasons are assumed defaults, the change could be READY with them
shown in the landing's question, which already offers `its assumed decisions confirmed as shown`.
One stop less for most factory changes that raise one (O3). Raised by the retrospective of
2026-11-20.
Theme: autonomy

## [2026-11-20-37] [idea] See whether fewer changes at once shortens lead time

A factory change's lead time (median 166 minutes, n=33) is a quarter queued (0.25) and a fifth
waiting at ready (0.22), against 0.21 in agents. A median of 3.5 changes ran at once (most 6), and
the 32 that ran beside three or more others took a median 68.5 minutes elapsed, against 20 for the
4 that ran alone. Four is anecdote. Try one wave built with at most three changes open, and compare
its queued and ready-wait shares with this window's. Raised by the retrospective of 2026-11-20.
Theme: autonomy
Priority: low

## [2026-11-20-38] [idea] Run the approver on Sonnet for one window

Opus is 88% of the window's spend ($214.93 of $243.53). The approver runs on Opus at $16.07 over
43 runs and 23 minutes, and reads and decides without editing. One window with `[models] approver
= "sonnet"` in `.sdlc/factory.toml` would cost about a tenth as much. Use the approver's decisions
as the guardrail: READY changes that escaped, and ESCALATEs the person found empty. Raised by the
retrospective of 2026-11-20.
Theme: cost

## [2026-11-20-39] [idea] Check the surface's retire list before retiring anything on it

The surface's retire list names 33 config keys unused for 3 windows, among them `git.base` and
`git.push`. Every change reads `git.base`, and close pushes by `git.push`. So the measure counts
a key as used only when something other than the config loader records it. First make the
measure count what `load_config()` and the commands read. Then go through what is still listed:
the 7 `commands.*` keys, the 3 `metrics.*` keys, and the `docs.*` and `release.*` keys a host may
rely on. Raised by the retrospective of 2026-11-20.
Theme: retro

## [2026-11-20-41] [idea] Prune the slow train tests and the drifted ones

`tests.due` is true. The serial suite takes 2,452 seconds over 3,563 tests (median 0.17s). The
gate's round median doubled, from 86.5 to 158.5 seconds. These are the candidates:
- **Slow tests** (each 150× or more the median):
  - `test_train::test_every_ejection_names_its_cause` (39.8s)
  - `test_a_train_fix_already_made_goes_on_to_the_gate` (31.6s)
  - `test_a_train_stops_past_land_moves` (27.7s)
  - `test_a_killed_train_run_resumes` (27.4s)
  - `test_train_run_resumes_after_a_kept_change` (27.3s)
  - `test_train_run_ejects_a_gate_fault_and_lands_the_rest` (26.4s)
  - `test_train_run_lands_a_batch_of_three` (25.6s)
  - `test_land::test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone`
    (25.0s)

  Each builds a repo and a train of its own. A shared fixture, or one train walked through several
  checks, may cover the same ground.
- **Drifted tests** (code moved since, in that many later changes):
  - `tests/fixtures/close-output.json` (172, 8)
  - `tests/test_function_heat.py` (177, 8)
  - `tests/prompts/land-fix.txt` (181, 7)
  - `tests/prompts/land-checks.txt`, `tests/train_driver.py` (185, 4)
  - `tests/test_bugs.py`, `tests/test_next_up.py` (176, 4)
  - `tests/test_indicators.py`, `tests/test_surface.py` (184, 3)

The later change's review decides what to merge, rewrite, move or delete. Raised by the
retrospective of 2026-11-20.
Theme: tests

## [2026-11-20-42] [idea] Pay down the `tests` nits

26 `[nit]` entries are open in the `tests` theme, the oldest from 2026-11-19, past the process
doc's threshold of 5. 191 paid down 26 of them a day ago, and the landings since filed as many
again. Take them in one change, and see whether one fixture or helper would stop the commonest
kind of nit coming back. Raised by the retrospective of 2026-11-20.
Theme: tests

## [2026-11-20-43] [idea] Pay down the `robustness` nits

5 `[nit]` entries are open in the `robustness` theme, the oldest from 2026-11-19, at the process
doc's threshold of 5. Take them in one change. Raised by the retrospective of 2026-11-20.
Theme: robustness

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
