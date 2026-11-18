---
id: 156
slug: cases-that-tell
tier: 2
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O3]
---

# 156 — The skills' cases tell what a skill did, and stop a landing only when you say so

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The skills' cases (`evals/`, run through `claude plugin eval`) cost more than they tell. Landing 150
on 2026-11-18 spent $8.27 over six runs on a change whose only skill edit was one word in
`skills/ship/behaviour.md`, and blocked the 150+151 train, because, from the kept traces:

1. Git fails in the eval's macOS sandbox whenever xcrun's cache is stale (`xcrun_db … Operation not
   permitted`), so `sdlc.py` misreads the repo (`preflight` said "not a Tier 2 change", no
   `branches`) and a case fails for reasons unrelated to the skill. Neither a shim on
   `$HOME/.zshenv`'s PATH nor a workspace `.claude/settings.json` `env` reached the agent's shell.
2. 60 of 71 graders check which tool was called: `reads-behaviour` failed when ship read
   `behaviour.md` with `cat` instead of Read, though it then ran the behaviour check correctly.
3. One run per case can't tell a regression from a bad roll (0.8, 0.9, 1.0, 0.9 on the same code).
4. A rerun repeats every case in scope, and traces are deleted unless `--keep`, so the first
   failure is never diagnosable.
5. A factory landing blocks a change's commit on a failed case, while `/sdlc:ship` lets the person
   answer it `wrong`.

## Outcome

- Graders check outcomes, not tool choice: the WAIT question asked word for word, `findings.md`'s
  lines, nothing committed, pushed or written before the yes. A grader that names a tool also
  accepts the equivalent read or write by another (a Bash `cat` of a pass file reads it); a test
  reads every grader and fails on one that would refuse an equivalent tool.
- A failed case doesn't stop a factory landing by itself: it is a signal in the landing question,
  with its case, failing graders and trace's folder, which the person's yes accepts, as ship's
  `wrong` answer does. `land` refuses a change whose cases didn't run, not one whose cases ran and
  failed.
- A failed case reruns alone, once, automatically, under the run's cap; a case fails only when it
  fails twice, and a failing run's trace is kept without `--keep`.
- A run whose trace shows git couldn't start (`xcode-select: Failed to locate 'git'`, exit 72) is
  classed environment, reported as such and never counted against the skill; the sandbox issue is
  reported upstream.
- Scope can skip cases when the person says so in the landing or ship question, for an edit that
  changes a skill's wording only; the question names what is skipped.
- The full suite (3 runs per case) runs at `/sdlc:release` as the measure of the skills, its scores
  kept over time; per-landing runs are a smoke test.
- **Moves O3:** a landing stops for a skill that truly broke, not for a sandbox or a model's habit.

## Affected

`evals/*/graders/`, `scripts/sdlc.py` (`run-cases`, `cases_argv()`, `CASE_CAP`, `_cases_report()`,
release), `plugins/factory/scripts/factory.py` (`cases`, `land`'s refusal, `land-check`'s signals),
`skills/ship/cases.md`, `plugins/factory/skills/land/SKILL.md`, `skills/release/SKILL.md`,
`docs/CONTRIBUTING.md` (*The skills' cases*) and `tests/test_evals.py`. Only this plugin's own repo:
hosts have no cases. It lands before 153, which moves the landing code.

## Constraints

- Every case run stays a paid call behind the person's prompt: never in `ALLOW_RULES`, a skill's
  `allowed-tools`, `check.sh` or CI; the automatic rerun is inside the approved run, under its cap.
- A case's result is never hidden: accepting a failure is the person's yes, shown in the question.
- Grader files keep `claude plugin eval`'s format; `tests/test_evals.py` still builds every fixture.

## Open questions

- ~~Does the two-failure rule hold for every case, or only for one whose failure isn't an outcome
  grader (the question, a commit)?~~ Resolved: every case (spec R5).
- ~~Is "wording only" judged by the script (a diff that changes only prose in a pass file), or simply
  the person's word in the question?~~ Resolved: the person's word, recorded by `--skip <why>` (spec
  R12, R16).
- ~~Does `/sdlc:release` run the full suite every time, or only when skills changed since the last
  release?~~ Resolved: unchanged, offered every time and run only on a yes (spec R18).
