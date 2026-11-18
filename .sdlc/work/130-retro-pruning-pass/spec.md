---
id: 130
slug: retro-pruning-pass
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 130 — Retro proposes a pruning pass over the test suite · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `[retro] test_times` is a new config key: a list of commands, `[]` by default, checked the same way `evidence` and `indicators` are (it joins `COMMAND_LISTS`). A string instead of a list is a warning, never a crash. `test_test_times_must_be_a_list_of_commands` (`tests/test_sdlc.py`, next to `test_evidence_must_be_a_list_of_commands`) fails without this.
2. R2. Only `sdlc.py retro` runs `retro.test_times`, and only through `_evidence()`. `check`, `status`, `config`, `readiness` and `retro --report` never run it. `test_nothing_but_retro_runs_test_times` (`tests/test_retro.py`) fails if any of those makes a `touch ran-times` marker. `retro_report()`, and so the committed report, stays as it is today: history only, no host command.
3. R3. `_evidence()` takes its limits as arguments. `evidence` and `indicators` keep 60 s and 20,000 characters. `test_times` gets `TIMES_TIMEOUT` (600 s) and `TIMES_LIMIT` (5,000,000 characters), because a suite's JUnit report runs to megabytes and a run that makes it can take minutes. `test_test_times_get_their_own_limits` monkeypatches all four constants and fails if a `test_times` row gets cut or timed out at the evidence limits. The existing `test_evidence_is_each_commands_output_and_never_a_raise` still passes unchanged.
4. R4. `indicators.junit_times(text)` is pure. It returns `{"cases": [...], "error": None}`, or `{"cases": [], "error": "<why>"}` for text that isn't XML or has no `<testcase>`, and it never raises. It reads every `<testcase>` at any depth, so `<testsuites>`, a bare `<testsuite>` and nested suites all work. Each case has:
   - `test`: `classname::name`, or `file::name` when there is no `classname`.
   - `file`: the `file` attribute, or `None`.
   - `seconds`: a float from `time`, or `None` when `time` is missing or isn't a number. It is never 0.
   - `skipped`: true when the case has a `<skipped>` child.

   Two tests fail without this: `test_junit_times_reads_every_testcase` (`tests/test_indicators.py`), which covers both root shapes, a missing `time` and a skipped case, and `test_junit_that_does_not_parse_is_an_error_not_a_raise`.
5. R5. `retro()["tests"]["times"]` has a `state`:
   - `unset`: no commands are configured.
   - `failed`: no command gave a case that parses. Each command's row says why: it exited non-zero, timed out, was `truncated` (cut XML counts as a failure, never as a partial read), or `junit_times` returned an error.
   - `ok`: at least one command gave cases. A failing command alongside working ones is still listed in `commands` with its `error`.

   With `ok` the block also holds:
   - `tests`, `skipped` and `untimed` counts.
   - `seconds`: the total over timed, non-skipped cases.
   - `median`.
   - `slowest`: the `TOP` (10) slowest, each with `test`, `file`, `seconds` and `share` of the total.
   - `slow`: the rows of `slowest` whose `seconds` are at least `SLOW_OVER` (10) × the median and at least `SLOW_LEAST` (1.0 s).

   Tests: `test_times_unset_failed_and_ok`, `test_a_truncated_report_is_a_failure_not_a_partial_read` and `test_slow_needs_ten_times_the_median_and_a_second` fail without this.
6. R6. The `tests` block never holds a command's raw output. Each row in `commands` keeps `command`, `exit`, `error`, `truncated` and `cases`, and drops `output`. `test_the_tests_block_stays_small_however_large_the_suite` feeds 5,000 test cases and fails if `json.dumps(out["tests"])` reaches 8,000 characters.
7. R7. `indicators.drifted_tests(lookback, kind, skip, present)` is pure. `lookback` is `[(change name, numstat rows)]`, oldest first.
   - A change touching more than `PAIR_FILES_MAX` files is left out, as `co_change()` already does.
   - For each tests-kind file T that the lookback touches, is still in `present`, and isn't `skip`ped: find the last change that touched T. Its partners are the code-kind files that change also touched. `later` is how many later changes touched a partner (all without T, since that was T's last touch).
   - T is drifted when `later >= DRIFT_LEAST` (3). Its row is `{file, last_change, code, later}`, where `code` holds the partners touched since, sorted and capped at 5.
   - Rows are sorted by `later` (highest first), then by file, and capped at `TOP`.

   Tests in `tests/test_indicators.py` fail without this:
   - `test_a_test_whose_code_moved_without_it_is_drifted`
   - `test_a_test_moved_with_its_code_is_not_drifted`
   - `test_a_deleted_test_is_never_drifted`
   - `test_a_change_too_large_to_pair_drifts_nothing`
