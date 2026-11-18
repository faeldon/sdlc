I've built all of 156 (R1–R19), test first. The gate is green: 2890 passed, 28 skipped. Everything is left uncommitted; `git rm` staged the deleted grader, and nothing else is staged.

**What was checked first**
- **Grader types:** no grader reads the workspace's final state, and `tool_used` takes one tool. So R2 uses an `llm` grader with `focus: trace`, as the spec says.
- **`--keep-temp` layout:** traces sit at `/private/tmp/e-<id>/out/trace.jsonl`. The `e-*` folder is `dr-x------` and holds a `sealed/` folder at `d---------`, so removing one means making it writable first.
- **Trace shape:** the git marker is in a `user` entry's `tool_result`. `tests/fixtures/eval-trace-no-git.jsonl` is cut from a real kept trace, with its local paths replaced by neutral ones.

**Slices built**
1. **Graders (R1–R3):** `reads-behaviour` is removed. `says-the-behaviour-check` is now an `llm` grader that counts Write, Edit and a shell write the same. `test_no_grader_insists_on_a_tool` failed on exactly those two graders before the change and passes now. The never-graders are unchanged.
2. **Sandbox failures (R8):** a failed run whose trace shows git couldn't start is classed `environment`. It is never rerun and never counted against the skill.
3. **Verdicts and the note line (R5, R7, R10):** each case's verdict comes from its runs. The findings line is written in one place only, in `sdlc.py`, and still matches `CASES_RE` in both scripts. The run summary reads failures from the verdicts, and from `result.json` for runs made before this change.
4. **Traces and workspaces (R9):** every run passes `--keep-temp`. A failed run's trace is copied to `<run>/traces/`, and each workspace is then removed, but only when it passes the guard: an `e-*` folder sitting directly in the system temp dir or `/tmp`. Anything else is listed under `left`, and `--keep` removes nothing. The removal test is marked `portable`.
5. **The rerun (R4, R6):** in a change's scope, a failed case reruns alone (`--case`, no `--tag`), once, under what is left of the $5 cap. If there is no cap left, or the rerun stops at its ceiling, the case counts as failed, marked `not rerun: the cost cap`.
6. **Full history (R18):** the cases report and release's report carry `full_history`. The release skill sets the last full run beside the one before it.
7. **The factory's note (R11, R12):** `factory.py cases` writes run-cases' note when cases fail too, and exits 1. `--skip <why>` writes the skip and runs nothing; it refuses an empty why or cases that already ran.
8. **Landing (R13–R15):** the failed, environment and skipped signals, with each failed case's graders and run folder. The `cases` part now carries `noted`, `failed`, `environment`, `skipped` and `run`. The question gains the clause "its failed or skipped skills' cases accepted as shown". `land` still refuses only cases that haven't run (R14).
9. **The land skill (R16):** it runs each change's cases in Step 1, before its WAIT, then runs `land-check` again so the question shows the results. Neither command has a rule, so the harness asks before each.
10. **Ship's `cases.md` (R17)** and the **docs (R19):** CONTRIBUTING, the *Writes before a WAIT* list in AGENTS.md (now five exceptions) and the factory README.

**Tests:** about 20 new or rewritten tests across `test_evals.py`, `test_land.py`, `test_factory.py` and `test_skills.py`. Each requirement's test is listed in `plan.md`.

**Changes from the plan:** my helper is named `classify_runs()` because `_classify` already existed in `sdlc.py`. The factory got `read_cases_note()`, `_cases_part()`, `_cases_shown()` and `_cases_signals()`. R19 is proved by an acceptance check in `checks.md`, not a suite test. `plan.md` now says all of this.

**`notes.md`:** one open item. 26 old `e-*` workspaces from earlier case runs are still in `/private/tmp`; clearing them is a follow-up, not part of this change.

- DECISION: [default] When the person declines the paid run at landing, the skill runs `--skip "declined at landing"` with its own fixed words, not the person's. Going ahead with that unless told otherwise.
  - OPTION: fixed words in the skill — keeps the rule that a person's words never go on a command line (`test_the_land_skill_passes_a_fixs_id_never_its_words`); the note doesn't say why the person declined
  - OPTION: the person's own words on `--skip` — the note says their reason; a quote or `$(` in it breaks or runs on the command line
  - OPTION: a ticked `(person, skip)` line in `decisions.md`, with `--skip R<n>` — their words without that risk; a new ledger line kind for the ledger reader to handle
  - WHY: R16 says "their reason", but the harness prompt they decline carries no words, and the repo's rule keeps a person's words off command lines
- DECISION: [default] In a full run, a case with 2 environment runs and 1 failed run counts as `passed`. That follows R7's rule literally (it fails on two or more failures that aren't the sandbox's), and the one failure is still shown in its verdict. Going ahead unless told otherwise.
  - OPTION: passed, failure shown — R7 as written; a case can pass with no clean run
  - OPTION: failed when no run counts — never passes on a single failed run; adds a rule R7 doesn't state
  - WHY: R7 names this test case without giving its result, so I applied its rule as written
- DECISION: [default] When several cases fail in one run, each rerun's ceiling is the $5 cap minus everything spent so far, reruns included, not just minus the first run's cost. Going ahead unless told otherwise.
  - OPTION: cap minus all spent — the whole call stays under $5, as the constraints require
  - OPTION: cap minus the first run only — R4's wording; several reruns together could go past $5
  - WHY: the intent's constraint that the rerun stays "under its cap"

## Evidence

$ uv run --group dev pytest -q tests/test_evals.py -k "insists or behaviour_case"   (before the grader edits)
FAILED tests/test_evals.py::test_no_grader_insists_on_a_tool - AssertionError: assert ['ship-behavi...aviour-check'] == []
2 failed, 37 deselected in 0.35s
exit: 1

$ uv run --group dev pytest -q tests/test_evals.py   (new R4–R10, R18 tests, before the code)
12 failed, 39 passed in 11.80s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_factory.py   (new R11–R15 tests, before the code)
7 failed, 422 passed in 58.33s
exit: 1

$ uv run --group dev pytest -q tests/test_evals.py
51 passed in 2.23s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k skip_writes
1 passed, 81 deselected in 0.47s
exit: 0

$ ./check.sh > /tmp/b156/gate.log 2>&1; echo "exit: $?"; grep -E "passed|failed|error" /tmp/b156/gate.log | grep -v "Validation\|plugin directory" | tail -5
exit: 0
All checks passed!
2890 passed, 28 skipped in 183.87s (0:03:03)

$ uv run --group dev pytest -q -n auto -m portable
595 passed, 28 skipped in 66.20s (0:01:06)
exit: 0

$ sh -c "$(awk '/^```sh/{f=1;next}/^```/{f=0}f' .sdlc/work/156-cases-that-tell/checks.md)"; echo "exit: $?"
exit: 0

$ ls /private/tmp | grep -c '^e-'
26
