# resolve

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

The base branch moved under this change, and rebasing onto it conflicts in: ${files}. Resolve each, keeping what both sides meant; edit only those files, run no git command, then report what you kept from each side, ending with ## Evidence.

## gone

The landing deleted ${gone} from ${inbox}, and they stay deleted: don't keep them.
