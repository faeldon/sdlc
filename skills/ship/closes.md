# Ship — the issues it closes

`preflight`'s `branches` names this file when its `closes` part lists issues: the intent's
`closes:` line names some.

## Step 4

**Issues it closes.** For each issue `preflight`'s `closes` part listed, show its number and title, with a line on
whether the diff resolves what it asks, and ask, issue by issue, whether this change resolved it.
Only a confirmed one stays on `closes:`, and `/sdlc:close` closes it when the change lands. One the
human says this change didn't resolve is never closed and never dropped: propose a new seed for it,
an `[idea]` or a `[bug]` as the human decides (a bug with its `Severity:`), with an id from the same
`next-entry` call, its `Issue: #N` line, and a first body line `Split from <NNN-slug>:` saying what
is left. Show the `closes:` line as it becomes.

## Step 6

Then the issues it closes, exactly as approved: take each one this change didn't resolve off the
intent's `closes:` line, and append its seed to the register with its `Issue: #N` line and its
`Split from <NNN-slug>:` line. The seed lands with the change; the `sync` below lets the issue go
from the change's issue, and `/sdlc:close` tells it which seed it stays open as.
