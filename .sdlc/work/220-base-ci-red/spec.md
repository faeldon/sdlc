---
id: 220
slug: base-ci-red
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 220 — A red CI on the base branch shows where the person looks · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: none

Assumptions, each checked in the code:
- "The base branch's tip" means the commit CI ran on. That is the remote-tracking ref `refs/remotes/<release.remote>/<git.base>`, read locally, as `_unpushed()` does. Local commits that haven't been pushed never ran CI.
- Core reaches GitHub only through the tracker (`tracker()`, CONTRIBUTING.md *Writing a tracker*). `unavailable()` already tells, without the network, whether `gh` and a GitHub remote are there.
- `status` adds its own entries under Problems in `cli_status()`, not in `analyze()`, as it does for `git.base`. So `vet --strict` never sees them.
- The factory reads ship's `preflight` JSON (`_preflight()` in `landing.py`) and never imports `sdlc.py`. A new preflight part therefore reaches `land_signals()` with no copied code.

Requirements:

1. **R1. The tracker reads CI.** A tracker may have an optional method `ci(branch, sha, timeout)`. It returns `{"state", "runs", "why"}`:
   - `state` is one of `red`, `green`, `pending` or `unknown`.
   - `runs` lists each workflow run on `sha` as `{name, status, conclusion, url}`.
   - The GitHub tracker makes one call: `gh run list --commit <sha> --branch <branch> --json databaseId,workflowName,status,conclusion,url,headSha --limit 50`, under `timeout`, keeping only runs whose `headSha` is `sha`.
   - `red`: some completed run concluded `failure`, `timed_out` or `startup_failure`. `startup_failure` covers a workflow that fails to run.
   - `pending`: no run is red and some run isn't completed.
   - `green`: every run completed and none is red.
   - `unknown`: no runs, a non-zero exit, a timeout, or JSON that won't parse. `unknown` always has a `why`.
   - `tests/test_base_ci.py::test_github_ci_reads_each_state` drives the `gh` fake in `tests/conftest.py` through each state. It fails if a cancelled run, an empty list or a failed `gh` reads as `red`.
2. **R2. A missing source is unknown, and nothing is called.** `base_ci(home, cfg, max_age)` in `sdlc.py` returns `unknown`, with its reason, and calls nothing in these cases:
   - no `git.base`;
   - no tracking ref;
   - `archive.target = "none"`;
   - a tracker without `ci`;
   - a tracker whose `unavailable()` gives a reason.

   `test_base_ci_never_calls_the_tracker_without_a_source` fails if the `gh` fake records a call in any of these cases.
3. **R3. One cache, keyed by commit.** Every reading `base_ci()` gets from the tracker is written to `sdlc-ci.json` in the git common dir (`CI_CACHE`, found through `_ledger_dir()`, like `UPDATE_CACHE`). It holds `branch`, `sha`, `checked` and the reading. It is written to a temp file and `os.replace`d, with `newline="\n"`. Nothing is written outside a repo.
   - A cached reading is reused only while its `branch` and `sha` match the tip now and it is younger than `max_age`. A cache that is older, from another commit, dated in the future, or won't read is read again from the tracker.
   - `test_base_ci_reuses_the_cache_for_the_same_tip` fails if a second call inside `max_age` reaches `gh`, or if a moved tip doesn't.
4. **R4. Status names a red base under Problems.** When `base_ci()` reads `red`, `status` adds one entry under Problems:
   `<remote>/<base>: CI is red at <short sha> (<failed workflow names>): <first failed run's url>`
   - For `green`, `pending` or `unknown` it adds nothing.
   - The entry is added in `cli_status()`, never in `analyze()`. So `vet --strict` and `status`'s exit code are unchanged.
   - Tests: `test_status_names_a_red_base`, `test_status_is_silent_on_green_pending_and_unknown`, and `test_vet_strict_never_sees_ci`.
