---
id: 149
slug: landing-resolver-agent
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 149 — A landing's conflicts are resolved by an agent of their own, measured apart from the builder · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code (each a fact this spec rests on):

- A factory agent's role is the name of its `runs/<role>.sessions` file, set by `cmd_agent` from
  `TASK_ROLE` through `agent_name()`. `sdlc.py`'s `_agent_sessions()` reads every `*.sessions`
  file under `runs/` and names each session after its file's stem. `metrics.py` writes
  `Sdlc-Role: <role>` from that map. Neither holds a list of factory roles, so a `resolver` role
  needs no change in `scripts/`.
- `train-resolve` is reached only from the train: the land skill's `resolve` step and
  `RUN_STEPS`' `("agent", "{change}", "--task", "train-resolve")`. The other `resolve` task (the
  builder, resumed, on a single change's rebase) is used only by
  `test_a_resolving_landing_records_the_builder_in_the_rebased_commit`. No skill runs it, since
  `land` no longer runs `base`. This change leaves it alone.
- `land-fix` runs the change's own builder, resumed (`RESUMES`). It stays that way.
- Today `resolve --continue` stages only the conflicted files (`_conflicted()`) and the change's
  records (`RESOLVE_RECORDS`, the marker, `build/land-<n>.md`). An edit to any other file is
  left unstaged. `git rebase --continue` may then refuse it, which the script reports as "a second
  conflict", or it may be carried along unseen. Nothing checks for it.

R1. `agent <NNN> --task train-resolve` runs `--agent sdlc-factory:resolver`, never
`sdlc-factory:builder`, in a fresh session (`--session-id`, never `--resume`), and its output's
`role` is `resolver`. Test: `test_a_train_conflict_goes_to_the_resolver_with_every_change` (the
renamed and updated `test_a_train_conflict_goes_to_one_agent_with_every_change` in
`tests/test_train.py`) fails if the argv names the builder or the role isn't `resolver`.

R2. The resolver's session id goes to `runs/resolver.sessions`, and its `runs/costs.jsonl` row has
`role: resolver` and the model it ran on. `runs/builder.sessions` and the builder's cost rows are
unchanged, byte for byte. Test: the same test, with a stand-in `_claude` that returns figures, fails
if `builder.sessions` changes, if any new row says `role: builder`, or if there's no `resolver` row.

R3. `resolve --continue` stages `runs/resolver.sessions` with the resolution (`RESOLVE_RECORDS`
holds it beside `builder.sessions`), so the rebased commit holds the session id and the worktree is
left clean. Test: the R1 test reads `runs/resolver.sessions` from `HEAD` after `--continue`, and
fails if `git status --porcelain` lists it.

R4. `train-resolve` refuses a `--role` that names any role but `resolver`, so the builder can never
be passed in by hand. Test: `test_train_resolve_runs_no_role_but_the_resolver` fails if
`--role builder` starts a session or writes any `.sessions` file.

R5. `plugins/factory/agents/resolver.md` exists. Its `name` is `resolver`, its `model` is
`sonnet`, its description is over 80 characters, and its tools are exactly `Read, Grep, Glob, Edit,
Bash`: no `Write`, no `Agent`. Its body says it never commits, pushes, merges, rebases, stashes or
switches branch, and edits only the files the prompt names. It also says to keep every change's
intent, never re-implement either side, and report what it combined from each side, ending with
`## Evidence`. Test: `test_agents_have_their_tools_and_nothing_more` (with `AGENT_TOOLS` gaining
`resolver`) fails on any other tool set, a missing file, or a body without "never" and "commit".

R6. The resolver runs no `checks.md` section. Its prompt file says so in the words
`NEVER_RUNS_CHECKS["resolver"]` pins, and names `accept` as the one place checks run. Test:
`test_no_agent_but_the_builder_runs_checks` fails without them.

R7. `[models] resolver` sets the resolver's model, read from the base branch like every
`[models]` key. Unset, it runs on `sonnet` at either depth and tier (`FIXED_MODELS["resolver"]`).
`ROLES` holds `resolver`, so `start`'s `models_at` lists it at `light` and `full`, and
`[models] resolver = "…"` raises no "unknown role" warning. Test:
`test_the_resolver_has_a_model_of_its_own` fails if the default isn't `sonnet` at both depths, if
`models_at` lacks it, if `[models] resolver = "opus"` doesn't reach the argv's `--model`, or if
`[models] builder = "haiku"` changes the resolver's model.

