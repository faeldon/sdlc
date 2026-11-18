# train-resolve

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

A landing train stacks ${count} changes on ${base} in this order, and stacking ${change} onto the change before it conflicts in: ${files}. Resolve each so every change in the train keeps what it was built to do: read each change's spec and diff with git show (reads only), edit only those files, run no other git command, then report what you kept from each side, ending with ## Evidence.

## change

- ${name}${this}: ${title}. Its spec: `git show ${pre}:${rel}/${spec}`; its diff: `git show ${pre}`.

## this

(this change)