5. **R5. Status stays fast.** `status` calls `base_ci()` with `max_age = CI_EVERY` (600 s), and the tracker's call gets `CI_TIMEOUT` (10 s). So a tip makes at most one network call every ten minutes, and a call that hangs costs at most ten seconds. `test_status_with_a_fresh_cache_calls_nothing` fails if `gh` is run while a matching cache is younger than `CI_EVERY`.
6. **R6. A broken tracker is unknown, never a crash.** An exception raised by the tracker's `ci()` is caught in `base_ci()` and read as `unknown` with its type and message. Nothing is cached for it. `test_a_raising_tracker_reads_as_unknown` fails on a traceback in `status`.
7. **R7. Preflight carries it.** `preflight` gains a `ci` part, `base_ci()` with `max_age = CI_FRESH` (60 s), so all of a landing's preflights share one call: `{"state", "branch", "sha", "runs", "failed", "url", "why"}`. A red part never adds to `problems` and never changes preflight's exit code. `tests/test_preflight.py::test_preflight_reports_ci_and_never_refuses_on_it` checks both.
8. **R8. Ship's question says it.** `preflight --question` reads `base_ci()` itself, with `CI_FRESH`, so the skill can't leave it out. When it reads `red`, a question that commits gains the clause `on a base whose CI is red at <short sha> (<url>)`. It has no clause otherwise. `test_ship_question_names_a_red_base` fails when the clause is missing on red, or present on any other state.
9. **R9. The factory's landing makes it a signal.** `land_signals()` adds `CI on <branch> is red at <short sha>: <url>` when `pre["ci"]["state"] == "red"`. So `land-check`'s `clear` turns false, and the WAIT no longer approves itself. A missing or non-red `ci` part adds nothing.
   - `tests/test_land.py::test_a_red_base_is_a_signal` fails if a red batch is `clear`.
   - `test_an_unknown_base_is_no_signal` fails if `unknown` is a signal.
