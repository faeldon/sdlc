# mend

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## evidence

Your reply has no ## Evidence, or a command without its exit: run what your claims rest on again and reply with it.

## verdict

Your reply holds VERDICT: lines that disagree, so the script can't read your verdict. Reply again, the whole reply, with one VERDICT: line as the first line and nothing before it.

## decision

Your reply holds DECISION: lines that disagree, so the script can't read your decision. Reply again, the whole reply, with one DECISION: line as the first line and nothing before it.

## arbitrate

The script couldn't read your answers: ${problems}. Reply again, the whole reply, answering each change exactly once as plain text with no emphasis, `- KEPT: <role>: C<n>: <why>` or `- DROPPED: <role>: C<n>: <the change> — <why>`.
