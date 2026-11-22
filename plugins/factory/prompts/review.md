# review

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

Review round ${round}.

## upgraded

This change was upgraded from Tier 1 to Tier 2 before this round (${decision}): review it against spec.md.

## reworked

Reworked: ${reworked}. Kept last round: ${kept}. Settled, never raise again: ${settled}.

## raise-again

Raise again, word for word, any change kept last round that the rework didn't make.

## handed

Nits handed to the builder last round: ${handed}; raise again, word for word with its weights, any the rework didn't make.

## earlier

Nits you raised in round ${before}: ${nits}; raise again, word for word with its weights, any that are still true.
