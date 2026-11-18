# spec

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## draft

Draft spec.md for this change.

## upgraded

It was upgraded from Tier 1 to Tier 2 before round ${round}, on the person's answer to ${decision} (${question}): ${answer}. The build so far, up to round ${before}, is in the worktree: specify the whole change, what is built included.

## revise

Revise your draft, as the person asks: ${words}

## recheck

Your draft is missing one of these: every <...> prompt replaced, the requirements numbered and each checkable, a Contracts touched line for each invariant the change comes near. Draft it again with all three.
