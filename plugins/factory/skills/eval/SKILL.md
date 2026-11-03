---
name: eval
description: Replay the factory's reviewers on the diffs that let real bugs through — every escaped bug the register and the Close commits trace to a change — and score which reviewer would have caught each, against the last eval, after one approval of the agent runs it takes. Use when a reviewer's prompt, a model in factory.toml, or the reviewer list changes, to keep the change only if the score holds or rises. Not for reviewing a change (/sdlc-factory:build, /sdlc:ship), not for finding new bugs in old code (/sdlc-factory:review), and never run on its own or on a schedule.
argument-hint: "[--limit N — how many escaped bugs, newest first; 10 by default]"
allowed-tools:
  - Read
  - Write
  - Agent
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py escapes *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py report-dir *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py score *)'
disable-model-invocation: true
---

# Factory eval — would the reviewers have caught the bugs that got through?

Every bug the register traces to a change (`Introduced by:`, and the `Sdlc-Fixes` lines close
writes when a change fixes one) came in through a diff the review passed. This replays the
factory's reviewers on those diffs, as they are configured now, and scores which of them raises a
`CHANGE:` on the bug's paths. Run it before and after changing a reviewer's prompt or model: the
change stays only if the score holds or rises.

**It writes nothing to the repo.** The reviewers read the old diff as text (`git diff`) and the
files as they were (`git show`); nothing is checked out, stashed or committed. Its replies and
scores go under `.sdlc/reports/`, a folder that ignores itself.

## Step 0 — What would run (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py escapes --limit <N>
```

`config` gives the reviewers (`factory.reviewers`) and any model a role is set to
(`factory.models`). `escapes` gives each escaped bug, newest reported first, up to `--limit` (10
unless the argument says otherwise): its id, title, paths, the change that let it in, and the
`base` and `commit` of the diff to replay. `partial` means the change's close recorded no
`Sdlc-Base:`, so only its last commit is replayed. A bug whose `paths` is null will be listed but
scored `unknown`, never `missed`. Say how many were `unattributed` (no `Introduced by:`) or name an
`unknown_change`: neither can be replayed.

**With no escapes, say so and stop:** there is nothing to score.

## Step 1 — Show it

Show the bugs (id, title, change, paths, `partial`), the reviewers with their models, and the
most agent runs: one per reviewer per bug.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Replay <reviewers> on the introducing diffs of these <N> escaped bugs, at most <runs> agent runs, and write the scores under .sdlc/reports/? (yes / change the limit / no)`

**Do nothing more until the person says yes.** A different limit is a new Step 0 and a new
question.

## Step 3 — Run it

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py report-dir --kind eval
```

It prints the run's folder. `Write` Step 0's `escapes` output, exactly as printed, to
`<run>/escapes.json`. Then, for each bug, spawn every reviewer (`sdlc-factory:reviewer-<role>`)
**in one message**, so they run in parallel, each with `Replay: review the change <change>: run
git diff <base> <commit>, and read files at <commit> with git show <commit>:<path>. There is no
change folder or worktree for it; write nothing.`, and its model when `factory.models` sets one.
`Write` each reply, exactly as returned, to `<run>/<bug id>/<role>.md`. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py score <run>
```

## Step 4 — Report and stop

Report each reviewer's score (`caught` of `scored`) beside the last eval's, when there was one,
then each bug with the reviewers that caught it and the `CHANGE:` line that did. A reviewer whose
score fell is the finding: name the prompt or model change since the last eval, if the person
said. Give the report's path (`report` in `score`'s output). Nothing was committed.

## Out of scope

- Editing a reviewer's prompt or `factory.toml`: that is a change, through `/sdlc:intent`.
- Checking out, stashing or committing anything, and writing anywhere but the run's folder.
- Filing or retiring bugs: `/sdlc:bug`.