R8. `resolve --continue` refuses a resolution that changed any path outside the conflicted files
and the change's own landing records (`RESOLVE_RECORDS`, `build/land-<n>.md`). That covers a
tracked file changed in the worktree and an untracked file that isn't ignored. The refusal names
every such path, stages nothing, writes no `runs/land-resolved` marker, leaves the rebase where it
is (as the conflict-marker refusal does), and records a `stop` with a plain line saying what to undo
and how to continue or eject. Test: `test_a_resolution_outside_its_files_is_refused` fails if a
stand-in resolver that also edits an unnamed tracked file, or creates one untracked, gets through
`--continue`, or if the refusal leaves anything staged.

R9. That check reads both sides from one `git status --porcelain -z` listing. A conflicted path is
an unmerged entry (`DD AU UD UA DU AA UU`). A stray path is any other entry whose worktree column
isn't blank, or `??`. Paths the replayed commit staged cleanly (worktree column blank) are the
commit's own and pass. The landing's records are compared as `as_posix()` paths relative to the
root. Test: in `test_a_resolution_outside_its_files_is_refused`, a clean resolution of a commit
that also changes a second file, which merges without conflict, goes through. The test fails if
that staged file is counted as stray.

R10. A resolution that edits only its conflicted files leaves every other file in the worktree as
the rebase left it. Test: the R1 test hashes a file the change touches but the conflict doesn't name
before and after `train-resolve` and `--continue`, and fails if it differs.

R11. `land-fix` still runs the change's own builder, resumed, and records under `builder`. Test:
the existing `land-fix` tests in `tests/test_land.py` keep asserting `role == "builder"`, and fail
if it moves.

R12. `Sdlc-Role` lines are built from the change's `runs/*.sessions` files as they are now. A
change with a `resolver.sessions` gets an `Sdlc-Role: resolver` line of its own. An old `Close`
commit is never re-read or rewritten. Test: `test_a_resolver_session_is_its_own_role`
(`tests/test_metrics.py`, or wherever `_agent_sessions()` is tested) fails if a session listed in
`resolver.sessions` is named `builder` or left unnamed.

R13. "Only the builder edits" becomes "only the builder and the resolver edit, the resolver only the
files a conflict names" in AGENTS.md (*The factory*), `plugins/factory/README.md` (the agents table
gains a `resolver` row, and the editor line and the landing paragraph change), the land skill's
`resolve` step and `AGENT_TOOLS`' comment. `builder.md` loses its *A conflict, while landing*
section. Test: `./check.sh` (`test_agents_have_their_tools_and_nothing_more`, the skills' rule
tests) and `rg -n "landing agent, the builder|Only the builder edits" plugins AGENTS.md` returning
nothing.

## Design

**The agent.** `plugins/factory/agents/resolver.md` is new and adapts nothing, so it carries no
NOTICE line and stays out of `ADAPTED`. It takes over the merging rules from `builder.md`'s *A
conflict, while landing*:

- read each change's spec and diff with `git show`, a read;
- resolve each named file so every change in the train keeps what it was built to do;
- remove every conflict marker;
- edit nothing else, and run no git command but reads;
- run the repo's tests and gate on the result if it chooses;
- report, per file, what it took from each side and why; how it combined them when both sides
  changed the same code; and anything it couldn't keep. The report ends with `## Evidence`.

It is told it is not building: no new behaviour, no refactor, no fix to anything it notices (that
goes in the report), and no re-implementation of either side. `holds()` already files a reply with
`## Evidence` for any role that isn't a reviewer, the approver, the verifier or the spec-writer, so
the resolver's reply is picked like the builder's.

**`factory.py`, in the tables.**

- `ROLES` gains `"resolver"`.
- `FIXED_MODELS["resolver"] = "sonnet"`.
- `TASK_ROLE["train-resolve"] = "resolver"`.
- `RESOLVE_RECORDS` gains `runs/resolver.sessions` and keeps `builder.sessions` for the other
  `resolve` task.