8. R8. `retro()["tests"]["drifted"]` comes from the same lookback rows and `present` set the architecture pass reads, with no second walk over the 30 changes. It tells kinds the host's way (`retro.test_paths` included). It is `None` when there's no base branch, as `architecture` is. `test_drift_follows_the_hosts_test_paths` (a `checks/` file drifts once `test_paths = ["checks/"]` is set) and `test_no_base_branch_means_no_drift` fail without this.
9. R9. `retro()["tests"]["due"]` is true exactly when `slow` or `drifted` is non-empty. `UNMEASURED` gains two signals:
   - "a test a newer one repeats", which needs per-test coverage.
   - "a test that passes for the wrong reason", which needs mutation results.

   `test_due_is_slow_or_drifted` and `test_the_unmeasured_test_signals_are_listed` fail without this. `test_it_reports_every_key_and_writes_nothing` adds `"tests"` to its key set.
10. R10. The retrospective never edits or deletes a test. `sdlc.py retro` with `test_times` set leaves the tree as it found it. `test_retro_with_test_times_writes_nothing` runs `cat` on a committed JUnit fixture and compares `_state(root)` before and after. `retro-commit`'s existing stray-path refusal still refuses a changed test file. `test_retro_commit_refuses_a_changed_test_file` pins that for a `tests/` path.
11. R11. `skills/retro/SKILL.md` changes in three places:
    - Step 0 describes `tests`.
    - The process pass gives the pruning pass one finding when `tests.due`. Its disposition is one seed, never one per test. The seed names each candidate and why it is one: for `slow`, its seconds, share and multiple of the median; for `drifted`, its last change, the code that moved since and `later`.
    - Step 7 says `No test times, so the pruning pass rests on history alone: set retro.test_times to run it on run times too.` when `times.state` isn't `ok`.

    *Out of scope* gains "editing or deleting a test". The skill reads no test file for this: the JSON is the evidence. It gets no new bash command and no new rule. `test_the_retro_proposes_pruning_as_one_seed_and_edits_no_test` (`tests/test_skills.py`) fails if those phrases go. The existing skill invariants (one WAIT, every rule used) still pass.
12. R12. `docs/REFERENCE.md` covers the key in three places:
    - Its `[retro]` sample shows `test_times`.
    - Its list of commands `sdlc.py` runs itself names it.
    - *Retrospectives* describes the JUnit contract, the limits, the `tests` block and the pruning pass.

    `test_reference_names_test_times_and_its_format` fails without this.

## Design

**Taken as given, checked in the code.**
- `_evidence()` is the only place a host's retro commands run (`retro.py`, and AGENTS.md's *Retrospectives*).
- `retro_report()` deliberately runs no host command (its docstring), so `retro-commit` writes the report from history alone.
- `_architecture()` already reads the last `ARCH_LOOKBACK` closed changes oldest first (`closed_changes(...)[-ARCH_LOOKBACK:]`), plus each one's numstat rows and the base branch's `present` path set.
- `_kind(cfg)` is how retro tells tests from code.
- `indicators.py` is pure and holds `co_change()` and `PAIR_FILES_MAX`, the shape drift reuses.
- The skill already reads `unmeasured` and gives each finding a seed, intent or drop. Nits already set the precedent of one seed to pay a theme down.

