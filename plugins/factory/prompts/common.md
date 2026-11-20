# common

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## head

Change folder: ${rel}. Worktree: ${root}.

## check

A full run of the suite, when you want one, is `uv run --quiet --script ${script} check ${ident}`: it waits for a gate slot.

## land-diff

`git diff ${fork}...HEAD`, from the commit this round rebased the change onto. ${base} may have moved since: a commit on it that isn't in that diff is not the change's, and a move is the script's to catch before the close, never a finding.

## weigh

Weigh each open default in decisions.md, ${ids}, with exactly one line each: `- SETTLED: D<n>: <the reason, naming where the spec, the code or a round answers it>`; `- CONFIRM: D<n>: <what the build assumed, and why the person's yes at the landing is enough>`, which leaves it open for the landing's question to show and the person's yes to confirm; or `- ESCALATED: D<n>: <why only the person can decide>`. A default with no line counts as escalated. The decision may be READY when every open default is SETTLED or CONFIRM and nothing else escalates; it is ESCALATE while any default is escalated. Never settle or confirm a blocking line, or a default about scope, policy, cost, a destructive operation, a secret or a published interface: escalate those.

## weigh-no-confirm

Weigh each open default in decisions.md, ${ids}, with exactly one line each: `- SETTLED: D<n>: <the reason, naming where the spec, the code or a round answers it>`, or `- ESCALATED: D<n>: <why only the person can decide>`. None may be carried to the landing with `- CONFIRM:`, since ${why}. A default with no line counts as escalated, and the decision is ESCALATE while any is. Never settle a blocking line, or a default about scope, policy, cost, a destructive operation, a secret or a published interface.

## weigh-bare

These have no options yet: ${ids}. Under the ESCALATED line of each you escalate, give two to four indented `  - OPTION: <option> — <pros and cons>` lines, the default first, then one `  - WHY: <why the default was chosen>`.
