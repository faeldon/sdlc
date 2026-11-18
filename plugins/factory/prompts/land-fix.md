# land-fix

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

The person asked for a fix while landing this change: ${ask} Make it, editing only what the fix needs; run no git command, then report what you changed, ending with ## Evidence.
