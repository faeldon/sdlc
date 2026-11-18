# Ship — the skills' cases

`preflight`'s `branches` names this file when its `cases` part has a `scope`: in this plugin's own
repo, the diff reaches a skill whose behaviour the suite in `evals/` checks under a model.

## Step 1

**Then the skills' own cases.** Show the cases in `scope` and that the run is paid and capped (at
most $5), and only then run `sdlc.py run-cases <NNN>`, the same way as `accept`: no rule here, so
the person answers the prompt it raises, and never a command line with `eval` in it, which the
harness refuses from a worktree. A case that fails reruns alone, once, inside that run and under
its cap, and fails only when its rerun fails too; a run whose trace shows the sandbox couldn't start
git is `environment`, never rerun or counted against the skill. It prints each case's verdict
(`passed`, `passed on rerun`, `failed`, `environment`) with each run's score, failing graders and
kept trace, the lists `failed`, `environment` and `passed_on_rerun`, and `note`, the line Step 3
writes. A `skipped` run (no `claude`, an unavailable eval, the cost ceiling) never stops ship:
Step 3's note says why. A failed case doesn't stop here either: Step 3 makes it a finding.

## Step 3

**The note says what the skills' cases did too:** run-cases' `note`, copied as `run-cases`
printed it (`Skill evals: ran, <passed> of <cases>`, then the cases that failed, hit the
environment or passed on rerun, and the run), or `Skill evals: skipped, <why>` when Step 1's run
was skipped or the person declined its prompt. Each case in `failed` is an **Important**
`[correctness]` finding, `open`: its `Evidence:` the case, its failing graders and its kept trace's
path, its `Class:` a skill doing what its text forbids. A case in `environment` or `passed on
rerun` is no finding: the note names it. One the person says failed for the model's sake, not the
change's, is answered `wrong` with why, never left out. As with the
fresh review, the question names a skip, and `sdlc.py ship` refuses a scoped diff whose note says
neither.
