# land-review

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

Review landing round ${round}: ${what}. Review its whole diff: ${diff}

## rebased

the change was rebased onto ${base}, ${why}

## resolved

its conflicts resolved while landing, in build/land-${round}.md

## clean

with no conflict

## asked

the builder made a fix the person asked for while landing, in build/land-${round}.md. The person asked: ${ask}