**Where the run times come from: the host, as JUnit XML.** `retro.test_times` lists commands, and each prints a JUnit XML report on stdout. Most runners can write that format: pytest's `--junitxml`, jest-junit, go-junit-report, Maven Surefire, Gradle, cargo-nextest. The format says nothing about which runner made it, so the plugin learns nothing about the host's runner. The host decides how to get a report: run the suite, `cat` one its gate left, or fetch CI's artifact. The commands run through `_evidence(home, commands, timeout=TIMES_TIMEOUT, limit=TIMES_LIMIT)`. Only this call passes the larger limits, and the default arguments keep `evidence` and `indicators` exactly as they are. The rows go through `indicators.junit_times()`, and `_tests()` keeps each row's metadata but never its output.

**What history can show without a test-to-code map: drift.** Age alone isn't evidence, because an old test of stable code is fine. "A test whose code was rewritten" shows up in the history every retro already reads: the code files that changed alongside a test file, and how often they changed afterwards while the test didn't. That's `drifted_tests()`, which reads the lookback rows `_architecture()` already gathers. To avoid gathering them twice, `retro()` builds them once in a new `_lookback(home, trunk)`, which returns `(recent, rows, present)`, and passes them to both `_architecture()` and `_tests()`. `_architecture()`'s output stays the same.

**The block.** `retro()["tests"] = {"times": ..., "drifted": [...] | None, "due": bool}`. The `tests` key is the same with and without `--metrics`, because it holds only aggregates and at most 20 named rows. Constants `TIMES_TIMEOUT`, `TIMES_LIMIT`, `SLOW_OVER` and `SLOW_LEAST` live in `retro.py`. `DRIFT_LEAST` lives in `indicators.py`, next to `PAIR_LEAST`.

**The proposal and its record.** When `due` is true, the retro skill's process pass makes the pruning pass one finding, and its disposition is one seed. The seed lists every candidate with its numbers. Because the seed is approved at the retro's existing WAIT and appended to the register, the `Retrospective YYYY-MM-DD` commit records the evidence it rests on, as the intent asks. Retro-commit's allow-list doesn't change. Pruning itself is a later change, opened with `/sdlc:intent` from that seed. Its edits get ship's review, so the retrospective never touches a test.

**Edge cases.**
- No commands: `state: unset`, and drift still runs.
- A command's XML gets cut at the limit: `failed` for that command, never a partial read.
- Several commands, such as a monorepo's suites: their cases are pooled. Duplicate ids stay as separate rows.
- Skipped cases are counted and never timed.
- A case with no `time` is counted as `untimed`.
- A test file deleted on the base branch never drifts, because `present` drops it.
- A mass rename or reformat (more than 50 files) pairs nothing.
- No base branch: `drifted` is `None`.
- `ElementTree` parses the host's own command output. Recent Python bundles an expat that refuses entity expansion attacks, and this input is as trusted as `evidence` already is.

**Files.**
- `scripts/sdlc.py`: `CONFIG_KEYS["retro"]["test_times"]` and `COMMAND_LISTS`.
- `scripts/retro.py`: `_evidence` arguments, `_lookback`, `_tests`, `UNMEASURED`, the key in `retro()`.
- `scripts/indicators.py`: `junit_times`, `drifted_tests`, and its docstring's list.
- `skills/retro/SKILL.md`.
- `docs/REFERENCE.md`.
- Tests in `tests/test_retro.py`, `tests/test_indicators.py`, `tests/test_sdlc.py` and `tests/test_skills.py`.

At ship, `AGENTS.md`'s *Retrospectives* line ("runs the host's `retro.evidence` and `retro.indicators`") gains `retro.test_times`. It is a context doc, so `sdlc.py context` lists it.

## Contracts touched