10. **R10. The docs say it.**
    - CONTRIBUTING.md *Writing a tracker* lists `ci()` as optional, with its states and that it reads the network.
    - REFERENCE.md *Trackers* says what `status`, ship and the landing show, and that no tracker or no CI means nothing new.
    - AGENTS.md's *Updates* paragraph, which calls the update cache "the one write made with no WAIT", names the CI cache too (see Contracts).
    - Review greps the docs for `UPDATE_CACHE` and "one write" (REVIEW.md, *A doc's claim the change made false*).
11. **R11. It runs on Windows.**
    - Every new `subprocess.run` names `encoding="utf-8"` and never uses `shell=True`.
    - The cache is written with `newline="\n"`.
    - The state classifier is a pure function. Its test is marked `portable`.
    - `tests/test_windows.py` passes unchanged.

## Design

**The tracker (`scripts/trackers/github.py`).**
- `Tracker.ci(branch, sha, timeout)` runs `gh run list` as R1 says, through a variant of `_gh` that passes `timeout` and catches `subprocess.TimeoutExpired` and `OSError` as `unknown`.
- Classifying a run list is a module-level pure function, `ci_state(runs)`, so it can be tested on every platform.
- The tracker reads only what it is given (`branch`, `sha`) and never reads `.sdlc/`.

**Core (`scripts/sdlc.py`, beside the update section).** New constants:
- `CI_CACHE = "sdlc-ci.json"`
- `CI_EVERY = 600`
- `CI_FRESH = 60`
- `CI_TIMEOUT = 10`

`base_ci(home, cfg, max_age) -> dict` works in this order:
1. Resolve `trunk = cfg["git"]["base"]`, `remote = cfg["release"]["remote"]`, and `sha = rev-parse refs/remotes/<remote>/<trunk>`, all local.
2. Return `unknown` (R2) if any of these is missing.
3. Read the cache, reusing it under R3's rule.
4. Otherwise take `tracker(home, cfg)` and check `unavailable()` and `getattr(t, "ci", None)`. Call it inside `try`, with `CI_TIMEOUT`, write the cache, and return `{state, branch, sha, runs, failed, url, why}`. `failed` holds the red runs' names, and `url` is the first red run's.

`ci_problem(reading) -> dict | None` turns a red reading into status's Problems entry. One function words both status's line and ship's clause from the same reading, so the two never drift apart.

**Where it's read:**
- `cli_status()`: `ci_problem(base_ci(home, cfg, CI_EVERY))`, appended to `a["problems"]` beside the `git.base` entry.
- `cmd_preflight()`: `parts["ci"] = base_ci(home, cfg, CI_FRESH)`. It isn't in the loop that collects problems, and isn't a `SHIP_BRANCHES` entry, since ship needs no side file for one clause.
- `cmd_ship_question()` passes `ci=base_ci(...)` into `ship_question()`, which takes a new keyword `ci: dict | None = None` and appends the clause after the sensitive-path one.
- `landing.py`'s `land_signals()` reads `pre.get("ci")`. Each change's preflight in a batch gets the same cached reading, so a red base is a signal on every change in the batch, which is what `clear` reads.

**Edge cases.**
- A tip that was just pushed is `pending`, and nothing is said until CI finishes.
- A red tip followed by a push moves the sha. The old reading no longer applies, and the next read is of the new tip.
- A repo with local commits not yet pushed is read at its tracking ref. That is the commit CI saw, and `status`'s *Unpushed* line already covers the rest.
- A host on any tracker other than GitHub, or on none, sees nothing new.

## Contracts touched

- **Core never calls `gh`.** Every `gh` call is in `trackers/github.py`. Core only calls `ci()` through `tracker()`, so the design stays inside the rule.
- **A tracker never reads `.sdlc/`.** `ci()` takes a branch and a sha and reads nothing else.
- **"That cache is the one write made with no WAIT outside the six above" (AGENTS.md, *Updates*).** ⚠ **This design changes it.** `sdlc-ci.json` is a second cache of the same kind: state in the git common dir, never in a tree, dirtying no checkout and deciding nothing. It is written by `status` and `preflight`, both in `READ_ONLY`, whose comment says "Nothing that writes is here", and `preflight`'s docstring says "Writes nothing". The edit:
  - AGENTS.md names both caches;
  - `READ_ONLY`'s comment allows a state cache in the git common dir;
  - `cmd_preflight()`'s docstring says it writes only that cache.

  This is a policy edit for you to approve, not a side effect. The alternative that keeps the rule is below, as open question 1.
- **`status` is read-only and must stay fast.** It still writes no artifact, and its one possible network call is bounded by R5.
- **A nudge in `status` is never a problem: `vet --strict` refuses.** The intent asks for *Problems*, so the entry goes there, but only in `cli_status()`, like `git.base`. `vet` is unchanged (R4).
- **`land.auto`'s rule: any signal is the person's.** A red base becomes one more signal in `land_signals()`. The rule itself is unchanged.
- **Ship reads a change through one `preflight` call, and asks the question `preflight --question` words.** Both are kept: the new fact is a new part of `cmd_preflight()` and a clause in `ship_question()`.
- **The scripts run on Windows.** Handled by R11.
- **Nothing public names the agent.** No text this change writes reaches GitHub.

## Alternatives rejected

- **Core calling `gh run list` directly.** This breaks "core never calls `gh`", and a host on another tracker would get a GitHub call.
- **A network call on every `status`.** The intent's Constraints rule it out, and a slow `gh` would slow every status.
- **Refreshing only in the SessionStart hook (`update --hook`).** The hook's contract is "one line or nothing", about updates and setup. CI changes far faster than once a session, so status would show a reading hours old. That staleness is the gap this change closes.
- **A reading only at the landing, with no cache.** This keeps the "one write" rule, but `status` would then have nothing to show, which fails the first Outcome.
- **Treating `cancelled`, `action_required` or `neutral` as red.** A person cancels runs on purpose, and a run awaiting approval hasn't failed. The intent says "A CI the tracker can't read is unknown, never red": only a clear failure is red.
- **Reading the newest completed run on the branch instead of the tip's.** A green fix that is still running would be hidden behind the red it fixes. The intent says the tip.
- **A batch-level `ci` field in `land-check` beside `signals`.** `clear` is computed from signals alone, so a separate field would need its own rule for auto-approval. A signal per change uses the rule that already exists.

## Verification

```bash
uv run --group dev pytest -q tests/test_base_ci.py tests/test_preflight.py tests/test_land.py -n auto
uv run --group dev pytest -q -m portable          # the classifier's test runs here too
./check.sh                                        # ruff, format, the full suite, plugin validate
```

Healthy output: every test passes, and `./check.sh` ends green with `claude plugin validate --strict` passing. To check by hand on this repo, with `gh` signed in:
- `uv run --quiet --script scripts/sdlc.py status` prints `Problems: none ✅` while CI on `origin/main`'s tip is green or pending.
- `preflight 220 | jq .ci` prints `"state": "green"` (or `pending`) with the tip's sha.
- `.git/sdlc-ci.json` exists, and `git status` in every checkout is clean.

