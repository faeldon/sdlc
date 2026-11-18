---
id: 156
slug: cases-that-tell
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 156 — The skills' cases tell what a skill did, and stop a landing only when you say so · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**Graders check outcomes, not which tool was used**

R1. A `tool_used` grader with `min` ≥ 1 can only name `Bash`, with an `input_match` for a command that only a shell runs: the plugin's script or git. A new test, `test_no_grader_insists_on_a_tool` in `tests/test_evals.py`, reads every `evals/*/graders/*.md`. It fails on any `tool_used` grader with `min` ≥ 1 that names `Read`, `Write`, `Edit`, `Glob` or `Grep`. Today it would fail on exactly two: `ship-behaviour/reads-behaviour` and `ship-behaviour/says-the-behaviour-check`.

R2. `ship-behaviour` grades the outcome rather than the route:
- `reads-behaviour` is removed.
- `says-the-behaviour-check` becomes an `llm` grader with `focus: trace`. It passes when, before the final question, the run's tool calls left `findings.md`'s note saying `Behaviour check: ran` or `Behaviour check: skipped, <why>`. A `Write`, an `Edit` and a shell write all count the same, and the skill's own text never counts as evidence.

`test_the_behaviour_case_reads_its_branch_and_says_it_ran` is rewritten to check this: type `llm`, `focus: trace`, the phrase `before its final question` (which `test_a_judgment_grader_reads_the_whole_reply` already requires), and Write, Edit and a shell command named as equal. It fails if `reads-behaviour` comes back.

R3. Every never-grader keeps `min: 0, max: 0`. These cover nothing committed, pushed or written before the yes, and the skill's own approved command never running. `test_a_stop_case_keeps_every_never_write_grader` and `test_the_never_graders_match_what_they_forbid` still pass unchanged.

**A run of the cases, in a change's scope**

R4. When a case's first run fails (score < 1) and the failure isn't from the environment (R8), `run-cases` reruns that case alone, once, inside the same call. The rerun is `claude plugin eval <evals> --case <name> --runs 1 --max-cost-usd <the cap less what the first run cost> … --output-dir <run>/rerun-<name>`. `test_a_failed_case_reruns_once_alone` fakes `subprocess.run` and checks:
- the second call carries `--case <name>` and no `--tag`;
- its ceiling is `5 − costUsd`;
- no third call is made, even if the rerun also fails.

R5. A case fails only when both of its runs fail. A case that fails and then passes is `passed on rerun`: it counts as passed and the run exits 0. `test_a_case_fails_only_twice` checks two sequences: fail→pass gives `failed: []`, `passed_on_rerun: [name]` and exit 0; fail→fail gives `failed: [name]` and exit 1.

R6. If the first run leaves no ceiling for a rerun (≤ 0), or the rerun stops at its ceiling (`plugin eval` exits 2), the case counts as failed and is marked `not rerun: the cost cap`. It is never quietly passed. A test covers both causes.

**A full run, as at release**

R7. A full run (`--full`, three runs per case, at most $20) never reruns anything. A case fails when two or more of its non-environment runs fail. A single failed run is shown in the case's verdict but doesn't fail it. `test_a_full_run_fails_a_case_on_two_runs` covers 0, 1 and 2 failures out of 3, and 2 environment runs plus 1 failure.

**Failures caused by the sandbox**

R8. A run is classed `environment` when it failed and its trace has `xcode-select: Failed to locate 'git'` in a tool result. Such a run:
- is never counted against the skill;
- is never rerun;
- is listed under `environment`.