- **Retrospectives: read-only but for its report; the commit holds the direction doc, the register, the product doc and the report, nothing else.** The design stays inside this. `retro` writes nothing (R10), and the pruning proposal reaches history only as an approved seed in the register. `cmd_retro_commit`'s allow-list is unchanged, and its stray refusal is pinned for a test file.
- **`_evidence()` is the only place retro's host commands run.** `test_times` runs there too (R2). Only its limits are new arguments, and the defaults keep today's behaviour. AGENTS.md's sentence naming the keys is updated at ship.
- **`metrics.py` and `indicators.py` are pure.** `junit_times()` and `drifted_tests()` take text and rows. They import only the stdlib (`xml.etree.ElementTree`), run no subprocess and don't import `sdlc.py`.
- **The plugin knows nothing about a host's runner (Mechanism vs. policy).** JUnit XML is a report format, and the host names the command. Nothing here parses `pytest` output or names a runner in code.
- **`breaking` / `RETIRED_KEYS` / `TEMPLATE_READS` (Setup).** A new optional key is neither a rename nor a removal, and no template heading is read. Nothing under `defaults/`, `templates/` or `guide/` changes, so `.sdlc/setup.json` needs no `record`, and the irreversible paths aren't touched.
- **Skills invariants.** Retro keeps exactly one WAIT and gains no bash command, so `allowed-tools` doesn't change. The text added to `SKILL.md` is prose only.
- **The scripts run on Windows.** No new subprocess call is added: the commands go through `_evidence()`'s `_sh` with `encoding="utf-8", errors="replace"`. No platform module is imported, and `xml.etree` is portable. The new `indicators` tests are pure and can be marked `portable`.
- **Nothing about a project.** The JUnit fixtures use neutral ids (`tests/test_drafts.py::test_reopen`).
- **Metrics trailers.** Untouched: run times never go into a `Close` commit.

No invariant needs to move.

## Alternatives rejected

- **Parsing pytest's `--durations` output.** It's one runner's text, so the plugin would have to know the host's runner, which the intent's contracts rule out.
- **A plain `<seconds> <test id>` line format.** Every host would have to write a converter. JUnit XML is what runners already produce.
- **A `retro.test_report` path to a JUnit file.** A gate runs in a change's worktree or the factory's, so its file never reaches the main checkout where retro runs. A stale file would also be read silently. A command covers the file case (`cat`) and the fresh case (run the suite) alike.
- **Timing tests at close or in `sdlc.py gate`.** Runner output would have to be parsed per change, and thousands of test names would bloat trailers that hold only numbers and names. The suite's shape is a retrospective question, not a per-change one.
- **A test-to-code map from per-test coverage.** No host records one today, and coverage contexts are tool-specific. Co-change history gives "its code moved, it didn't" for any language, from data retro already reads.
- **Age or blame alone.** An old test of stable code is healthy, so a list ranked by age would mostly be noise.
- **A seed per candidate.** It would flood the register. One seed pays the pass down in one change, as nits do.
- **A `## Tests` section in the committed report.** The report is written at `retro-commit` from history alone. Running a host command there would run it twice, and could commit numbers that differ from what the person approved. The approved seed already carries the evidence.
- **Retro opening the pruning intent, or editing tests.** This is ruled out by the intent's constraint and the skill's rule that it never edits code.
- **Skipped tests as candidates.** Platform skips, such as Windows-only tests on a Mac, are legitimate and would be noise. They're counted only.
- **Detecting duplicate tests and tests that pass for the wrong reason.** That needs per-test coverage or mutation results, so both go into `unmeasured` (R9) rather than being guessed at.

## Verification

- `./check.sh`: ruff, the format check, `pytest -n auto` and both `claude plugin validate --strict` runs exit 0.
- `uv run --group dev pytest -q tests/test_indicators.py tests/test_retro.py tests/test_skills.py tests/test_sdlc.py -k "junit or drift or test_times or tests_block or due or unmeasured or pruning or every_key"`: all pass. Every R1–R12 test named above is collected.
- `uv run --group dev pytest -q -m portable`: passes, the new pure `indicators` tests included.
- This repo's suite as a real fixture:
  1. Run `uv run --group dev pytest -q -n auto --junitxml=/tmp/sdlc-130-junit.xml`.
  2. Load `scripts/indicators.py` by path in `uv run --group dev python` and call `junit_times()` on that file.
  3. It is healthy when `error` is `None` and the case count matches pytest's summary (about 2,336). Skipped ones are counted, and the slowest cases are the adoption and bare-repo tests.
- `git status --porcelain` in the worktree after the above shows only the change's own edits. No test file is touched by anything that ran.

