---
name: review
description: Review code no change touches — the paths the base branch's [review] sensitive lists, else the least recently changed files, or the paths named — with the factory's code and security reviewers, and after one approval of the agent runs it takes, write what they find as proposed [bug] entries in a report under .sdlc/reports/, for /sdlc:bug to file. Use when asked, or on a /schedule routine, to catch old bugs before a change trips on them. Not for reviewing a change (/sdlc-factory:build, /sdlc:ship), not for filing the bugs (/sdlc:bug does, from the report), and never for fixing anything.
argument-hint: "[paths… — what to review; else the sensitive paths, else the least recently changed]"
allowed-tools:
  - Read
  - Write
  - Agent
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py slice *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py report-dir *)'
disable-model-invocation: true
---

# Factory review — old code, looked at before a change trips on it

A change's review reads the change. Code no change has touched in a while, often the code a
mistake costs most in, is read only when a bug is filed against it. This hands a slice of it to the
factory's code and security reviewers as it stands, and turns what they find into proposed bugs.

**It fixes nothing and files nothing.** Its one write is a report under `.sdlc/reports/`, a folder
that ignores itself; the bugs in it reach `.sdlc/work/inbox.md` only through `/sdlc:bug`, which
gives each an id and commits it the way every bug is filed.

## Step 0 — What would be reviewed (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py slice --paths <paths> --limit <N>
```

Leave out `--paths` when the argument names none. `slice` gives `paths`: the ones named; else the
tracked files under the base branch's `[review] sensitive`; else the `--limit` (10 by default)
least recently changed tracked files, with `why`. Any path an open change's worktree touches is in
`left_out`, never reviewed here: that change's own review reads it. **With no paths, say so and
stop.**

## Step 1 — Show it

Show the paths and `why`, what was left out, the reviewers (`code` and `security`, with any model
`factory.models` sets), and the most agent runs: one per reviewer.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Review these <N> paths with <reviewers> as they stand, at most <runs> agent runs, and write the problems found as proposed bugs to .sdlc/reports/? (yes / change the paths / no)`

**Do nothing more until the person says yes.**

## Step 3 — Run it

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py report-dir --kind review
```

Spawn `sdlc-factory:reviewer-code` and `sdlc-factory:reviewer-security` **in one message**, each
with `No change: review the code at <paths> as it stands, not a diff. There is no change folder;
write nothing. Return each problem as - PREEXISTING: path:line: what is wrong.` `Write` each reply,
exactly as returned, to `<run>/<role>.md`.

Then `Write` `<run>/review.md`: `# Review <run>`, the paths and `why`, then one block per distinct
problem the replies raise (two reviewers naming the same line are one), in the shape `/sdlc:bug`
files:

```
## [?] [bug] <what's broken, in a few words>

<What is wrong at that line, and what it breaks; which reviewer raised it.>

Severity: <a word from the process doc's section on bugs, proposed>
Paths: <path>
```

The `?` is for `/sdlc:bug` to give it an id. Propose the severity from the process doc's words
(`docs.process` in `.sdlc/config.toml`, its section on bugs), never one of your own. Leave out a
reply's style nits and what it marks as fine.

## Step 4 — Report and stop

Report how many problems each reviewer raised, the proposed bugs by title and severity, and the
report's path. End with the command that files them, which only the person runs:
`/sdlc:bug <run>/review.md`. Nothing was committed or filed.

**To run it on a schedule,** a `/schedule` routine can invoke `/sdlc-factory:review`: it still
stops at its WAIT, and files nothing on its own.

## Out of scope

- Fixing any problem it finds: that is a change, through `/sdlc:intent`.
- Writing `.sdlc/work/inbox.md` or committing: `/sdlc:bug` files bugs.
- Reviewing a change in progress: its paths are left out here, and its own review reads them.
