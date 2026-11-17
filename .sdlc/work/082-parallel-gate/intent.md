---
id: 082
slug: parallel-gate
tier: 1
impact: none
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
serves: none
---

# 082 — Run the gate's tests in parallel, and let it pass in the main checkout

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The gate, `./check.sh`, takes 4 minutes. `pytest -q --durations=40` on 2026-11-17 ran the suite in
240 s: 1,848 tests one after another on an 18-core machine, none over 7.6 s, the slowest 40 about
60 s together. The time is thousands of `git` and `uv run` process starts, serially. Every change
pays it at least twice (building, then ship), and a factory run pays it on every round's gate
(`factory.py gate` runs the base branch's `check.sh`). The same day,
`uv run --with pytest-xdist pytest -n auto` ran the same suite in 45 s, with the same results, while
another gate ran alongside it.

That timing run also showed the gate is **red in the main checkout**:
`tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden` walks every file under the root
with `rglob` (`scanned()`, `tests/test_nothing_local.py:64-77`), gitignored ones included bar
`SKIP_DIRS` and the change worktrees, so it reads `.sdlc/reports/`, where `run-cases` writes its
results, and finds 72 home-directory paths (`cases-2026-11-13-1/aggregate-result.json` and the
rest). A change's worktree has no `.sdlc/reports/`, which is why every gate run from one passed,
but `./check.sh` from the main checkout, where CONTRIBUTING.md and the release run it, fails on a
folder that never reaches GitHub.

## Outcome

- `./check.sh` runs pytest across the machine's cores (`-n auto`) and takes well under a minute on
  the machine above, measured before and after, the figures in `notes.md`.
- The same suite passes in parallel as serially: no test depends on running alone or in order.
- `./check.sh` passes in the main checkout with `.sdlc/reports/` holding `run-cases` results, and
  `test_nothing_local` still reads every file that could reach GitHub (tracked, or untracked and
  not ignored) and nothing git ignores.
- `pytest-xdist` is in `pyproject.toml`'s `dev` group and `uv.lock`; `./check.sh` passes from a
  fresh worktree.
- CI's jobs (`.github/workflows/check.yml`) still pass; the Windows job's `-m portable` run works
  with or without `-n`.

## Affected

- **Area:** this repo's gate and its tests.
- **Files & components:** `check.sh` (the pytest line), `pyproject.toml` (`dev` group) and
  `uv.lock`, `tests/test_nothing_local.py` (`scanned()`), perhaps `.github/workflows/check.yml`, and
  the command lists in `AGENTS.md` and `docs/CONTRIBUTING.md`.
- **Downstream:** every gate in this repo (`/sdlc:ship`'s Step 1, `factory.py gate` and `gate --land`
  on this repo's changes, the release), CI, and anyone running `./check.sh` from a clone. No host:
  `check.sh` and the `dev` group aren't part of the plugin a host installs.
- **Contracts:** `check.sh`'s fail-fast rule and its "no tests collected is red" line; *Nothing about
  a project or a workspace* (the scan must not narrow to miss a file that ships); *Script
  dependencies* (xdist is a test dependency only, so the PEP 723 block is unchanged);
  `test_the_gate_and_ci_never_run_the_skills_cases`.

## Constraints

- A green gate still means every test ran: no silent drop or skip in parallel, and pytest's exit 5
  stays red.
- The scan keeps reading every file that could be committed, untracked ones too, so a new file is
  checked before its first commit.
- No test made order-dependent or skipped to get there: one that fails only in parallel is fixed,
  not marked serial, unless there is no other way, and then it says why.

## Open questions

- Scan by `git ls-files --cached --others --exclude-standard` (exactly what could reach GitHub), or
  keep `rglob` and add `.sdlc/reports` to what it skips? The first fixes the class, any ignored
  local output; the second is the smaller diff.
- `-n auto` everywhere, or only in `check.sh`, CI left serial? GitHub's runners have 2 to 4 cores,
  and the Windows job is the slow one.
- Does anything in the suite write to a shared place (the main checkout's `.sdlc/reports/`, the git
  common dir's lock, a fixed port) that a parallel run trips on? One clean parallel run is evidence,
  not proof.

## Approach

Add `pytest-xdist` to the `dev` group and lock it; change `check.sh`'s test line to
`pytest -q -n auto`; make `scanned()` in `tests/test_nothing_local.py` list files through git,
tracked plus untracked-not-ignored, filtered by suffix as now. Time `./check.sh` before and after,
from the worktree and the main checkout, and run the parallel suite three times to look for flakes.
Update the gate's command lines in `AGENTS.md` and `docs/CONTRIBUTING.md`.