- `RESUMES` stays as it is: `train-resolve` was never in it, and `cmd_agent` resumes only when
  `role == "builder"`, so the resolver always starts fresh.
- `agent_name("resolver")` is `resolver`, so the run is `--agent sdlc-factory:resolver` and the
  sessions file is `runs/resolver.sessions` with no new code.
- `model_for()` needs no change: `[models]`, then `FIXED_MODELS`.
- `DEFAULTS["models"]` stays `{}`: the default lives in `FIXED_MODELS`, like every other role's.

**`factory.py`, in `cmd_agent`.** Before anything is written, `task == "train-resolve"` with a
`role` other than `resolver` (or `None`) is refused (R4). The words change in a few places, with no
behaviour behind them:

- `_land_task`'s docstring;
- the `RESUMES` comment;
- `cmd_resolve`'s docstring ("left for the builder", "the builder only edits");
- `land-review`'s prompt, which says "its conflicts resolved while landing, in
  `build/land-<n>.md`" in place of "by the builder". The marker is written by both `resolve` tasks,
  and a reviewer needs the resolution, not who wrote it.

**The fence (R8, R9).** `cmd_resolve --continue`, after the conflict-marker check and before the
register is pruned or anything is staged, reads `git status --porcelain -z --untracked-files=all`
once. That is the same call `_dirty()` makes, through a sibling reader that keeps each entry's `XY`
code. The listing is split into unmerged paths (the conflicted files) and changed paths (worktree
column not blank, or `??`). Changed paths that are neither conflicted nor among the landing records
are stray. Stray paths go through `_land_refused()`, with a raw `why`
(`edited outside its conflicted files: <paths>`) and a plain line: undo those edits in the change's
worktree (`git checkout -- <path>`, or delete an untracked file), then
`factory.py resolve <NNN> --continue`, or eject the change from the train. The rebase is left under
way, exactly as the marker refusal leaves it. Under `train --run` a refusal already stops the loop
for the person, so no new stop is needed. The check sits in `--continue`, not in the agent run,
because `--continue` is the one place a resolution is accepted, whoever made it. It covers the
builder's single-change `resolve` and a person's hand resolution too, and both were told "edit only
those files" already.

Why not the tool list alone: `Edit` takes any path in the worktree and `Bash` can write anything,
so no tool permission can confine an agent to a list of files. The prompt asks; the script checks.

**Who reads the new role, unchanged.**

- `run_cost()` splits `by_role`, so the resolver's cost shows on its own.
- `sdlc.py`'s `_agent_sessions()` and `_agent_models()` give `metrics.py` the role and model, so
  the change's `Close` commit gets `Sdlc-Role: resolver … model=sonnet` from code that already
  exists.
- `board.py`'s `step_samples()` times no landing builder rows, and a `resolver` row falls through
  the same way. The landing's `resolve` step is still timed from `land-times.jsonl` (its docstring
  gets one word).

**Edge cases.**

- The resolver leaves conflict markers: refused as now, before the fence.
- It edits a conflicted file and a record file: passes, since records are allowed.
- The register (`.sdlc/work/inbox.md`) is conflicted: it is a conflicted path, so the fence allows
  it, and `drop_entries()` still runs after the fence.
- `.sdlc/last-id` was settled by the script: it is staged, its worktree column is blank, so it
  passes.
- A host's tests leave an untracked, non-ignored file: refused, naming it. Left there, it would have
  made the next `_amend_record()` refuse with "uncommitted outside the change's folder", later and
  with less said.

## Contracts touched

- **"Agents that judge have no Write; only the builder edits (its sub-agents only
  `Agent(Explore, Plan)`)"** (AGENTS.md, *The factory*; `AGENT_TOOLS` in `tests/test_skills.py`).
  **This invariant changes**, as the intent asks: a second agent may edit. The edit is fenced three
  ways. It has no `Write` (no new files) and no `Agent`. Its edits are confined by the script, not
  the prompt (R8). It runs only on `train-resolve`, which only the train starts, after the person's
  yes. AGENTS.md, the factory README and the test's comment say the new rule in the same commit.
  This is a policy edit: the person approves it by approving this spec.
- **"No agent commits"**, and "landing is the one place it commits". The resolver runs no git
  command but reads, and `cmd_resolve --continue` still stages and continues the rebase. The
  supervisor's HEAD check is unchanged.
