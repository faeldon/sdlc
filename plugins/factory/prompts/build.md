# build

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## first

Build it: plan.md first (Tier 2), then the code, test first.

## restart

The approver escalated this change after round ${before}, and the person sent it back for another build: read ${rel}/${archive} and build round ${round} to answer it, plan.md first where the approach changes, then the code, test first.

## restart-words

The person adds: ${words}

## upgraded

${decision} is decided in decisions.md: ${answer}. So this change is now Tier 2, upgraded before round ${round}, and ${rel}/spec.md is its approved spec. Rewrite ${rel}/plan.md against it first, keeping what still holds of your plan so far, then build round ${round} to the spec, test first. Every other ticked line in decisions.md is settled: build on it.