A case whose every run is `environment` is neither passed nor failed. The trace is read the way a real one is laid out: the test's fixture, `tests/fixtures/eval-trace-no-git.jsonl`, is cut down from a kept trace's actual entries (`.sdlc/REVIEW.md`, *A transcript's shape assumed, not read*). `test_a_trace_that_could_not_start_git_is_environment` checks that such a run is `environment`, and that a trace with the marker only in the agent's own text, or a passing run with the marker, is not.

**Traces are kept for every failure**

R9. Every run passes `--keep-temp`. The trace (`tracePath`) of each failed or environment run is copied to `<run>/traces/<case>-<n>.jsonl` (`-rerun` for a rerun) and named in the output.

Without `--keep`, each run's temporary workspace is then removed, but only when it passes a guard: it is the nearest folder named `e-*` above `tracePath`, and that folder sits directly in the resolved system temp dir or the resolved `/tmp`. A path that fails the guard is left where it is and listed under `left`. `test_only_the_evals_own_workspace_is_removed` covers a workspace in temp, which is removed, and a `tracePath` outside temp, whose folder is left and listed. With `--keep`, nothing is removed.

**What a run reports**

R10. `run-cases` prints the following and writes the same into the run's `scope.json`:
- `verdicts`: for each case, its `result` (`passed`, `passed on rerun`, `failed`, `environment`) and its runs, each with its score, its failing graders (`name`, `explanation`, read from the run's `graders[]`) and its trace;
- `failed`, `environment` and `passed_on_rerun`;
- `note`: the exact findings line, `Skill evals: ran, <passed> of <cases>[; failed: <case>, …][; environment: <case>, …][; passed on rerun: <case>, …]; run: <run, as posix>`.

`passed` means `failed` is empty. `_run_summary()` takes `passed` and `failed` from `verdicts` when the record has them, and from `result.json` for runs made before this change, so `cases`, `status` and release read confirmed failures only. A test covers each source. The line still matches `CASES_RE` in both scripts (the pinned copies don't change).

**The factory's landing**

R11. `factory.py cases <NNN>` writes run-cases' `note` into `findings.md` when cases fail too, and exits 1. The note is never composed in two places. The test in `tests/test_land.py` that says "a failed case writes nothing" is turned around: a failed case writes its note once, and a rerun of the command replaces it.

R12. `factory.py cases <NNN> --skip <why>` writes `Skill evals: skipped, <why>` and runs nothing. It refuses an empty `<why>`, and a change whose note already says `ran`. A test covers the write and both refusals.

R13. `land_signals()` adds three signals, read from the change's note and its run's `scope.json`:
- `skills' cases failed: <case> (<grader>, …), trace in <run>`;
- `skills' cases hit the environment: <case>, …`;
- `skills' cases skipped: <why>`.

`test_a_failed_case_is_a_signal_not_a_refusal` checks that `land --by auto` is refused while one of these stands, and that `land --by person` lands a change whose note says `ran` with failures.

R14. `land` (`_land_readiness()`'s `before`) still refuses a change that has cases in scope and no `Skill evals:` line. It never refuses one whose note says `ran` with failures, or `skipped`. A test covers each case.

R15. `land_parts()`' `cases` part carries `failed`, `environment`, `skipped` and `run`. `land_shown()` lists each failed case with its failing graders and its trace folder. When any change has a failed or skipped case, `land_question()` adds the clause `its failed or skipped skills' cases accepted as shown`. A test checks both texts.

R16. The factory's `land` skill runs the cases before its WAIT (Step 1), as ship does. For each change with cases in scope and no `Skill evals:` line, it shows the scope and the $5 cap, then runs `factory.py cases <NNN>`. If the person declines that prompt, it runs `factory.py cases <NNN> --skip "<their reason>"`. Then it runs `land-check` again, so the question shows the results.

Neither command gets a rule in the skill's `allowed-tools`, so the harness asks before each one. A skip therefore always comes from the person. `test_skills.py` checks the bash blocks and rules as usual, and a new `test_no_skill_grants_the_cases` fails if any skill's `allowed-tools` grants `factory.py cases` or `sdlc.py run-cases`, and if `run-cases` appears in `ALLOW_RULES`.

**Ship and release**

R17. `skills/ship/cases.md`:
- each case in `failed` is still an **Important** finding, now with its failing graders and its trace's path as `Evidence:`;
- an `environment` or `passed on rerun` case is no finding, and the note says it;
- the note line is copied as `run-cases` printed it in `note`.

A test checks that `cases.md` names `note`, `environment` and `passed on rerun`.

R18. `_cases_report()` gains `full_history`: every full run, oldest first, with its date, Claude Code version, cost, and each case's score and verdict. `skills/release/SKILL.md` shows the last full run's verdicts beside the full run before it. Whether release offers the run at all is unchanged (see the open questions). `test_full_runs_are_kept_in_order` covers this.

**Docs**

R19. Three documents change:
- `docs/CONTRIBUTING.md` (*The skills' cases*) describes the rerun, the environment class, kept traces, `--skip`, and outcome-only graders, and drops "keeps each run's trace" from `--keep`, which now only keeps workspaces.
- `AGENTS.md` (*Writes before a WAIT*) names the factory's `cases` note as a write before `land`'s WAIT (see *Contracts touched*).
- `plugins/factory/README.md` changes wherever it describes the landing's cases.

## Design

**Taken as given, checked in the code:**
- `run-cases` is `cmd_run_cases()` in `scripts/sdlc.py`.
- `factory.py cases` wraps it (`cmd_cases()`), reads its JSON, and writes the note with `_note_line()`.
- `land` refuses through `_land_readiness()`'s `before` when there is no note. A failure blocks today only because `cmd_cases` writes nothing when cases fail.
- `result.json` has, per case, `arms.with[]`, and each run there has `score`, `passed`, `error`, `tracePath` (in `/private/tmp/e-*/out/`) and `graders[]` with `name`, `passed` and `explanation`. Read from `.sdlc/reports/cases-2026-11-18-16/result.json`.
- The grader types this repo uses are `tool_used` (one `tool` each), `regex` (`target: last_message`) and `llm` (`focus: trace`).
- `--case` takes one pattern per call (`cases_argv()`'s docstring).

**Taken as given, to check first in the plan:**
- Whether the CLI offers a grader that reads the workspace's final state, or a `tool_used` grader that takes several tools. If either exists, R2 uses it instead of the `llm` grader, which costs a judge call per run.
- How `--keep-temp` lays out its folders (R9's guard is written against the one `tracePath` seen).
- The shape of a trace's tool-result entries (R8), taken from a kept trace before any code reads it.

**`run-cases`** keeps its single entry point. After the first `plugin eval` call it reads `result.json` and works out each case's verdict, using a new pure helper, `case_verdicts(result, scope, traces)`. For a change's scope, each failed, non-environment case gets one rerun through `cases_argv()`, which gains an optional `case`: with a case set it passes `--case <name>` in place of `--tag` and a given ceiling. The remaining ceiling is `float(CASE_CAP["change"][1]) − result["costUsd"]`, rounded down to the cent.

The rerun's `result.json` goes in `<run>/rerun-<case>/` and is combined with the first run's in `case_verdicts`. Environment classification (`_environment_run(trace_path)`) reads the copied trace line by line, looking at tool results only, for the marker in `CASE_ENV_MARKERS`. Copying traces and removing workspaces happens in `_keep_traces(run, result, keep)` after each `plugin eval` call. Every write uses `newline="\n"`, every path shown is `as_posix()`, and the copy is a binary `shutil.copyfile`.

`compare_runs()` doesn't change. Its score columns still feed `cases compare` and the `fell` list. In `run-cases`' output, `failed` and `passed` now come from the verdicts.

**The note line** is composed once, in `sdlc.py` (R10). `factory.py` writes it as given, so the two scripts can't word it differently. Its `ran|skipped` opening stays readable by both copies of `CASES_RE`. `land_signals()` takes the run folder from the note's `run:` part and reads that run's `scope.json` for the failing graders. This is a copy of `sdlc.py`'s reading, pinned by a test, as with the factory's other copies. With no readable record, the signal still names the failed cases from the note alone.

**Landing order.** The factory's `land` skill now runs the cases in Step 1, before its WAIT, the same way ship runs them before its own. So the batch question shows each result, and a "yes" accepts a failure it has actually seen. The train's `before: cases` fallback stays, for a change whose cases somehow didn't run before the question. Cases never run a second time once they have run. This change lands before 153, which moves the landing code, so it edits `land_signals()`, `land_parts()`, `land_shown()` and `land_question()` where they are now.

**Edge cases:**
- A first run that writes no `result.json` is still `skipped` (R14 of the earlier change, unchanged).
- A rerun that writes no result leaves the case `failed`, marked `rerun wrote no result`.
- A case that fails both runs, one of them `environment`, counts as `environment` only if both runs are. Otherwise it is `failed`, since it failed the run that reached git.

**Not built here:** reporting the sandbox fault to Claude Code's tracker is the person's job, done by hand, outside this repo's code.

## Contracts touched

- **Writes before a WAIT (AGENTS.md). This change edits that rule.** The rule lists four named exceptions, and ship's `findings.md` is one of them because it "decides nothing". With R16, `factory.py cases` (and `--skip`) writes `findings.md`'s `Skill evals:` line before the factory `land` skill's WAIT. This is the same kind of write, and the same file and line ship writes before its own WAIT. But it is a new place, so `AGENTS.md`'s list grows to say so, in this change and on purpose. If you'd rather keep the list as it is, the alternative below (cases after the yes, and a failed change comes back to the next `/sdlc:land`) keeps it, at the cost of a second landing round for every failure.
- **Only a person runs a paid call.** `run-cases` stays out of `ALLOW_RULES`, every skill's `allowed-tools`, `check.sh` and CI. The rerun happens inside the call the person already approved, under the same `--max-cost-usd` total. `--skip` has no rule either, so the harness's prompt is the person's word for it (R16).
- **The skills' cases (`evals/`).** No command name contains `eval`. `--skip` is a flag on `cases`. `tests/test_evals.py` still builds every fixture and runs `check --strict`.
- **The factory.** `factory.py` never imports `sdlc.py`. It reads `run-cases`' JSON and the run's `scope.json`, with a pinned copy of the reading. No agent gains a tool. The person's gate is unchanged: a failed case is a signal, so `by=auto` can't land while one stands (R13).
- **A finding counted for the wrong reviewer (REVIEW.md).** A ship-side failure stays ship's own finding, with no `By:` line. The factory's failures are signals, not findings, so `Sdlc-Findings` counts don't move.
- **A transcript's shape assumed (REVIEW.md).** R8's fixture comes from a real trace.
- **The scripts run on Windows.** No new top-level imports, `newline="\n"` on every write, posix paths in output. The temp-workspace guard compares resolved paths. R9's test is `portable`.
- **Results are never hidden (intent's constraint).** A failure that is accepted stays in the note, which is committed with the change, and in the landing question.

## Alternatives rejected

- **Run cases after the landing's yes, and send a failure back to a second `/sdlc:land`.** This keeps *Writes before a WAIT* unchanged, but every failure costs another round and a new flag (`--accept-cases NNN=<run>`) passed through `train --begin`, just before 153 moves that code. It is kept as the fallback if you turn down the contract edit.
- **Let the yes accept failures in advance ("land even if a case fails").** That accepts a result nobody has seen, which the intent's constraint rules out.
- **Judge "wording only" in the script** (a diff that changes only prose in a skill's pass file). Pass files are all prose, and a single word in one changes what a skill does: the 150 edit that started this was one word. The person's decline at the prompt, written by `--skip` and named in the question, is the rule (open question 2).
- **Catch shell writes with a regex never-grader** (`>`, `tee`, `sed -i`). It would fail on `> /dev/null` and `2>&1`, which the skills run all the time. That is exactly the kind of false failure this change removes.
- **Rerun environment failures.** The stale xcrun cache doesn't fix itself within a run, so a rerun would spend money to confirm a sandbox fault.
- **A shim or a settings `env` entry to make git reachable in the sandbox.** Both were tried on 2026-11-18 and neither reached the agent's shell. The fix belongs to the sandbox, upstream.
- **Commit the full runs' scores into the repo** (for instance, with the release commit). That widens what `cmd_release` takes into its commit, which is safe only under `_release_refusals()`. The local `.sdlc/reports/` history that `full_history` reads is enough for "kept over time" on the machine that runs releases.
- **Rerun more than once, or for more runs.** Two runs separate a bad roll from a real break for the price of one more run. More runs is the full suite's job.

## Verification

```bash
./check.sh                                        # ruff, format, pytest -n auto, plugin validate: all green
uv run --group dev pytest -q tests/test_evals.py tests/test_land.py tests/test_factory.py tests/test_findings.py
uv run --group dev pytest -q -m portable          # the guard and record tests pass where Windows CI runs them
```

When healthy, the new tests named in R1–R18 pass, and the rewritten ones (R2, R11) pass in their new form. `test_no_grader_insists_on_a_tool` lists nothing.

One paid check, run by the person behind the harness prompt, once the change is built:

```bash
uv run --quiet --script scripts/sdlc.py run-cases 156   # ≤ $5
```

Healthy output:
- has `verdicts` for `ship`, `ship-open-finding` and `ship-behaviour`, the `note` line and `left: []`;
- has a `traces/` folder in the run only if a run failed;
- leaves no `e-*` folder from this run in `/tmp`.

If a case fails once and then passes, it shows as `passed on rerun` and the exit is 0.