- **"No agent but the builder runs `checks.md`"** (`test_no_agent_but_the_builder_runs_checks`).
  The resolver has `Bash`, so the test covers it, and its prompt carries the never-run words (R6).
- **`factory.py agent` is the one place the factory runs `claude`.** The resolver runs through it,
  with no other entry point.
- **The metrics trailer format is a contract: extend, never redefine.** `Sdlc-Role` gains a value,
  not a field. History is never re-read: an old `Close` commit's `Sdlc-Role: builder`, its
  resolutions inside, stays as it is (R12). A retro reading across the boundary sees landing work
  inside `builder` before this change and apart from it after. That isn't recounted.
- **A resolved conflict is a signal until every reviewer at the run's depth passes its landing
  round** (`resolution_signals()`, `land_verdict()`). This is unchanged: the marker is still written
  by `--continue`, and `land_verdict` still asks every reviewer when it's present.
- **REVIEW.md: a path compared as text between two sources that write it differently.** The fence
  takes both sides from one `-z` listing and compares records as `as_posix()` (R9). It never matches
  `_conflicted()`'s quoted output against `_dirty()`'s unquoted paths.
- **The scripts run on Windows.** The new reader uses `encoding="utf-8"`, no shell, and POSIX paths,
  like `_dirty()`.
- **Mechanism vs. judgment.** What the resolver may touch is decided by the script (R8), not by
  the agent.

## Alternatives rejected

- **Keep the builder and tag its landing rows** (for example a `task` field on cost rows). This
  separates cost but not the model: `[models] builder` would still pick the resolver's model. And
  `Sdlc-Role` would still mix the two unless metrics learned to split one role by task, which
  redefines the trailer instead of extending it.
- **The change's own builder, resumed, for a train conflict.** A train conflict spans every change
  in it. One change's builder session knows its own change and none of the others. The fresh,
  train-wide session is 147's design and stays.
- **Confine the resolver by tool permissions or the prompt alone.** No tool rule limits `Edit` or
  `Bash` to a list of paths, and the intent's constraint is that this is checked by the script.
- **Check the fence in `cmd_agent` after the session.** That misses a person's or the builder's hand
  resolution, and splits the accepting of a resolution across two commands. `--continue` already is
  the one gate.
- **Move `land-fix` to the resolver.** A fix the person asked for changes the work, not a merge.
  It belongs to the change's builder, whose context it resumes.
- **Move the single-change `resolve` task to the resolver too.** No skill reaches it. Moving it
  would widen this change for no measured run. It is left for whoever retires or revives it.
- **Give the resolver `Write`.** Resolving a conflict never needs a new file, and a missing `Write`
  keeps an untracked file from appearing through the agent's own tools. The fence catches one made
  through `Bash`.

## Verification

```sh
uv run --group dev pytest -q tests/test_train.py -k "resolver or conflict"
uv run --group dev pytest -q tests/test_skills.py -k "agents_have_their_tools or runs_checks"
uv run --group dev pytest -q tests/test_factory.py -k "model"
uv run --group dev pytest -q tests/test_metrics.py -k resolver
uv run --group dev pytest -q tests/test_land.py -k "land_fix or resolving"
./check.sh
rg -n "landing agent, the builder|Only the builder edits" plugins AGENTS.md
```

Healthy:

- each `pytest` line ends `passed` with no failures, the R1–R12 tests among them;
- `./check.sh` is green: ruff check, ruff format check, the full suite, and
  `claude plugin validate --strict`;
- the `rg` prints nothing.

By hand, once, after landing: a train with a stacking conflict shows
`"role": "resolver", "model": "sonnet"` in `agent --task train-resolve`'s output, a
`runs/resolver.sessions` in the change's commit, and `Sdlc-Role: resolver` on its `Close` commit.

**Boundaries.**

- Always: the resolver runs only on `train-resolve`, fresh. Its edits are accepted only by
  `--continue`'s fence. Every reviewer at the run's depth still reads a resolution.
- Ask first: changing the resolver's default model, or moving `land-fix` or the single-change
  `resolve` task to it.
- Never: the resolver commits, pushes, merges, rebases, writes a new file or starts a sub-agent.
  History is never recounted, and no `Sdlc-*` field is redefined.

